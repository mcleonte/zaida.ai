# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List
import datetime as dt
import time

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionShowTime(Action):
  """Action for showing time"""

  def name(self) -> Text:
    return "action_show_time"

  def run(
      self,
      dispatcher: CollectingDispatcher,
      tracker: Tracker,
      domain: Dict[Text, Any],
  ) -> List[Dict[Text, Any]]:

    dispatcher.utter_message(
        text=f"It's {time.strftime('%H:%M', time.localtime())}")

    return []
