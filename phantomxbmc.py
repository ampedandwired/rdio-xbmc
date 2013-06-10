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

from subprocess import Popen, PIPE
import os
import re
import json

class PhantomXbmc:

  _CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
  _PHANTOM_XBMC_SCRIPT = os.path.join(_CURRENT_DIR, 'phantom.js')

  def __init__(self, addon):
    self._addon = addon

  def phantom(self, script_path, *args):
    command_args = ['phantomjs', _PHANTOM_XBMC_SCRIPT, script_path] + list(args)
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
