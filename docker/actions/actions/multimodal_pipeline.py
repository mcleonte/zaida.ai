from typing import Any, Text, Dict, List, Optional

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.endpoint import logger, instruct

import os
from urllib.parse import urlparse
import random

import aiohttp
from bs4 import BeautifulSoup
from transformers import pipeline


class Pipe:
  """
  Utility class for handling intermediary outputs between pipeline steps.
  """

  def __init__(self):
    self._pipe = []
    self.curr_step = None
    self.prev_step = None

  def add(self, partial:Any):
    self._pipe[-1].append(partial)

  def new_step(self, step:Optional[List]=None):
    if step is None:
      step = []
    self._pipe.append(step)
    self.prev_step, self.curr_step = self.curr_step, self._pipe[-1]

  def empty(self):
    return bool(self._pipe)




class ActionMultimodalPipeline(Action):
  """
  Text processing action.
  Supports any combination of summarization, TTS and outputing to file.
  """

  http_session = aiohttp.ClientSession()

  _summarizer = pipeline("summarization",
                         model="philschmid/flan-t5-base-samsum",
                         device=0 if os.environ["DEVICE"]=="gpu" else -1,)

  def name(self) -> Text:
    return "multimodal_pipeline"

  def path_from(self, destination="home"):
    raise NotImplementedError

  def is_valid_url(self, url: str):
    parsed = urlparse(url)
    if parsed.netloc:
      return parsed
    return False

  async def get_html(self, url):
    async with self.http_session.get(url) as resp:
      html = await resp.text()
    await self.http_session.close()
    return html

  def parse_html(self, html, parsed_url):
    soup = BeautifulSoup(html, "html.parser")
    match parsed_url.netloc:
      case "linkedin.com":
        to_find = [("div", {"class":"core-rail"})]
      case _:
        to_find = [("title",), ("body",)]

    return "\n\n".join([soup.find(*args).get_text().strip() for args in to_find])


  async def get_text_from_clipboard(self):
    logger.debug("Calling instruct('get_clipoard')")
    clip = await instruct("get_clipboard")
    logger.debug("Instruct completed, received: %s", clip)

    if os.path.isfile(clip):
      with open(clip, "r") as file:
        return file.read()

    if (parsed_url := self.is_valid_url(clip)):
      html = await self.get_html(clip)
      return self.parse_html(html, parsed_url)

    return clip

  def summarize(self, text:str)->str:
    logger.debug("Summarizing text...")
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

    pipe = Pipe()

    for step in steps:
      pipe.new_step()

      match step.get("input"):
        case "link":
          pipe.add(await self.get_text_from_clipboard())
        case "text":
          pipe.add(await self.get_text_from_clipboard())
        case "pocket":
          raise NotImplementedError
        case None:
          if pipe.empty():
            pipe.add(await self.get_text_from_clipboard())

      match step.get("action"):
        case "summarize":
          logger.debug("Summarizing the following text(s):\n%s",pipe[-1])
          pipe.new_step([x["summary_text"] for x in
                         list(map(self.summarize, pipe.curr_step))[0]])
        case "transcribe":
          raise NotImplementedError
        case "translate":
          raise NotImplementedError

      logger.debug(pipe.curr_step)

      match step.get("output"):
        case "read":
          logger.debug("Reading: \n%s",pipe.curr_step)
          map(dispatcher.utter_message, pipe.curr_step)
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
            file.write(pipe.curr_step)

    if "output" not in steps[-1]:
      for out in pipe.curr_step:
        logger.debug("Uttering message: %s",out)
        dispatcher.utter_message(out)
    else:
      dispatcher.utter_message(random.choice(["All done.","Done.","Finished."]))

