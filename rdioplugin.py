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
import xbmcplugin
from t0mm0.common.addon import Addon
import rdiocommon

ADDON_ID = 'plugin.audio.rdio'
addon = Addon(ADDON_ID, argv=sys.argv)
sys.path.append(os.path.join(addon.get_path(), 'resources', 'lib'))

from rdioxbmc import RdioApi


class XbmcRdioOperation:
  
  def __init__(self, addon):
    self._addon = addon
    self._rdio_api = RdioApi(self._addon)

  def main(self):
    self._addon.add_directory({'mode': 'albums'}, {'title': self._addon.get_string(30204)})
    self._addon.add_directory({'mode': 'artists'}, {'title': self._addon.get_string(30203)})
    self._addon.add_directory({'mode': 'playlists'}, {'title': self._addon.get_string(30200)})
    self._addon.add_directory({'mode': 'settings'}, {'title': self._addon.get_string(30205)})
    self._addon.end_of_directory()

  def albums(self):
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
      playlist_title = playlist['name'] if playlist_type == 'owned' else '%s (%s)' % (playlist['name'], playlist['owner'])
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

  def settings(self):
    self._addon.show_settings()
    
  def execute(self):
    self._addon.log_debug("Executing Rdio operation: " + str(self._addon.queries))
    handler = getattr(self, self._addon.queries['mode'])
    handler_args = inspect.getargspec(handler)
    if handler_args.keywords and len(handler_args.keywords) > 1:
      handler(**self._addon.queries)
    else:
      handler()


XbmcRdioOperation(addon).execute()
