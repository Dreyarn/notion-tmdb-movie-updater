from constants import *

import updateStreamingServices

poster_base_url = 'https://image.tmdb.org/t/p/w600_and_h900_bestv2/%s'
imdb_base_url = 'https://www.imdb.com/title/%s'
tmdb_base_url = 'https://www.themoviedb.org/movie/%s'
ignored_genres = ['Family']


def update_movie(notion, movie_db_data, movie_details, current_title, genre_dict, country_dict, streaming_dict, apply_changes):
    original_title = get_original_title(movie_details)
    overview, translated_title = load_spanish_data(movie_details, original_title)
    new_title = current_title or translated_title or original_title
    # If title in Spanish already contains the original title, do not fill the original title
    if original_title in new_title:
        original_title = ''

    directors = get_directors(movie_details)
    translated_genres = get_genres(movie_details, genre_dict)
    translated_countries = get_countries(movie_details, country_dict)
    runtime = get_runtime_hhmm(movie_details)
    release_date, year = get_release_date(movie_details)
    poster_url = get_poster_url(movie_details)
    imdb_url = get_imdb_url(movie_details)
    tmdb_url = get_tmdb_url(movie_details)

    print_log(directors, new_title, original_title, runtime, translated_countries, translated_genres, year)

    streaming_services = updateStreamingServices.get_streaming_services_data(new_title, streaming_dict)

    if apply_changes:
        notion.pages.update(
            movie_db_data['id'],
            icon={"external": {"url": poster_url}},
            cover={"external": {"url": poster_url}},
            properties={
                TITLE_PROPERTY: {"title": build_rich_text_data(new_title)},
                ORIGINAL_TITLE_PROPERTY: {"rich_text": build_rich_text_data(original_title)},
                RUNTIME_PROPERTY: {"rich_text": build_rich_text_data(runtime)},
                DIRECTOR_PROPERTY: {"rich_text": build_rich_text_data(', '.join(directors))},
                YEAR_PROPERTY: {"number": year},
                OVERVIEW_PROPERTY: {"rich_text": build_rich_text_data(overview)},
                RELEASE_DATE_PROPERTY: {"date": {"start": release_date}},
                IMDB_LINK_PROPERTY: {"url": imdb_url},
                TMDB_LINK_PROPERTY: {"url": tmdb_url},
                LOADED_PROPERTY: {"checkbox": True},
                GENRES_PROPERTY: {"multi_select": translated_genres},
                COUNTRIES_PROPERTY: {"multi_select": translated_countries},
                AVAILABILITY_PROPERTY: streaming_services and {"multi_select": streaming_services}
            }
        )


def build_rich_text_data(text):
    return [{"type": "text", "text": {"content": text}}]


def print_log(directors, new_title, original_title, runtime, translated_countries, translated_genres, year):
    if original_title:
        print(f"    > ({original_title})")
    print(f"    > {year}")
    print(f"    > {', '.join(directors)}")
    print(f"    > {runtime}")
    print(f"    > {', '.join([g['name'] for g in translated_genres])}")
    print(f"    > {', '.join([c['name'] for c in translated_countries])}")


def get_tmdb_url(movie_details):
    tmdb_id = movie_details["id"]
    tmdb_url = tmdb_base_url.replace('%s', str(tmdb_id))
    return tmdb_url


def get_imdb_url(movie_details):
    imdb_id = movie_details["imdb_id"]
    imdb_url = imdb_base_url.replace('%s', str(imdb_id))
    return imdb_url


def get_poster_url(movie_details):
    poster_path = movie_details["poster_path"]
    poster_url = poster_base_url.replace('%s', poster_path)
    return poster_url


def get_release_date(movie_details):
    release_date = movie_details["release_date"]
    year = int(release_date.split("-")[0])
    return release_date, year


def get_runtime_hhmm(movie_details):
    runtime_minutes = movie_details["runtime"]
    if runtime_minutes:
        return str(runtime_minutes // 60) + "h " + str(runtime_minutes % 60).zfill(2) + "m"
    else:
        return ''


def get_directors(movie_details):
    return [crew["name"] for crew in movie_details["casts"]["crew"] if crew["job"] == 'Director']


def load_spanish_data(movie_details, original_title):
    translated_title = original_title
    overview = movie_details['overview']
    spanish_data = [translation for translation in movie_details["translations"]["translations"] if
                    translation.iso_3166_1 == 'ES' and translation.iso_639_1 == 'es']
    if spanish_data:
        translation_data = spanish_data[0].data
        translated_title = translation_data.title
        overview = translation_data.overview
    return overview, translated_title


def get_original_title(movie_details):
    return movie_details["original_title"]


def get_genres(movie_details, genre_dict):
    genres = [g["name"] for g in movie_details["genres"] if g["name"] not in ignored_genres][0:3]
    translated_genres = [{'name': genre_dict.get(g, g)} for g in genres]
    return translated_genres


def get_countries(movie_details, country_dict):
    countries = [country['name'] for country in movie_details['production_countries']]
    translated_countries = [{'name': country_dict.get(c, c)} for c in countries]
    return translated_countries
