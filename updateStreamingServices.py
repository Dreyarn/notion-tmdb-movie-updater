import json

from simplejustwatchapi.justwatch import search

from constants import *


def update_streaming_services(notion, movie_db_data, title, apply_changes):
    streaming_offers_data = get_streaming_services_data(title)

    if apply_changes:
        notion.pages.update(
            movie_db_data['id'],
            properties={
                AVAILABILITY_PROPERTY: {"multi_select": streaming_offers_data},
            }
        )

def get_streaming_services_data(title):
    streaming_services_data = load_streaming_services_dict()
    jw_results = search(title, JW_COUNTRY, JW_LANGUAGE, 1, True)
    if not jw_results:
        return

    streaming_offers = parse_streaming_offers(jw_results, streaming_services_data)

    streaming_offers_data = [{'name': s} for s in streaming_offers]
    print(f"    > Available on: {', '.join(streaming_offers)}")


def parse_streaming_offers(jw_results, streaming_services_dict):
    offers = jw_results[0].offers
    streaming_offers = [offer.package.name for offer in offers if offer.monetization_type == 'FLATRATE']

    if [offer.monetization_type for offer in offers if offer.monetization_type == 'CINEMA']:
       streaming_offers.append("Cinema")

    if streaming_offers:
        streaming_offers = [streaming_services_dict.get(s) for s in streaming_offers if streaming_services_dict.get(s)]

    if not streaming_offers:
        streaming_offers = ['🏴‍☠️']

    return streaming_offers


def load_streaming_services_dict():
    with open("streamingServices.txt", encoding='UTF-8') as f:
        streaming_services_data = f.read()

    return json.loads(streaming_services_data)
