# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List

import arrow
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionTellTime(Action):
  """Action for showing time"""

  def name(self) -> Text:
    return "tell_time"

  def time_of(self, place: str):
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(place)
    timezone = TimezoneFinder().timezone_at(
        lng=location.longitude,
        lat=location.latitude,
    )
    return arrow.utcnow().to(timezone).format("HH:mm")

  def run(
      self,
      dispatcher: CollectingDispatcher,
      tracker: Tracker,
      domain: Dict[Text, Any],
  ) -> List[Dict[Text, Any]]:

    place = next(tracker.get_latest_entity_values("GPE"), None)

    if place is None:
      msg = f"It's {arrow.now().format('HH:mm')}."
    elif (time := self.time_of(place)) is None:
      msg = f"I don't know where {place} is. Is it spelled correctly?"
    else:
      msg = f"It's {time} in {place} now."

    dispatcher.utter_message(msg)
    return []
