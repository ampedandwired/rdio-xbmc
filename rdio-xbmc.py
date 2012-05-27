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
from urlparse import urlparse, parse_qs
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
import CommonFunctions

ADDON_ID = 'plugin.audio.rdio'
addon = Addon(ADDON_ID, argv=sys.argv)
sys.path.append(os.path.join(addon.get_path(), 'resources', 'lib'))

from rdioapi import Rdio
from rdiostream import get_rtmp_info

RDIO_DOMAIN = 'localhost'

class XbmcRdioOperation:
  
  def __init__(self, addon):
    self._addon = addon
    self._rdio_api = RdioApi(self._addon)
    
  def main(self):
    self._addon.add_item({'mode': 'get_playback_token'}, {'title': 'Token'})
    self._addon.add_item({'mode': 'play', 'rdio_key': 't2886649'}, {'title': 'Play'}, item_type = 'music')
    self._addon.end_of_directory()
    
  def get_playback_token(self):
    token = self._rdio_api.get_playback_token()
    self._addon.log_debug("Got playback token " + token)
    return token
    
  def play(self, **params):
    track_id = params['rdio_key']
    rtmp_info = get_rtmp_info(RDIO_DOMAIN, self.get_playback_token(), track_id)
    stream_url = rtmp_info['rtmp']
    for key, value in rtmp_info.items():
      stream_url += '' if key == 'rtmp' else ' %s=%s' % (key, value)

    self._addon.log_debug("Resolved playback URL to " + stream_url)
    self._addon.resolve_url(stream_url)

  def execute(self):
    self._addon.log_debug("Executing Rdio operation: " + str(self._addon.queries))
    handler = getattr(self, self._addon.queries['mode'])
    handler_args = inspect.getargspec(handler)
    if handler_args.keywords and len(handler_args.keywords) > 1:
      handler(**self._addon.queries)
    else:
      handler()


class RdioApi:
  _AUTH_STATE_FILE_NAME = 'rdio-config.json'
  
  def __init__(self, addon):
    self._addon = addon
    self._net = Net()
    self._auth_state = addon.load_data(self._AUTH_STATE_FILE_NAME)
    if not self._auth_state:
      addon.log_debug("Persistent auth state not loaded")
      self._auth_state = {'auth_state': {}}
    else:
      addon.log_debug("Loaded persistent auth state")

    apikey = addon.get_setting('apikey')
    addon.log_debug("Connecting to Rdio with apikey " + apikey)
    self._rdio = Rdio(apikey, addon.get_setting('apisecret'), self._auth_state)
    if not self._rdio.authenticated:
      self._authenticate()
  
    addon.log_notice("Connected successfully to Rdio with apikey " + apikey)
      
  def _authenticate(self):
    self._addon.log_notice("Authenticating to Rdio")
    auth_url = self._rdio.begin_authentication('oob')
    parsed_auth_url = urlparse(auth_url)
    url_base = "%s://%s" % (parsed_auth_url.scheme, parsed_auth_url.netloc)

    self._addon.log_notice("Authorizing OAuth token " + auth_url)
    html = self._net.http_GET(auth_url).content
    login_path = CommonFunctions.parseDOM(html, 'form', {'name': 'login'}, 'action')
    if login_path:
      login_url = url_base + login_path[0]
      username = self._addon.get_setting('username')
      password = self._addon.get_setting('password')
      self._addon.log_notice("Logging in to Rdio as %s using URL %s" % (username, login_url))
      html = self._net.http_POST(login_url, {'username': username, 'password': password}).content

    oauth_token = CommonFunctions.parseDOM(html, 'input', {'name': 'oauth_token'}, 'value')[0]
    verifier = CommonFunctions.parseDOM(html, 'input', {'name': 'verifier'}, 'value')[0]
    self._addon.log_notice("Approving oauth token %s with pin %s" % (oauth_token, verifier))
    self._net.http_POST(auth_url, {'oath_token': oauth_token, 'verifier': verifier, 'approve': ''})
    self._addon.log_notice("Verifying OAuth token on Rdio API with pin " + verifier)
    self._rdio.complete_authentication(verifier)
    self._addon.save_data(self._AUTH_STATE_FILE_NAME, self._auth_state)
    self._addon.log_notice("Successfully authenticated to Rdio")

  def _call(self, method, **args):
    return self._rdio.call(method, **args)
    
  def get_playback_token(self):
    return self._call('getPlaybackToken', domain=RDIO_DOMAIN)


XbmcRdioOperation(addon).execute()
