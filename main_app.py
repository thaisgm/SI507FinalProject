# Thais Gonzalez Final Project

# uniqname = thaisgm

from bs4 import BeautifulSoup
import secrets
import requests
import json
import base64
import sqlite3
import webbrowser

CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {}

class Album: 
    
    def __init__(self, album_name, artist_name, release_date, spotify_link):
        self.album_name = album_name
        self.artist_name = artist_name
        self.release_date = release_date
        self.spotify_link = spotify_link
    
    def info(self):
        return f"{self.album_name} by {self.artist_name}, released: {self.release_date} ({self.spotify_link})"

def load_cache():
    try: 
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME, 'w')
    content_to_write = json.dumps(cache)
    cache_file.write(content_to_write)
    cache_file.close()

def make_url_request_with_caching(url, cache): 
    if (url in cache.keys()):
        print('Using cache...')
        return cache[url]
    else: 
        print('Fetching...')
        #time.sleep(1)
        page = requests.get(url)
        cache[url] = page.text
        save_cache(cache)
        return cache[url]


def scrape_genres(cache):
    ''' Returns a list of genre options to the user from "https://www.udiscovermusic.com/udiscover-genres/"
    
    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is index number and value is genre
        e.g. {1: 'Blues', 2: 'Classical', etc.}
    '''
    page = make_url_request_with_caching('https://www.udiscovermusic.com/udiscover-genres/', cache)
    soup = BeautifulSoup(page, 'html.parser')
    genre_list = soup.find_all(class_='mega-menu-item mega-menu-item-type-custom mega-menu-item-object-custom mega-menu-columns-1-of-5')

    return_genre_dict = {}

    for item in genre_list:
        genre = item.text.lower()
        genre_link = item.find('a').get('href')
        full_genre_link = 'https://www.udiscovermusic.com' + genre_link
        return_genre_dict[genre] = full_genre_link

    return_genre_dict['punk-rock'] = return_genre_dict['prog rock']
    del return_genre_dict['prog rock']

    return_genre_dict['r-n-b'] = return_genre_dict['r&b']
    del return_genre_dict['r&b']

    return_genre_dict['rock-n-roll'] = return_genre_dict["rock 'n' roll"]
    del return_genre_dict["rock 'n' roll"]
    
    return return_genre_dict

def get_genre_articles(dictionary, genre, cache):
    ''' Returns a list of articles to the user from "https://www.udiscovermusic.com/udiscover-genres/"
    
    Parameters
    ----------
    None

    Returns
    -------
    '''
    site_url = dictionary[genre]
    page = make_url_request_with_caching(site_url, cache)
    soup = BeautifulSoup(page, 'html.parser')
    genre_list = soup.find_all(class_='mvp-blog-story-wrap left relative infinite-post')
    
    genre_headlines_dict = {}

    index = 1

    for item in genre_list:
        temp_list = []
        temp_list.append(item.find(class_='mvp-blog-story-text left relative').find('h2').text)
        temp_list.append(item.find('a').get('href'))
        genre_headlines_dict[index] = temp_list
        index+=1
    
    return genre_headlines_dict

def spotify_authorization_request():
    ''' Returns a list of results from spotify API

    Parameters
    ----------
    None

    Returns
    -------
    list
        recommendations based on the seed genre provided by the user
    '''
    # spotify requires authorization to utilize API. I am issuing authorization based on my client ID and client secret, not an individual user authorization flow
    auth_str = '{}:{}'.format(secrets.CLIENT_ID, secrets.CLIENT_SECRET)

    b64_auth_str = base64.urlsafe_b64encode(auth_str.encode()).decode()

    headers = {
    'Authorization': 'Basic {}'.format(b64_auth_str)
    }

    data = {
    'grant_type': 'client_credentials'
    }

    post_request = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)

    response_data = json.loads(post_request.text)

    # the access_token allows access to general spotify API
    access_token = response_data['access_token']

    return(access_token)

def spotify_api_request(access_token, genre):
    ''' Returns a list of results from spotify API

    Parameters
    ----------
    None

    Returns
    -------
    list
        recommendations based on the seed genre provided by the user
    '''

    headers = {
    'Authorization': 'Bearer {}'.format(access_token)
    }

    params = (
        ('seed_genres', genre),
        ('min_energy', '0.4'),
        ('min_popularity', '50'),
        ('market', 'US'),
        ('limit', '10')
    )

    get_request = requests.get('https://api.spotify.com/v1/recommendations', headers=headers, params=params)

    response_data = json.loads(get_request.content)

    x = 0

    all_albums = []

    while x < 10:
        spotify_link = response_data['tracks'][x]['external_urls']['spotify']
        album_name = response_data['tracks'][x]['album']['name']
        artist_name = response_data['tracks'][x]['album']['artists'][0]['name']
        release_date = response_data['tracks'][x]['album']['release_date']
        new_album = Album(album_name, artist_name, release_date, spotify_link)
        all_albums.append(new_album)
        x += 1
        
        #uploads information to SQL Table
        connection = sqlite3.connect("Album_Collection.sqlite")
        cursor = connection.cursor()
        sql = ('''INSERT INTO ALBUMS(album_name, artist_name, release_date, spotify_link) VALUES (?, ?, ?, ?);''')
        data_tuple = (new_album.album_name, new_album.artist_name, new_album.release_date, new_album.spotify_link)

        cursor.execute(sql, data_tuple)
        connection.commit()
        cursor.close()
        
    
    for i in all_albums: 
        print(i.info())
        print('----------------------')

