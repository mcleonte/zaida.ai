"""
Natural Languange Understanding module with dockerized Rasa
"""

import requests
import json


class NLU:
  """
  Interface class for communicatind with Rasa server container.
  """

  def __init__(
      self,
      uri=None,
      protocol="http",
      hostname="localhost",
      port=5005,
  ):

    if uri is None:
      uri = f"{protocol}://{hostname}:{port}/webhooks/rest/webhook"
    self.uri = uri

  def interpret(self, text):
    resp = requests.post(
        self.uri,
        data=json.dumps({"message": text}),
        timeout=None,
    )
    if resp.ok:
      return resp.json()[0]["text"]
    else:
      return f"Sorry, Rasa server returned status code {resp.status_code}"


def main():
  nlu = NLU()
  print(nlu.interpret("What time is it in Amsterdam?"))


if __name__ == "__main__":
  main()
