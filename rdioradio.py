import random


class RdioRadio:

  def __init__(self, addon, rdio_api):
    self._addon = addon
    self._rdio_api = rdio_api


  def next_track(self, base_artist, last_artist = None, allow_related = True, user = None):
    track = None
    while not track or not track['canStream']:
      artist = self._choose_artist(base_artist, last_artist, user)
      track = self._choose_track(artist, user)

    return track


  def _choose_artist(self, base_artist, last_artist, user):
    if not last_artist:
      last_artist = base_artist

    if random.randint(1, 5) == 1:
      return base_artist

    candidate_artist_keys = None

    if user:
      related_artists = self._rdio_api.call('getRelatedArtists', artist = last_artist)
      related_artist_keys = [artist['key'] for artist in related_artists]
      collection_artists = self._rdio_api.call('getArtistsInCollection', user = user)
      collection_artist_keys = [artist['artistKey'] for artist in collection_artists]
      candidate_artist_keys = list(set(related_artist_keys) & set(collection_artist_keys))
      self._addon.log_notice("************************ " + str(collection_artist_keys))
      self._addon.log_notice("************************ " + str(related_artist_keys))
      self._addon.log_notice("************************ " + str(candidate_artist_keys))
    else:
      related_artists = self._rdio_api.call('getRelatedArtists', artist = last_artist, start = 0, count = 10)
      candidate_artist_keys = [artist['key'] for artist in related_artists]

    if candidate_artist_keys:
      artist = random.choice(candidate_artist_keys)

    if not artist:
      artist = base_artist

    return artist

  def _choose_track(self, artist, user):
    tracks = None
    if user:
      tracks = self._rdio_api.call('getTracksForArtistInCollection', artist = artist, user = user)
    else:
      tracks = self._rdio_api.call('getTracksForArtist', artist = artist, extras = 'playCount,isInCollection', start = 0, count = 15)

    track = None
    if tracks:
      track = random.choice(tracks)

    return track
