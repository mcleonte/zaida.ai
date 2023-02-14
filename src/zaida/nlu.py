"""
Natural Languange Understanding module with dockerized Rasa
"""

import requests
import json
from pprint import pprint


class NLUserver:
  """
  Interface class for communicating with Rasa server.
  """

  def __init__(
      self,
      uri=None,
      protocol="http",
      hostname="localhost",
      port=5005,
  ):

    if uri is None:
      uri = f"{protocol}://{hostname}:{port}"
    uri += "/webhooks/rest/webhook"
    self.uri = uri

  def interpret(self, text):
    resp = requests.post(
        self.uri,
        data=json.dumps({"message": text}),
        timeout=None,
    )
    if not resp.ok:
      return f"Sorry, Rasa server returned status code {resp.status_code}"
    try:
      return resp.json()[0]["text"]
    except IndexError as ie:
      raise SyntaxError(f"Rasa returned empty response: {resp.json()}") from ie


def main(text=None):
  nlu = NLUserver()
  text = text or "What time is it in Amsterdam?"
  print(nlu.interpret(text))


if __name__ == "__main__":
  import sys
  main(sys.argv[-1])
