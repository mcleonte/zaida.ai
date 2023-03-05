from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from countryinfo import CountryInfo


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
