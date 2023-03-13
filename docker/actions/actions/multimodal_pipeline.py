from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.endpoint import logger, instruct

import os
from urllib.parse import urlparse
import random

import aiohttp
from bs4 import BeautifulSoup
from transformers import pipeline


class ActionMultimodalPipeline(Action):
  """
  Text processing action.
  Supports any combination of summarization, TTS and outputing to file.
  """

  http_session = aiohttp.ClientSession()

  def name(self) -> Text:
    return "multimodal_pipeline"

  def path_from(self, destination="home"):
    raise NotImplementedError

  def is_valid_url(self, url: str):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

  async def get_html(self, url):
    async with self.http_session.get(url) as resp:
      text = await resp.text()
    await self.http_session.close()
    return text


  async def get_text_from_clipboard(self):
    logger.debug("Calling instruct('get_clipoard')")
    clip = await instruct("get_clipboard")
    logger.debug("Instruct completed, received: %s", clip)

    if os.path.isfile(clip):
      with open(clip, "r") as file:
        return file.read()

    if self.is_valid_url(clip):
      resp = await self.get_html(clip)
      logger.debug(resp)
      soup = BeautifulSoup(resp, "html.parser")
      return "\n\n".join([
          soup.find("title").get_text(),
          soup.find("body").get_text(),
      ])

    return clip

  def summarize(self, text:str)->str:
    logger.debug("Summarizing text...")
    try:
      return self._summarizer(text,max_length=len(text)//5)
    except AttributeError:
      model = "philschmid/flan-t5-base-samsum"
      self._summarizer = pipeline("summarization",model=model)
      return self._summarizer(text,max_length=len(text)//5)

  async def run(
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
          steps.append({})
      steps[group][entity["entity"]] = entity["value"]

    # default_input_type = "clipboard_link"
    # default_output_type = "speech"

    logger.debug(steps)

    pipe = [[]]

    for step in steps:

      match step.get("input"):
        case "link":
          pipe[-1].append(await self.get_text_from_clipboard())
        case "text":
          pipe[-1].append(await self.get_text_from_clipboard())
        case "pocket":
          raise NotImplementedError
        case None:
          if not pipe[0]:
            pipe[-1].append(await self.get_text_from_clipboard())

      match step.get("action"):
        case "summarize":
          logger.debug("Summarizing the following text(s):\n%s",pipe[-1])
          pipe.append([x["summary_text"] for x in list(map(self.summarize,pipe[-1]))[0]])
        case "transcribe":
          raise NotImplementedError
        case "translate":
          raise NotImplementedError

      logger.debug(pipe[-1])

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
      for out in pipe[-1]:
        logger.debug("Uttering message: %s",out)
        dispatcher.utter_message(out)
    else:
      dispatcher.utter_message(random.choice(["All done.","Done.","Finished."]))

