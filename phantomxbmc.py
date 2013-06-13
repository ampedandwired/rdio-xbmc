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

import os
import re
import json
import urllib
from subprocess import Popen, PIPE
from distutils.spawn import find_executable
from urllib import urlretrieve

class PhantomXbmc:

  _PHANTOMJS_VERSION = '1.9.1'
  _CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
  _PHANTOM_XBMC_SCRIPT = os.path.join(_CURRENT_DIR, 'phantomxbmc.js')
  _PHANTOM_DOWNLOAD_URL = ""

  def __init__(self, addon):
    self._addon = addon

  def phantom(self, script_path, *args):
    command_args = [self._phantom_binary(), self._PHANTOM_XBMC_SCRIPT, script_path] + list(args)
    self._addon.log_debug("Executing phantom with args " + str(command_args))

    phantom_process = Popen(command_args, stdout = PIPE, stderr = PIPE)
    stdout, stderr = phantom_process.communicate()

    self._addon.log_debug("Phantomjs complete")
    self._addon.log_debug(stdout)
    self._addon.log_notice(stderr)

    result = None
    for output_line in stdout.split("\n"):
      match = re.match('PhantomXbmc Result: (.*)', output_line)
      if match:
        result_string = match.group(1)
        result = json.loads(result_string)

    self._addon.log_debug("Phantom result: " + str(result))
    return result


  def _phantom_binary(self):
    if find_executable('phantomjs'):
      self._addon.log_debug("Using phantomjs found in path")
      return 'phantomjs'

    self._addon.log_error("Phantomjs executable not found - please download phantomjs and add it to your system PATH")
    raise PhantomXbmcException("Please download phantomjs and add it to your system PATH")

    # TODO - download phantomjs for the user...

    # phantomjs_executable_path = self._phantomjs_executable_path()

    # if not os.path.isfile(phantomjs_executable_path):
    #   phantomjs_gzip_path = phantomjs_executable_path + '.gz'
    #   self._download_phantom_binary(phantomjs_gzip_path)
    #   self._unzip_file(phantomjs_gzip_path, phantomjs_executable_path)

    # self._addon.log_debug("Using downloaded phantomjs: %s" % phantomjs_executable_path)
    # return phantomjs_executable_path


  def _phantomjs_executable_path(self):
    profile_path = self._addon.get_profile()
    try:
        os.makedirs(profile_path)
    except:
        pass

    phantomjs_executable_name = self._phantom_executable_for_current_platform()
    return os.path.join(profile_path, phantomjs_executable_name)

  def _phantom_executable_for_current_platform(self):
    return 'phantomjs-%s-linux-x86_64' % self._PHANTOMJS_VERSION


  def _download_phantom_binary(self, dest):
    filename = os.path.basename(dest)
    url = "%s/%s" % (self._PHANTOM_DOWNLOAD_URL, filename)
    self._addon.log_debug("Downloading %s to %s" % (url, dest))
    urllib.urlretrieve(url, dest)
    self._addon.log_debug("Download of %s complete" % url)


  def _unzip_file(self, zip_file_path, dest_file_path):
    chunksize = 4096
    zip_file = gzip.GzipFile(zip_file_path, 'rb')
    output_file = open(dest_file_path, 'wb')
    buffer = zip_file.read(chunksize)
    while buffer:
      output_file.write(buffer)
      buffer = zip_file.read(chunksize)

class PhantomXbmcException(Exception):
  pass
