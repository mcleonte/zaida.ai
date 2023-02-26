# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

import arrow
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from countryinfo import CountryInfo


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


class ActionCountryInfo(Action):

  def name(self) -> Text:
    return "tell_country_info"

  def run(
      self,
      dispatcher: CollectingDispatcher,
      tracker: Tracker,
      domain: Dict[Text, Any],
  ) -> List[Dict[Text, Any]]:

    gpe = next(tracker.get_latest_entity_values("GPE"), None)
    info = next(tracker.get_latest_entity_values("country_info"), None)

    if gpe is None:
      dispatcher.utter_message("Sorry, please specify a country")
    try:
      country = CountryInfo(gpe)
    except:
      dispatcher.utter_message(f"I'm sorry, but {gpe} isn't a country")
    try:
      answer = getattr(country, info)()
      dispatcher.utter_message(
          f"{info} for {gpe} "
          f"{'are' if isinstance(answer,list) and len(answer)>1 else 'is'} "
          f"{answer}")
    except AttributeError:
      dispatcher.utter_message(f"Sorry, I don't know the {info} for {gpe}")
