import random
from collections import deque


class RdioRadio:

  _RETURN_TO_BASE_ARTIST_FREQUENCY = 5
  _NO_REPEAT_TRACK_COUNT = 25
  _NUM_TOP_TRACKS_TO_CHOOSE_FROM = 20

  _RADIO_STATE_FILE_NAME = 'rdio-radio-state.json'
  _INITIAL_STATE = {'played_tracks': deque()}

  def __init__(self, addon, rdio_api):
    self._addon = addon
    self._rdio_api = rdio_api
    self._state = addon.load_data(self._RADIO_STATE_FILE_NAME)
    if not self._state:
      self._state = self._INITIAL_STATE


  def next_track(self, base_artist, last_artist = None, user = None):
    if not last_artist:
      self._state = self._INITIAL_STATE

    track = None
    artist_blacklist = []
    while not track or not track['canStream']:
      artist = self._choose_artist(base_artist, last_artist, user, artist_blacklist)
      if artist:
        track = self._choose_track(artist, user)
        if not track:
          artist_blacklist.append(artist)
      else:
        # TODO: Should do something clever here, but what? For now reset to initial state.
        self._state = self._INITIAL_STATE

    self._record_played_track(track['key'])
    self._save_state()
    return track


  def _choose_artist(self, base_artist, last_artist, user, artist_blacklist = []):
    if not last_artist or random.randint(1, self._RETURN_TO_BASE_ARTIST_FREQUENCY) == 1:
      return base_artist

    chosen_artist = None
    candidate_artist_keys = None

    candidate_artist_keys = self._cached_value('related_artists_' + last_artist, lambda: [artist['key'] for artist in self._rdio_api.call('getRelatedArtists', artist = last_artist)])
    if user:
      collection_artist_keys = self._cached_value('artists_in_collection_' + user, lambda: [artist['artistKey'] for artist in self._rdio_api.call('getArtistsInCollection', user = user)])
      candidate_artist_keys = list((set(candidate_artist_keys) & set(collection_artist_keys)) - set(artist_blacklist))

    if candidate_artist_keys:
      chosen_artist = random.choice(candidate_artist_keys)

    return chosen_artist or base_artist


  def _choose_track(self, artist, user):
    tracks = None
    if user:
      tracks = self._cached_value('artist_tracks_in_collection_%s_%s' % (artist, user), lambda: self._rdio_api.call('getTracksForArtistInCollection', artist = artist, user = user))
    else:
      tracks = self._cached_value('artist_tracks_%s' % artist, self._rdio_api.call('getTracksForArtist', artist = artist, extras = 'playCount,isInCollection', start = 0, count = self._NUM_TOP_TRACKS_TO_CHOOSE_FROM))

    chosen_track = None
    if tracks:
      played_tracks = self._state['played_tracks']
      track_keys = [track['key'] for track in tracks]
      candidate_track_keys = list(set(track_keys) - set(played_tracks))
      if candidate_track_keys:
        track_key = random.choice(candidate_track_keys)
        chosen_track = next(track for track in tracks if track['key'] == track_key)

    return chosen_track


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

  def _record_played_track(self, track_key):
    played_tracks = self._state['played_tracks']
    played_tracks.append(track_key)
    if len(played_tracks) > self._NO_REPEAT_TRACK_COUNT:
      played_tracks.popleft()