def genre_options(cache):
     genre_dict = scrape_genres(cache)
     index = 0
     
     print('-------------')
     print('GENRE OPTIONS')
     print('-------------')
     
     temp_genre_list = []
     
     for i in genre_dict:
         print(index,  i)
         temp_genre_list.append(i)
         index+=1

     return temp_genre_list
    
def article_options(article_dictionary):
    #prints article options

    for key in article_dictionary.keys():
        print(key, ": ", article_dictionary[key][0])

    article_input = input('Select a number to read one of these articles? Or `exit` the program? ')
 
    if (article_input == 'exit'):
        print('Bye!')
    else: 
        article_website = article_dictionary[int(article_input)][1]
        print('Launching...')
        print(article_website)
        print('in web browser...')
        webbrowser.open_new(article_website)

def create_sql_table():

    connection = sqlite3.connect("Album_Collection.sqlite")
    cursor = connection.cursor()
    sql = "CREATE TABLE ALBUMS(album_name , artist_name , release_date , spotify_link )"
    result = cursor.execute(sql).fetchall()
    print(result)
    connection.close()

def user_interface():

    CACHE_DICT = load_cache()

    intial_input = input('Hi! Would you like to explore genres or our database of albums? Reply `genres` or `albums` to explore or `No` to exit the program: ')
     
    if (intial_input == 'genres'):

        genre_dict = scrape_genres(CACHE_DICT) 

        genre_list = genre_options(CACHE_DICT)
        print('-------------')
        alt_input = input('Select the number of a genre you would like to explore further: ')
        print('-------------')
        genre_choice = genre_list[int(alt_input)]
        next_input = input('You chose ' + genre_choice + ', would you like to explore `news`, `recommendations`, `genre page`, or `exit`? ')
        print('-------------')
        
        if (next_input == 'news'):
            #presents the news articles for the particular genre and asks if the user would like to open one in their browser
            article_dict = get_genre_articles(genre_dict, genre_choice, CACHE_DICT)
            article_options(article_dict)

        elif (next_input == 'recommendations'):
            #recommendations
            token = spotify_authorization_request()
            spotify_api_request(token, genre_choice)

        elif (next_input == 'genre page'):
            #opens the main genre page in the user's browser
            print('Launching...')
            print(genre_dict[genre_list[int(alt_input)]])
            print('in web browser...')
            webbrowser.open_new(genre_dict[genre_list[int(alt_input)]])

        elif (next_input == 'exit'):
            #quits the program
            print('Bye!')

    elif (intial_input == 'albums'):
        #goes to database program exploration
        print('In albums')
        albums_input = input('Search our database by `album name` or `artist name`: ')
        if (albums_input == 'album name'):
            album_name = input('Search an album name, will return the first result or not available: ')
            #search database for album name
            connection = sqlite3.connect("Album_Collection.sqlite")
            cursor = connection.cursor()
            query = "SELECT * FROM ALBUMS WHERE album_name = '" + album_name + "' "
            result = cursor.execute(query).fetchone()
            connection.close()
            listen_input = input('We found the album ' + result[0] + ' by ' + result[1] + ' released ' + result[2] + '. Would you like to listen? `yes` or `exit`: ')
            if (listen_input == 'yes'):
                print('Launching...')
                print(result[3])
                print('in web browser...')
                webbrowser.open_new(result[3])
            else: 
                print('Bye!')

        elif (albums_input == 'artist name'):
            artist_name = input('Search an artist name, will return the first result or not available: ')
            #search database for artist name
            connection = sqlite3.connect("Album_Collection.sqlite")
            cursor = connection.cursor()
            query = "SELECT * FROM ALBUMS WHERE album_name = '" + artist_name + "' "
            result = cursor.execute(query).fetchone()
            connection.close()
            listen_input = input('We found the album ' + result[0] + ' by ' + result[1] + ' released ' + result[2] + '. Would you like to listen? `yes` or `exit`: ')
            if (listen_input == 'yes'):
                print('Launching...')
                print(result[3])
                print('in web browser...')
                webbrowser.open_new(result[3])
            else: 
                print('Bye!')
    else: 
        print('Bye!')

user_interface()