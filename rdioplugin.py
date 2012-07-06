# Copyright 2012 Charles Blaxland
# This file is part of rdio-xbmc.
#
# rdio-xbmc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# rdio-xbmc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rdio-xbmc.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import inspect
import time
import urllib
import xbmcplugin
from t0mm0.common.addon import Addon
import rdiocommon


ADDON_ID = 'plugin.audio.rdio'
addon = Addon(ADDON_ID, argv=sys.argv)
sys.path.append(os.path.join(addon.get_path(), 'resources', 'lib'))

from rdioxbmc import RdioApi, RdioAuthenticationException


class XbmcRdioOperation:
  _TYPE_ALBUM = 'a'
  _TYPE_ARTIST = 'r'
  _TYPE_PLAYLIST = 'p'
  _TYPE_USER = 's'
  _TYPE_TRACK = 't'
  _TYPE_ALBUM_IN_COLLECTION = 'al'
  _TYPE_ARTIST_IN_COLLECTION = 'rl'

  _PAGE_SIZE_ALBUMS = 100
  _PAGE_SIZE_HEAVY_ROTATION = 14

  def __init__(self, addon):
    self._addon = addon
    self._rdio_api = RdioApi(self._addon)

  def main(self):

    # TODO should get rid of the recursive references to 'mode=main' here as they mess up the ".." nav

    if self._mandatory_settings_are_valid():
      if not self._rdio_api.authenticated():
        try:
          self._rdio_api.authenticate()
        except RdioAuthenticationException, rae:
          self._addon.show_error_dialog([self._addon.get_string(30903), str(rae)])
          self._addon.add_directory({'mode': 'main'}, {'title': self._addon.get_string(30206)})

      if self._rdio_api.authenticated():
        self._addon.add_directory({'mode': 'albums_in_collection'}, {'title': self._addon.get_string(30204)})
        self._addon.add_directory({'mode': 'artists_in_collection'}, {'title': self._addon.get_string(30203)})
        self._addon.add_directory({'mode': 'playlists'}, {'title': self._addon.get_string(30200)})
        self._addon.add_directory({'mode': 'new_releases'}, {'title': self._addon.get_string(30215)})
        self._addon.add_directory({'mode': 'heavy_rotation'}, {'title': self._addon.get_string(30216)})
        self._addon.add_directory({'mode': 'following'}, {'title': self._addon.get_string(30208)})
        self._addon.add_directory({'mode': 'search_artist_album'}, {'title': self._addon.get_string(30209)})
        self._addon.add_directory({'mode': 'search_playlist'}, {'title': self._addon.get_string(30218)})
        self._addon.add_directory({'mode': 'reauthenticate'}, {'title': self._addon.get_string(30207)})
    else:
      self._addon.show_ok_dialog([self._addon.get_string(30900), self._addon.get_string(30901), self._addon.get_string(30902)])
      self._addon.add_directory({'mode': 'main'}, {'title': self._addon.get_string(30206)})

    self._addon.add_directory({'mode': 'settings'}, {'title': self._addon.get_string(30205)})
    self._addon.end_of_directory()

  def search_artist_album(self):
    self._search('Artist,Album')

  def search_playlist(self):
    self._search('Playlist')

  def _search(self, types_to_search):
    kb = xbmc.Keyboard(heading = self._addon.get_string(30210))
    kb.doModal()
    if kb.isConfirmed():
      query = kb.getText()
      search_results = self._rdio_api.call('search', query = query, types = types_to_search, extras = 'playCount')
      for result in search_results['results']:
        if result['type'] == self._TYPE_ARTIST:
          self._add_artist(result)
        elif result['type'] == self._TYPE_ALBUM:
          self._add_album(result)
        elif result['type'] == self._TYPE_PLAYLIST:
          self._add_playlist(result)

    self._addon.end_of_directory()


  def albums_in_collection(self, **params):
    start = int(params['start']) if 'start' in params else 0
    if 'key' in params:
      albums = self._rdio_api.call('getAlbumsInCollection', user = params['key'], extras = 'playCount', count = self._PAGE_SIZE_ALBUMS, start = start)
    else:
      albums = self._rdio_api.call('getAlbumsInCollection', extras = 'playCount', count = self._PAGE_SIZE_ALBUMS, start = start)

    self._add_albums(albums)

    # Add a "More..." menu option if there are too many albums
    if len(albums) == self._PAGE_SIZE_ALBUMS:
      queries = params.copy()
      queries['start'] = start + self._PAGE_SIZE_ALBUMS
      self._addon.add_item(queries, {'title': self._addon.get_string(30214)}, is_folder = True)

    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ALBUM)
    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ARTIST)
    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()

  def all_albums_for_artist(self, **params):
    self._albums_for_artist(**params)

  def top_albums_for_artist(self, **params):
    self._albums_for_artist(True, **params)

  def _albums_for_artist(self, top_only = False, **params):
    if top_only:
      albums = self._rdio_api.call('getAlbumsForArtist', artist = params['key'], extras = 'playCount', start = 0, count = 9)
    else:
      albums = self._rdio_api.call('getAlbumsForArtist', artist = params['key'], extras = 'playCount')

    self._add_albums(albums)

    if not top_only:
      xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ALBUM)
      xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_DATE)
    else:
      self._addon.add_directory({'mode': 'all_albums_for_artist', 'key': params['key']}, {'title': self._addon.get_string(30222)})

    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()

  def new_releases(self):
    albums = self._rdio_api.call('getNewReleases', extras = 'playCount')
    self._add_albums(albums)
    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()

  def heavy_rotation(self):
    albums = self._rdio_api.call('getHeavyRotation', user = self._rdio_api.current_user(),
      friends = True, type = 'albums', start = 0, count = self._PAGE_SIZE_HEAVY_ROTATION, extras = 'playCount')
    self._add_albums(albums)
    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()

  def _add_albums(self, albums):
    for album in albums:
      self._add_album(album)

  def _add_album(self, album):
    album_key = album['albumKey'] if 'albumKey' in album else album['key']
    add_collection_context_menu_item = self._build_context_menu_item(self._addon.get_string(30219), mode = 'add_to_collection', key = album_key)
    remove_collection_context_menu_item = self._build_context_menu_item(self._addon.get_string(30220), mode = 'remove_from_collection', key = album_key)

    self._addon.add_item({'mode': 'tracks', 'key': album['key']},
    {
      'title': '%s (%s)' % (album['name'], album['artist']),
      'album': album['name'],
      'artist': album['artist'],
      'date': rdiocommon.iso_date_to_xbmc_date(album['releaseDate']),
      'duration': album['duration'],
      'playCount': album['playCount']
    },
    item_type = 'music',
    contextmenu_items = [add_collection_context_menu_item, remove_collection_context_menu_item],
    img = album['icon'],
    total_items = album['length'],
    is_folder = True)


  def artist(self, **params):
    key = params['key']
    self._addon.add_directory({'mode': 'top_albums_for_artist', 'key': key}, {'title': self._addon.get_string(30211)})
    self._addon.add_directory({'mode': 'tracks_for_artist', 'key': key}, {'title': self._addon.get_string(30212)})
    self._addon.add_directory({'mode': 'all_albums_for_artist', 'key': key}, {'title': self._addon.get_string(30221)})
    self._addon.add_directory({'mode': 'related_artists', 'key': key}, {'title': self._addon.get_string(30213)})
    self._addon.end_of_directory()

  def artists_in_collection(self, **params):
    if 'key' in params:
      artists = self._rdio_api.call('getArtistsInCollection', user = params['key'])
    else:
      artists = self._rdio_api.call('getArtistsInCollection')

    for artist in artists:
      self._add_artist(artist)

    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ARTIST)
    xbmcplugin.setContent(self._addon.handle, 'artists')
    self._addon.end_of_directory()

  def albums_for_artist_in_collection(self, **params):
    if 'key' in params:
      albums = self._rdio_api.call('getAlbumsForArtistInCollection', artist = params['artist'], user = params['key'], extras = 'playCount,Track.isInCollection')
    else:
      albums = self._rdio_api.call('getAlbumsForArtistInCollection', artist = params['artist'], extras = 'playCount,Track.isInCollection')

    if len(albums) == 1:
      album = albums[0]
      self._add_tracks(album['tracks'])
    else:
      self._add_albums(albums)
      xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ALBUM)
      xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_DATE)
      xbmcplugin.setContent(self._addon.handle, 'albums')

    self._addon.add_directory({'mode': 'artist', 'key': params['artist']}, {'title': self._addon.get_string(30217)})
    self._addon.end_of_directory()

  def related_artists(self, **params):
    artists = self._rdio_api.call('getRelatedArtists', artist = params['key'])
    for artist in artists:
      self._add_artist(artist)

    xbmcplugin.setContent(self._addon.handle, 'artists')
    self._addon.end_of_directory()

  def _add_artist(self, artist):
    queries = {'mode': 'artist', 'key': artist['key']}
    if artist['type'] == self._TYPE_ARTIST_IN_COLLECTION:
      queries['mode'] = 'albums_for_artist_in_collection'
      queries['key'] = artist['userKey']
      queries['artist'] = artist['artistKey']

    self._addon.add_item(queries,
      {
        'title': artist['name'],
        'artist': artist['name']
      },
      item_type = 'music',
      img = artist['icon'],
      is_folder = True)


  def playlists(self, **params):
    if 'key' in params:
      playlists = self._rdio_api.call('getPlaylists', user = params['key'], extras = 'description')
    else:
      playlists = self._rdio_api.call('getPlaylists', extras = 'description')

    self._add_playlists(playlists['owned'])
    self._add_playlists(playlists['collab'])
    self._add_playlists(playlists['subscribed'])

    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()

  def _add_playlists(self, playlists):
    for playlist in playlists:
      self._add_playlist(playlist)

  def _add_playlist(self, playlist):
    playlist_title = '%s (%s)' % (playlist['name'], playlist['owner'])
    self._addon.add_item({'mode': 'tracks', 'key': playlist['key']},
      {
        'title': playlist_title,
        'album': playlist['name'],
        'artist': playlist['owner']
      },
      item_type = 'music',
      img = playlist['icon'],
      total_items = playlist['length'],
      is_folder = True)


  def following(self):
    followed_users = self._rdio_api.call('userFollowing', user = self._rdio_api.current_user())
    for followed_user in followed_users:
      self._add_user(followed_user)

    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ARTIST)
    xbmcplugin.setContent(self._addon.handle, 'artists')
    self._addon.end_of_directory()


  def user(self, **params):
    key = params['key']
    self._addon.add_directory({'mode': 'albums_in_collection', 'key': key}, {'title': self._addon.get_string(30204)})
    self._addon.add_directory({'mode': 'artists_in_collection', 'key': key}, {'title': self._addon.get_string(30203)})
    self._addon.add_directory({'mode': 'playlists', 'key': key}, {'title': self._addon.get_string(30200)})
    self._addon.end_of_directory()

  def _add_user(self, user):
    name = user['firstName']
    if user['lastName']:
      name += ' ' + user['lastName']

    self._addon.add_item({'mode': 'user', 'key': user['key']},
      {
        'title': name,
        'artist': name
      },
      item_type = 'music',
      img = user['icon'],
      is_folder = True)


  def tracks(self, **params):
    key = params['key']
    track_container = self._rdio_api.call('get', keys = key, extras = 'tracks,Track.isInCollection,playCount')[key]
    self._add_tracks(track_container['tracks'])

    # Add "More from this artist" link if container is an album or artist
    if track_container['type'][0] == self._TYPE_ALBUM or track_container['type'][0] == self._TYPE_ARTIST:
      self._addon.add_directory({'mode': 'artist', 'key': track_container['artistKey']}, {'title': self._addon.get_string(30217)})

    self._addon.end_of_directory()

  def tracks_for_artist(self, **params):
    tracks = self._rdio_api.call('getTracksForArtist', artist = params['key'], extras = 'playCount,isInCollection', start = 0, count = 20)
    self._add_tracks(tracks)
    self._addon.add_directory({'mode': 'artist', 'key': params['key']}, {'title': self._addon.get_string(30217)})
    self._addon.end_of_directory()

  def _add_tracks(self, tracks):
    for track in tracks:

      if track['isInCollection']:
        collection_context_menu_item = self._build_context_menu_item(self._addon.get_string(30220), mode = 'remove_from_collection', key = track['key'])
      else:
        collection_context_menu_item = self._build_context_menu_item(self._addon.get_string(30219), mode = 'add_to_collection', key = track['key'])

      if not 'playCount' in track:
        track['playCount'] = 0

      self._addon.add_item({'mode': 'play', 'key': track['key']},
        {
          'title': track['name'],
          'artist': track['artist'],
          'album': track['album'],
          'duration': track['duration'],
          'tracknumber': track['trackNum'],
          'playCount': track['playCount']
        },
        item_type = 'music',
        contextmenu_items = [collection_context_menu_item],
        img = track['icon'])


  def play(self, **params):
    key = params['key']
    stream_url = self._rdio_api.resolve_playback_url(key)
    if stream_url:
      self._addon.resolve_url(stream_url)


  def add_to_collection(self, **params):
    key = params['key']
    if self._is_track_key(key):
      track_keys= [key]
    else:
      track_keys = self._get_track_keys_not_in_collection(key)

    if track_keys:
      self._rdio_api.call('addToCollection', keys = ','.join(track_keys))

  def remove_from_collection(self, **params):
    key = params['key']
    if self._is_track_key(key):
      track_keys= [key]
    else:
      track_keys = self._get_track_keys_in_collection(key)

    if track_keys:
      self._rdio_api.call('removeFromCollection', keys = ','.join(track_keys))

  def _get_track_keys_in_collection(self, key):
    return self._get_track_keys(key, in_collection = True, not_in_collection = False)

  def _get_track_keys_not_in_collection(self, key):
    return self._get_track_keys(key, in_collection = False, not_in_collection = True)

  def _get_track_keys(self, key, in_collection = True, not_in_collection = True):
    track_keys = []
    track_container = self._rdio_api.call('get', keys = key, extras = 'tracks,Track.isInCollection')
    for track in track_container[key]['tracks']:
      if ((in_collection and track['isInCollection']) or (not_in_collection and not track['isInCollection'])):
        track_keys.append(track['key'])

    return track_keys


  def reauthenticate(self):
    self._rdio_api.logout()
    self.main()


  def settings(self):
    self._addon.show_settings()

  def _mandatory_settings_are_valid(self):
    return self._addon.get_setting('username') and self._addon.get_setting('password') and self._addon.get_setting('apikey') and self._addon.get_setting('apisecret')


  def _build_context_menu_item(self, menu_text, **queries):
    url = 'special://home/addons/%s/%s' % (ADDON_ID, os.path.basename(__file__))
    params = str(self._addon.handle) + ",?" + urllib.urlencode(queries)
    return (menu_text, 'XBMC.RunScript(%s, %s)' % (url, params))


  def _is_track_key(self, key):
    return key[0] == self._TYPE_TRACK and key[1].isdigit()


  def execute(self):
    start_time = time.clock()
    mode = self._addon.queries['mode']
    self._addon.log_notice("Executing Rdio %s addon operation %s with params %s" % (self._addon.get_version(), mode, str(self._addon.queries)))
    handler = getattr(self, mode)
    handler_args = inspect.getargspec(handler)
    if handler_args.keywords and len(handler_args.keywords) > 1:
      handler(**self._addon.queries)
    else:
      handler()

    time_ms = (time.clock() - start_time) * 1000
    self._addon.log_notice("Executed Rdio addon operation %s in %i ms" % (mode, time_ms))


XbmcRdioOperation(addon).execute()
