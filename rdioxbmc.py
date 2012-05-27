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
from t0mm0.common.addon import Addon

ADDON_ID = 'plugin.audio.rdio'
addon = Addon(ADDON_ID, argv=sys.argv)
sys.path.append(os.path.join(addon.get_path(), 'resources', 'lib'))

from rdioapi import RdioApi


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
      self._addon.add_directory({'mode': 'tracks', 'key': album['key']}, { 'title': '%s (%s)' % (album['name'], album['artist']) })
      
    self._addon.end_of_directory()
    
  def artists(self):
    artists = self._rdio_api.call('getArtistsInCollection')
    for artist in artists:
      self._addon.add_directory({'mode': 'tracks', 'key': artist['key']}, {'title': artist['name']})
      
    self._addon.end_of_directory()

  def playlists(self):
    playlists = self._rdio_api.call('getPlaylists')
    for playlist in playlists['owned']:
      self._addon.add_directory({'mode': 'tracks', 'key': playlist['key']}, {'title': playlist['name']})

    for playlist in playlists['collab']:
      self._addon.add_directory({'mode': 'tracks', 'key': playlist['key']}, { 'title': '%s (%s)' % (playlist['name'], self._addon.get_string(30201)) })

    for playlist in playlists['subscribed']:
      self._addon.add_directory({'mode': 'tracks', 'key': playlist['key']}, { 'title': '%s (%s)' % (playlist['name'], self._addon.get_string(30202)) })

    self._addon.end_of_directory()
    
  def tracks(self, **params):
    key = params['key']
    track_container = self._rdio_api.call('get', keys = key, extras = 'tracks')[key]
    for track in track_container['tracks']:
      self._addon.add_item({'mode': 'play', 'key': track['key']}, {'title': track['name']}, item_type = 'music')
      
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
