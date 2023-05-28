
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
        return redirect(url_for('spotify.are_you_okay'))
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

@bp.route('/are_you_okay', methods=['GET'])
def are_you_okay():
    topArtists, topSongs = getData()
    percentOkay, topSongs = determineOkayness(topArtists, topSongs)
    print(percentOkay*100, "% okay")

    # print all songs and okayness
    for song in topSongs:
        print(song['track_name'], song['okayness'])

    # flask can return a dict of variables to the react app
    return {'percentOkay': percentOkay, 'topSongs': topSongs}

    return render_template('hello.html')

def determineOkayness(topArtists, topSongs):

    # Heurestic via OLS
    weights = {
        'danceability': 1.13672760,
        'energy': .707503208,
        'loudness': -.0216086695,
        'acousticness': -.181718205,
        'valence': .260874576,
        'instrumentalness': .0799966934,
        'tempo': -.000139013606
    }
    offset= -0.7663552990979238
    threshold = 0.6

    okay = 0
    for song in topSongs:
        song['okayness'] = 0
        for feature in song:
            if feature in weights:
                song['okayness'] += song[feature] * weights[feature]
        song['okayness'] += offset
        if song['okayness'] > threshold:
            okay += 1
    
    topSongs.sort(key=lambda x: x['okayness'])
    percentOkay = okay/len(topSongs)
    # now we need to determine okayness based on artists. I'll check if any artist is in my list of not okay artists and subtract a little bit from the okay score if so.
    for artist in topArtists:
        if artist in notOkayArtists:
            percentOkay -= 0.05

    return percentOkay, topSongs

# Get user's relevant spotify data
def getData():
    access_token = session['access_token']
    spotifyAPI = spotipy.Spotify(access_token)
    
    # Fetch the user's top 50 artists
    topArtists = getTopArtists(spotifyAPI)
 
    # Fetch the user's top songs
    topSongs = getTopSongs(spotifyAPI)

    return topArtists, topSongs


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
            song['track_id'] = t['id']
            trackIds.add(song['track_id'])
            topSongs.append(song)
    
    # can make this more efficient by storing topSongs in a dict
    audioFeatures = spotifyAPI.audio_features(tracks=list(trackIds))
    for features in audioFeatures:
        for song in topSongs:
            if features['id'] == song['track_id']:
                song['danceability'] = features['danceability']
                song['energy'] = features['energy']
                song['loudness'] = features['loudness']
                song['acousticness'] = features['acousticness']
                song['instrumentalness'] = features['instrumentalness']
                song['valence'] = features['valence']
                song['tempo'] = features['tempo']
                break
    
    return topSongs


notOkayArtists = ["Phoebe Bridgers"]


def printSongData(songs):
    for song in songs:
        # print song attributes separated by tabs
        print(song['track_name'], "\t", song['danceability'], "\t", song['energy'], "\t", song['loudness'], "\t", song['acousticness'], "\t", song['instrumentalness'], "\t", song['valence'], "\t", song['tempo'], "\t", song['okayness'])
