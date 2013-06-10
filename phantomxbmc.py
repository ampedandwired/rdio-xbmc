from subprocess import Popen, PIPE
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
