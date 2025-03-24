import argparse
import json
import re

from notion_client import Client
from tmdbv3api import Movie
from tmdbv3api import TMDb
from tmdbv3api import Search

import updateStreamingServices
import updateUtils
from constants import *

notion_api_url = 'https://api.notion.com/v1/'

notion = Client(auth=NOTION_SECRET)
tmdb = TMDb()
tmdb.api_key = TMDB_ACCESS_KEY
parser = argparse.ArgumentParser()
parser.add_argument("-t", "--Test", help="Test run", action="store_true")
parser.add_argument("-f", "--Full", help="Full database", action="store_true")
parser.add_argument("-s", "--Streaming", help="Update only streaming services", action="store_true")
parser.add_argument("-p", "--Pending", help="Update only movies pending viewing", action="store_true")
genre_dict = {}
country_dict = {}

#######################
apply_changes = True
filter_loaded = True
only_streaming = False
only_pending = False


#######################


def load_genre_dict():
    with open("genres.txt", encoding='UTF-8') as f:
        genre_data = f.read()

    return json.loads(genre_data)


def load_country_dict():
    with open("countries.txt", encoding='UTF-8') as f:
        country_data = f.read()

    return json.loads(country_data)


def get_database():
    has_more = True
    db_rows = []
    next_cursor = None

    while has_more:
        params = {"database_id": DATABASE_ID}

        if only_pending:
            params["filter"] = {
                "property": STATUS_PROPERTY,
                "status": {
                    "equals": UNWATCHED
                }
            }
        else:
            if filter_loaded:
                params["filter"] = {
                    "property": LOADED_PROPERTY,
                    "checkbox": {"equals": False}
                }

        if next_cursor is not None:
            params["start_cursor"] = next_cursor

        db_data = notion.databases.query(**params)

        has_more = db_data['has_more']
        next_cursor = db_data['next_cursor']

        db_rows.extend(db_data['results'])

    return db_rows


def retrieve_tmdb_movie_from_title(title):
    m = Movie()
    result = m.search(title)
    details = {}
    if result:
        details = m.details(result[0]['id'])

    return details


def retrieve_tmdb_movie_from_id(movie_id):
    m = Movie()
    result = m.details(movie_id)
    details = {}
    if result:
        details = result

    return details


def get_movie_title(db_data):
    movie_title = ''
    movie_title_field = db_data['properties'][TITLE_PROPERTY]['title']
    if movie_title_field:
        movie_title = movie_title_field[0]['plain_text']
    return movie_title


def parse_imdb_id(db_data):
    imdb_url = db_data['properties'][IMDB_LINK_PROPERTY]['url']
    return re.sub('/(.*)', '', re.sub('(.*)title/', '', imdb_url)) if imdb_url else None


def parse_tmdb_id(db_data):
    tmdb_url = db_data['properties'][TMDB_LINK_PROPERTY]['url']
    return re.sub('-(.*)', '', re.sub('(.*)movie/', '', tmdb_url)) if tmdb_url else None


def retrieve_movie_details(db_data, title, index, database_size):
    imdb_id = parse_imdb_id(db_data)
    tmdb_id = parse_tmdb_id(db_data)

    print(f"    > imdb: '{imdb_id}', tmdb: '{tmdb_id}'")

    if tmdb_id or imdb_id:
        details = retrieve_tmdb_movie_from_id(tmdb_id or imdb_id)
    else:
        details = retrieve_tmdb_movie_from_title(title)
    if not details:
        print("    (!) Not found. Try changing the name or manually entering the IMDB/TMDB ids")
    return details


def process_movie(db_data, index, database_size):
    title = get_movie_title(db_data)
    details = {}

    print(f"[{index}/{database_size}] Processing '{title}'...")
    if not only_streaming:
        details = retrieve_movie_details(db_data, title, index, database_size)
        if details:
            updateUtils.update_movie(notion, db_data, details, title, genre_dict, country_dict, apply_changes)

    updateStreamingServices.update_streaming_services(notion, db_data, details, title, apply_changes)
    print()


def update_notion_films():
    global genre_dict, country_dict
    apply_arguments()

    database = get_database()
    genre_dict = load_genre_dict()
    country_dict = load_country_dict()
    database_size = len(database)
    i = 1;
    for movie_db_data in database:
        process_movie(movie_db_data, i, database_size)
        i += 1
    if apply_changes:
        print(f"=== {database_size} database rows processed and updated ===")
    else:
        print(f"========= {database_size} database rows processed =========")


def apply_arguments():
    global apply_changes, filter_loaded, only_streaming, only_pending
    args = parser.parse_args()
    if args.Test:
        apply_changes = False
        print("==== Test run: changes will not be applied =====")
    else:
        print("===== Normal run: changes will be applied ======")
    if args.Full:
        filter_loaded = False
        print("==== Full run: full database will be parsed ====")
    if args.Streaming:
        only_streaming = True
        print("==== Only streaming services will be updated ===")
    if args.Pending:
        only_pending = True
        print("===== Pending only: only unwatched movies ======")
    else:
        print("==== Partial run: only 'not loaded' entries ====")
    print()


if __name__ == '__main__':
    filter_loaded = True
    apply_changes = True

    update_notion_films()
