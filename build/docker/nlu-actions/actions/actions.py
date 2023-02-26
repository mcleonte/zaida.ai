"""
This files contains your custom actions which can be used to run
custom Python code.

See this guide on how to implement these action:
https://rasa.com/docs/rasa/custom-actions
"""

import os
from typing import Any, Text, Dict, List
import logging
from urllib.parse import urlparse
import random

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

import arrow
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from countryinfo import CountryInfo
import pyperclip

import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import wikipedia

logger = logging.getLogger("actions-nlu")
logger.setLevel(logging.DEBUG) #os.environ["LOG_LEVEL"])
logger.addHandler(logging.StreamHandler())

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


class ActionMultimodalPipeline(Action):
  """
  Text processing action.
  Supports any combination of summarization, TTS and outputing to file.
  """

  def name(self) -> Text:
    return "multimodal_pipeline"

  def path_from(self, destination="home"):
    raise NotImplementedError

  def is_valid_url(self, url: str):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

  def get_text_from_copied_source(self):
    source = pyperclip.paste()
    if os.path.isifle(source):
      with open(source, "r") as file:
        return file.read()
    if self.is_valid_url(source):
      soup = BeautifulSoup(requests.get(source, timeout=10), "html.parser")
      return "\n\n".join([
          soup.find("title").get_text(),
          soup.find("body").get_text(),
      ])
    return source

  def summarize(self, text:str)->str:
    logger.debug("Summarizing text...")
    try:
      return self._summarizer(text)
    except AttributeError:
      model = "philschmid/flan-t5-base-samsum"
      self._summarizer = pipeline("summarization",model=model)
      return self._summarizer(text)

  def run(
      self,
      dispatcher: CollectingDispatcher,
      tracker: Tracker,
      domain: Dict[Text, Any],
  ) -> List[Dict[Text, Any]]:


    entities = tracker.latest_message.get("entities",[])
    entities.sort(key=lambda x: x["start"])
    steps = []
    for entity in entities:
      group = int(entity.get("group", 0))
      try:
        steps[group]
      except IndexError:
        while len(steps) <= group:
          steps.append(dict())
      steps[group][entity["entity"]] = entity["value"]

    # default_input_type = "clipboard_link"
    # default_output_type = "speech"

    logger.debug(steps)

    pipe = [[]]

    for step in steps:

      match step.get("input"):
        case "link":
          pipe[-1].append(self.get_text_from_copied_source())
        case "text":
          pipe[-1].append(self.get_text_from_copied_source())
        case "pocket":
          raise NotImplementedError
        case None:
          if not pipe[0]:
            pipe[-1].append(self.get_text_from_copied_source())

      match step.get("action"):
        case "summarize":
          logger.debug("Summarizing the following text(s):\n%s",pipe[-1])
          pipe.append(list(map(self.summarize, pipe[-1])))
        case "transcribe":
          raise NotImplementedError
        case "translate":
          raise NotImplementedError

      match step.get("output"):
        case "read":
          logger.debug("Reading: \n%s",pipe[-1])
          map(dispatcher.utter_message, pipe[-1])
        case "drive":
          raise NotImplementedError
        case "pocket":
          raise NotImplementedError
        case "bookmark":
          raise NotImplementedError
        case None:
          pass
        case _:
          path = self.path_from(step["output"])
          with open(path, "rb") as file:
            file.write(pipe)

    if "output" not in steps[-1]:
      map(dispatcher.utter_message, pipe[-1])
    else:
      dispatcher.utter_message(random.choice(["All done.","Done.","Finished."]))


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
