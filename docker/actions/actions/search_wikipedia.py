from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.endpoint import logger

import wikipedia


class ActionSearchWikipedia(Action):
  "search_wikipedia action class"

  def name(self) -> Text:
    return "search_wikipedia"

  def run(
    self,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    domain: Dict[Text, Any],
  ) -> List[Dict[Text, Any]]:

    term = next(tracker.get_latest_entity_values("wiki_search_term"), None)
    logger.info("Wikipedia search term detected: %s", term)
    dispatcher.utter_message(wikipedia.summary(term, sentences=4))
