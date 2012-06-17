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
        self._addon.add_directory({'mode': 'search'}, {'title': self._addon.get_string(30209)})
        self._addon.add_directory({'mode': 'reauthenticate'}, {'title': self._addon.get_string(30207)})
    else:
      self._addon.show_ok_dialog([self._addon.get_string(30900), self._addon.get_string(30901), self._addon.get_string(30902)])
      self._addon.add_directory({'mode': 'main'}, {'title': self._addon.get_string(30206)})

    self._addon.add_directory({'mode': 'settings'}, {'title': self._addon.get_string(30205)})
    self._addon.end_of_directory()


  def search(self):
    kb = xbmc.Keyboard(heading = self._addon.get_string(30210))
    kb.doModal()
    if kb.isConfirmed():
      query = kb.getText()
      search_results = self._rdio_api.call('search', query = query, types = 'Artist,Album', extras = 'playCount')
      for result in search_results['results']:
        if result['type'] == self._TYPE_ARTIST:
          self._add_artist(result)
        elif result['type'] == self._TYPE_ALBUM:
          self._add_album(result)

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

  def albums_for_artist(self, **params):
    albums = self._rdio_api.call('getAlbumsForArtist', artist = params['key'], extras = 'playCount', start = 0, count = 9)
    self._add_albums(albums)
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
    img = album['icon'],
    total_items = album['length'],
    is_folder = True)


  def artist(self, **params):
    key = params['key']
    self._addon.add_directory({'mode': 'albums_for_artist', 'key': key}, {'title': self._addon.get_string(30211)})
    self._addon.add_directory({'mode': 'tracks_for_artist', 'key': key}, {'title': self._addon.get_string(30212)})
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
      albums = self._rdio_api.call('getAlbumsForArtistInCollection', artist = params['artist'], user = params['key'], extras = 'playCount')
    else:
      albums = self._rdio_api.call('getAlbumsForArtistInCollection', artist = params['artist'], extras = 'playCount')

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
    track_container = self._rdio_api.call('get', keys = key, extras = 'tracks,playCount')[key]
    self._add_tracks(track_container['tracks'])
    if track_container['type'][0] == self._TYPE_ALBUM or track_container['type'][0] == self._TYPE_ARTIST:
      self._addon.add_directory({'mode': 'artist', 'key': track_container['artistKey']}, {'title': self._addon.get_string(30217)})

    self._addon.end_of_directory()

  def tracks_for_artist(self, **params):
    tracks = self._rdio_api.call('getTracksForArtist', artist = params['key'], extras = 'playCount', start = 0, count = 20)
    self._add_tracks(tracks)
    self._addon.add_directory({'mode': 'artist', 'key': params['key']}, {'title': self._addon.get_string(30217)})
    self._addon.end_of_directory()

  def _add_tracks(self, tracks):
    for track in tracks:
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
        img = track['icon'])


  def play(self, **params):
    key = params['key']
    stream_url = self._rdio_api.resolve_playback_url(key)
    self._addon.resolve_url(stream_url)


  def reauthenticate(self):
    self._rdio_api.logout()
    self.main()


  def settings(self):
    self._addon.show_settings()

  def _mandatory_settings_are_valid(self):
    return self._addon.get_setting('username') and self._addon.get_setting('password') and self._addon.get_setting('apikey') and self._addon.get_setting('apisecret')


  def execute(self):
    start_time = time.clock()
    mode = self._addon.queries['mode']
    self._addon.log_debug("Executing Rdio plugin operation %s with params %s" % (mode, str(self._addon.queries)))
    handler = getattr(self, mode)
    handler_args = inspect.getargspec(handler)
    if handler_args.keywords and len(handler_args.keywords) > 1:
      handler(**self._addon.queries)
    else:
      handler()

    time_ms = (time.clock() - start_time) * 1000
    self._addon.log_debug("Executed Rdio plugin operation %s in %i ms" % (mode, time_ms))


XbmcRdioOperation(addon).execute()
