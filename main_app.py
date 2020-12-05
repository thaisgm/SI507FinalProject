# Thais Gonzalez Final Project

# uniqname = thaisgm

from bs4 import BeautifulSoup
import secrets
import requests
import json
import base64

class Album: 
    
    def __init__(self, album_name, artist_name, release_date, spotify_link):
        self.album_name = album_name
        self.artist_name = artist_name
        self.release_date = release_date
        self.spotify_link = spotify_link
    
    def info(self):
        return f"{self.album_name} by {self.artist_name}, released: {self.release_date} ({self.spotify_link})"

def scrape_genres():
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
    page = requests.get('https://www.udiscovermusic.com/udiscover-genres/')
    soup = BeautifulSoup(page.text, 'html.parser')
    genre_list = soup.find_all(class_='mega-menu-item mega-menu-item-type-custom mega-menu-item-object-custom mega-menu-columns-1-of-5')

    return_genre_dict = {}

    for item in genre_list:
        genre = item.text
        genre_link = item.find('a').get('href')
        full_genre_link = 'https://www.udiscovermusic.com/' + genre_link
        return_genre_dict[genre] = full_genre_link
    
    return return_genre_dict

def get_genre_articles(dictionary, genre):
    ''' Returns a list of articles to the user from "https://www.udiscovermusic.com/udiscover-genres/"
    
    Parameters
    ----------
    None

    Returns
    -------
    '''
    site_url = dictionary[genre]
    page = requests.get(site_url)
    soup = BeautifulSoup(page.text, 'html.parser')
    genre_list = soup.find_all(class_='mvp-blog-story-wrap left relative infinite-post')
    
    genre_headlines_dict = {}

    index = 1

    for item in genre_list:
        while index < 6:
            temp_list = []
            temp_list.append(item.find(class_='mvp-blog-story-text left relative').find('h2').text)
            temp_list.append(item.find('a').get('href'))
            genre_headlines_dict[index] = temp_list
    
    print('HOW DEM APPLES, ', genre_headlines_dict)

    return


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
        #replace with SQL database
        all_albums.append(new_album)
        x += 1
    
    for i in all_albums: 
        print(i.info())
        print('----------------------')

def create_sql_table(Album):
    CREATE TABLE table_name(
   column1 datatype,
   column2 datatype,
   column3 datatype,
   .....
   columnN datatype,
);


#something = scrape_genres()
#scrape_moods(something, 'Alternative')
token = spotify_authorization_request()
print(token)
spotify_api_request(token, 'country')
