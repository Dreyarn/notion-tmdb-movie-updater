from constants import *
from simplejustwatchapi.justwatch import search

def update_streaming_services(notion, movie_db_data, movie_details, title, apply_changes):
    if movie_details:
        title = movie_details['title']
    jw_results = search(title, JW_COUNTRY, JW_LANGUAGE, 1, True)
    if not jw_results:
        return

    offers = jw_results[0].offers
    streaming_offers = [offer.package.name for offer in offers if offer.monetization_type == 'FLATRATE']

    if apply_changes:
        notion.pages.update(
            movie_db_data['id'],
            properties={
                AVAILABILITY_PROPERTY: {"multi_select": streaming_offers},
            }
        )