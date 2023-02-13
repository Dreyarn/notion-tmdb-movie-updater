# Notion & TMDB movie scraper and updater

This is a Python script I created in order to update my Notion movie database with information and covers from TheMovieDatabase.
It is probably not good code, but I hacked it away little by little in order to touch some Python and improve my Notion page.

## **Requirements:**
### Libraries
* notion-client
* tmdbv3api
* argparse
### Preparation
#### Notion
* Create a [Notion integration](https://www.notion.so/my-integrations) for this script and save its internal integration token (AKA secret).
* In your Notion database, save its ID: [here's how to](https://stackoverflow.com/questions/67728038/where-to-find-database-id-for-my-database-in-notion).
* In that same Notion database, open the upper-right "..." menu and it to your newly created integration.
#### TheMovieDb.org
* Create a user account (or use your existing one) and, in settings go to the API tab and register yourself as an API user. 
* When you get accepted (this is usually fast), save your API key.
#### Python files
* Update **countries.txt** and **genres.txt** with the desired translations for country and genre names
    * Here you can add or delete countries and genres
* Update **constants.py** with:
    * Your Notion Secret
    * Your Notion Database ID 
    * Your Access Key for the TheMovieDatabase API
    * For each field, the name it has in your notion database
        * The "Loaded" field is important and will allow the script to only update newly added movies.
    
## Launch and behavior
Script is executed by calling the main.py file.
It will:
* Search your Notion database and retrieve its movies
* For each movie:
    * Retrieve its information from TMDB using its name, IMDB URL/id or TMDB URL/id
        * _Search precedence: TMDB info > IMDB info > movie name from Notion_
    * Parse the retrieved information and update the corresponding Notion page
#### Launch parameters
Two command line flags can be used when launching the script:
* **-t** (test): The script will parse the movies it has found, but not update them
* **-f** (full): The script will not filter by the "loaded" flag when searching, so it will process your whole database

[Notion integration]: https://www.notion.so/my-integrations