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
parser.add_argument("-a", "--Archived", help="Include archived movies", action="store_true")
parser.add_argument("-l", "--Loaded", help="Include loaded movies", action="store_true")
genre_dict = {}
country_dict = {}

#######################
apply_changes = True
only_streaming = False
only_pending = False
skip_archived = True
skip_loaded = True


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
    db_filter = build_notion_db_filter()

    while has_more:
        params = {"database_id": DATABASE_ID}
        params['filter'] = db_filter

        if next_cursor is not None:
            params["start_cursor"] = next_cursor

        db_data = notion.databases.query(**params)

        has_more = db_data['has_more']
        next_cursor = db_data['next_cursor']

        db_rows.extend(db_data['results'])

    return db_rows


def build_notion_db_filter():
    filters = []
    if only_pending:
        pending_filter = {
            "property": STATUS_PROPERTY,
            "status": {
                "equals": UNWATCHED
            }
        }
        filters.append(pending_filter)
    else:
        if skip_loaded:
            loaded_filter = {
                "property": LOADED_PROPERTY,
                "checkbox": {"equals": False}
            }
            filters.append(loaded_filter)
    if skip_archived:
        archived_filter = {
            "property": ARCHIVED_PROPERTY,
            "checkbox": {"equals": False}
        }
        filters.append(archived_filter)
        print ("Filter: Only unarchived movies")

    if filters:
        if len(filters) == 1: return filters[0]
        else: return {"and": filters}
    return


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

    if tmdb_id or imdb_id:
        details = retrieve_tmdb_movie_from_id(tmdb_id or imdb_id)
    else:
        details = retrieve_tmdb_movie_from_title(title)

    if not details:
        print("    (!) Not found. Try changing the name or manually entering the IMDB/TMDB ids")
    else:
        imdbid = details["imdb_id"]
        tmdbid = details["id"]
        print(f"    > imdb: '{imdbid}' -- tmdb: '{tmdbid}'")

    return details


def process_movie(db_data, index, database_size):
    title = get_movie_title(db_data).strip()
    details = {}

    print(f"({index}/{database_size}) {title}")
    if not only_streaming:
        details = retrieve_movie_details(db_data, title, index, database_size)
        if details:
            updateUtils.update_movie(notion, db_data, details, title, genre_dict, country_dict, apply_changes)

    updateStreamingServices.update_streaming_services(notion, db_data, details, title, apply_changes)
    print()


def update_notion_films():
    global genre_dict, country_dict
    print("=====================================")
    print("===  Pablo's Notion Film Updater  ===")
    print("=====================================")
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
    global apply_changes, only_streaming, only_pending, skip_archived, skip_loaded
    # Priority: Pending > Full > Loaded
    args = parser.parse_args()
    if args.Test:
        apply_changes = False
        print("(*)  Test run:  Changes will not be applied")
    if args.Streaming:
        only_streaming = True
        print("(*) Streaming:  Only streaming services will be updated")
    if args.Pending:
        only_pending = True
        skip_loaded = False
        print("(*)   Pending:  Process all unwatched movies")
    if args.Archived and not args.Full:
        skip_archived = False
        print("(*)  Archived:  Archived movies will be included")
    if args.Full:
        skip_archived = False
        skip_loaded = False
        print("(*)  Full run:  Full database will be processed")
    else:
        if args.Loaded:
            skip_loaded = False
            print("(*)    Loaded:  Loaded movies will be included")
    if skip_loaded and skip_archived and not only_pending:
            print("(*)   Default:  Only 'not loaded' and 'not archived' movies'")
    print()


if __name__ == '__main__':
    apply_changes = True

    update_notion_films()
