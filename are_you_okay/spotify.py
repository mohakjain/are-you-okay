
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, session
)
import spotipy
from spotipy import oauth2

bp = Blueprint('spotify', __name__)


SCOPE = 'user-top-read'

CACHE = '.spotifycache'
# Reads client id and client secret from environment variables
spotifyAuth = oauth2.SpotifyOAuth(scope=SCOPE,cache_path=CACHE)

@bp.route('/', methods=['GET'])
def login():
    cachedToken = spotifyAuth.get_cached_token()
    if cachedToken and not spotifyAuth.is_token_expired(cachedToken):
        token = cachedToken['access_token']
        session['access_token'] = token
        return redirect(url_for('spotify.getData'))
    else:
        loginUrl = spotifyAuth.get_authorize_url()
        return redirect(loginUrl)

@bp.route('/oauth/callback', methods=['GET'])
def setToken():
    token = request.args['code']
    token_info = spotifyAuth.get_access_token(token)
    access_token = token_info['access_token']
    session['access_token'] = access_token
    return redirect(url_for('spotify.are_you_okay'))

# Get user's spotify data
@bp.route('/are_you_okay', methods=['GET'])
def getData():
    access_token = session['access_token']
    spotifyAPI = spotipy.Spotify(access_token)
    
    # Fetch the user's top 50 artists
    topArtists = getTopArtists(spotifyAPI)
    print([t["artist_name"] for t in topArtists])
 
    # Fetch the user's top songs
    topSongs = getTopSongs(spotifyAPI)
    print(len(topSongs))
    print([t["track_name"] for t in topSongs])



    return render_template('hello.html')
    return render_template('user.html', user=user)



# Fetch the user's top 50 artists
def getTopArtists(spotifyAPI: spotipy.Spotify):
    topArtistsResult = spotifyAPI.current_user_top_artists(limit=50)
    topArtists = []
    for t in topArtistsResult['items']:
        artist = {}
        artist['artist_name'] = t['name']
        artist['artist_id'] = t['id']
        topArtists.append(artist)
    return topArtists

# Fetch the user's top songs
def getTopSongs(spotifyAPI: spotipy.Spotify):
    topSongsResultMediumTerm = spotifyAPI.current_user_top_tracks(limit=50, time_range="medium_term")
    trackIds = set()
    topSongs = []
    for t in topSongsResultMediumTerm['items']:
        song = {}
        song['artist_name'] = t['artists'][0]['name']
        song['track_name'] = t['name']
        song['album_name'] = t['album']['name']
        song['album_image'] = t['album']['images'][0]['url']
        song['track_id'] = t['id']
        trackIds.add(song['track_id'])
        topSongs.append(song)

    topSongsResultShortTerm = spotifyAPI.current_user_top_tracks(limit=50, time_range="short_term")
    for t in topSongsResultShortTerm['items']:
        if t['id'] in trackIds:
            continue
        else:
            song = {}
            song['artist_name'] = t['artists'][0]['name']
            song['track_name'] = t['name']
            song['album_name'] = t['album']['name']
            song['album_image'] = t['album']['images'][0]['url']
            song['track_id'] = t['id']
            trackIds.add(song['track_id'])
            topSongs.append(song)
    
    return topSongs