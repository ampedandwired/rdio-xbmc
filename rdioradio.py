import random


class RdioRadio:

  def __init__(self, addon, rdio_api):
    self._addon = addon
    self._rdio_api = rdio_api

  def next_track(self, base_artist_key, last_artist_key = None, allow_related = True, collection_only = False):
    if not last_artist_key:
      last_artist_key = base_artist_key

    track = None
    while not track or not track['canStream']:
      artist = base_artist_key
      track_count = 20
      if allow_related and not (random.randint(1, 5) == 1):
        artist = random.choice(self._rdio_api.call('getRelatedArtists', artist = last_artist_key, start = 0, count = 10))['key']
        track_count = 10

      tracks = self._rdio_api.call('getTracksForArtist', artist = artist, extras = 'playCount,isInCollection', start = 0, count = track_count)
      if len(tracks) > 0:
        track = random.choice(tracks)

    return track
