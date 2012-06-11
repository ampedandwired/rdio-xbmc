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
        self._addon.add_directory({'mode': 'albums'}, {'title': self._addon.get_string(30204)})
        self._addon.add_directory({'mode': 'artists'}, {'title': self._addon.get_string(30203)})
        self._addon.add_directory({'mode': 'playlists'}, {'title': self._addon.get_string(30200)})
        self._addon.add_directory({'mode': 'following'}, {'title': self._addon.get_string(30208)})
        self._addon.add_directory({'mode': 'reauthenticate'}, {'title': self._addon.get_string(30207)})
    else:
      self._addon.show_ok_dialog([self._addon.get_string(30900), self._addon.get_string(30901), self._addon.get_string(30902)])
      self._addon.add_directory({'mode': 'main'}, {'title': self._addon.get_string(30206)})

    self._addon.add_directory({'mode': 'settings'}, {'title': self._addon.get_string(30205)})
    self._addon.end_of_directory()


  def albums(self, **params):
    if 'key' in params:
      albums = self._rdio_api.call('getAlbumsInCollection', user = params['key'])
    else:
      albums = self._rdio_api.call('getAlbumsInCollection')

    for album in albums:
      self._addon.add_item({'mode': 'tracks', 'key': album['key']},
        {
          'title': '%s (%s)' % (album['name'], album['artist']),
          'album': album['name'],
          'artist': album['artist'],
          'date': rdiocommon.iso_date_to_xbmc_date(album['releaseDate']),
          'duration': album['duration']
        },
        item_type = 'music',
        img = album['icon'],
        total_items = album['length'],
        is_folder = True)

    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ALBUM)
    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ARTIST)
    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()


  def artists(self):
    artists = self._rdio_api.call('getArtistsInCollection')
    for artist in artists:
      self._addon.add_item({'mode': 'tracks', 'key': artist['key']},
        {
          'title': artist['name'],
          'artist': artist['name']
        },
        item_type = 'music',
        img = artist['icon'],
        is_folder = True)

    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ARTIST)
    xbmcplugin.setContent(self._addon.handle, 'artists')
    self._addon.end_of_directory()


  def playlists(self):
    playlists = self._rdio_api.call('getPlaylists', extras = 'description')
    self._add_playlist(playlists, 'owned')
    self._add_playlist(playlists, 'collab')
    self._add_playlist(playlists, 'subscribed')

    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()

  def _add_playlist(self, playlists, playlist_type):
    for playlist in playlists[playlist_type]:
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
    following = self._rdio_api.call('userFollowing', user = self._rdio_api.current_user())
    for followed_person in following:
      name = followed_person['firstName']
      if followed_person['lastName']:
        name += ' ' + followed_person['lastName']

      self._addon.add_item({'mode': 'person', 'key': followed_person['key']},
        {
          'title': name,
          'artist': name
        },
        item_type = 'music',
        img = followed_person['icon'],
        is_folder = True)

    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ARTIST)
    xbmcplugin.setContent(self._addon.handle, 'artists')
    self._addon.end_of_directory()


  def person(self, **params):
    key = params['key']
    self._addon.add_directory({'mode': 'albums', 'key': key}, {'title': self._addon.get_string(30204)})
    self._addon.end_of_directory()


  def tracks(self, **params):
    key = params['key']
    track_container = self._rdio_api.call('get', keys = key, extras = 'tracks')[key]
    for track in track_container['tracks']:
      self._addon.add_item({'mode': 'play', 'key': track['key']},
        {
          'title': track['name'],
          'artist': track['artist'],
          'album': track['album'],
          'duration': track['duration'],
          'tracknumber': track['trackNum']
        },
        item_type = 'music',
        img = track['icon'])

    self._addon.end_of_directory()


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
