import random


class RdioRadio:

  _RADIO_STATE_FILE_NAME = 'rdio-radio-state.json'

  def __init__(self, addon, rdio_api):
    self._addon = addon
    self._rdio_api = rdio_api
    self._state = addon.load_data(self._RADIO_STATE_FILE_NAME)
    if not self._state:
      self._state = {}


  def next_track(self, base_artist, last_artist = None, user = None):
    if not last_artist:
      self._state = {}

    track = None
    while not track or not track['canStream']:
      artist = self._choose_artist(base_artist, last_artist, user)
      track = self._choose_track(artist, user)

    self._save_state()
    return track


  def _choose_artist(self, base_artist, last_artist, user):
    if not last_artist or random.randint(1, 5) == 1:
      return base_artist

    chosen_artist = None
    candidate_artist_keys = None

    candidate_artist_keys = self._cached_value('related_artists_' + last_artist, lambda: [artist['key'] for artist in self._rdio_api.call('getRelatedArtists', artist = last_artist)])
    if user:
      collection_artist_keys = self._cached_value('artists_in_collection_' + user, lambda: [artist['artistKey'] for artist in self._rdio_api.call('getArtistsInCollection', user = user)])
      candidate_artist_keys = list(set(candidate_artist_keys) & set(collection_artist_keys))

    if candidate_artist_keys:
      chosen_artist = random.choice(candidate_artist_keys)

    if not chosen_artist:
      chosen_artist = base_artist

    return chosen_artist


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


  def _save_state(self):
    self._addon.save_data(self._RADIO_STATE_FILE_NAME, self._state)


  def _cached_value(self, key, fn):
    value = None
    if key in self._state:
      value = self._state[key]
    else:
       value = fn()
       self._state[key] = value

    return value
