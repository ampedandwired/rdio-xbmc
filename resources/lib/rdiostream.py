import httplib
from pyamf.remoting.client import RemotingService
from urlparse import urlparse

# URL hosting the Flash player
FLASH_PLAYER_URL = 'http://www.rdio.com/api/swf'

# API endpoint for AMF
AMF_ENDPOINT = 'http://www.rdio.com/api/1/amf/'

def resolve_url(url):
    '''Recursively resolve the given URL, following 3xx redirects. Returns
       the final URL that did not result in a redirect.'''

    url = FLASH_PLAYER_URL
    while True:
        pr = urlparse(url)

        hc = httplib.HTTPConnection(pr.hostname)
        hc.request('GET', pr.path)
        hr = hc.getresponse()

        
        if hr.status / 100 == 3:
            url = hr.getheader('location')
        else:
            return url


def get_rtmp_info(domain, token, track, flash_url=None):
    '''Return a dictionary containing rtmp playback info; raises an Exception on failure.'''

    if not flash_url:
        flash_url = resolve_url(FLASH_PLAYER_URL)

    svc = RemotingService(AMF_ENDPOINT, referer=flash_url)
    svc.addHeader('Auth', chr(5))
    rdio_svc = svc.getService('rdio')

    pi = rdio_svc.getPlaybackInfo({
        'domain': domain,
        'playbackToken': token,
        'manualPlay': False,
        'playerName': 'api_544189',
        'type': 'flash',
        'key': track})
    if not pi:
        raise Exception, 'Failed to get playback info'
        
    return {
      'rtmp': 'rtmpe://%s:1935%s' % (pi['streamHost'], pi['streamApp']),
      'app': pi['streamApp'][1:],
      'playpath': 'mp3:%s' % pi['surl'],
      'swfVfy': flash_url,
      'pageUrl': 'http://%s/' % domain
    }
