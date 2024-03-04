"""
Websocket hub
"""

import os
import asyncio
import logging

import websockets

connected = {}

# Predefined routing map
routing_map = {
    "client": "stt",
    "stt": "langchain",
    "langchain": "tts",
    # "stt": "tts",
    "tts": "client",
}

logging.basicConfig(
    format="%(asctime)s | %(message)s",
    level=os.environ.get("LOG_LEVEL"),
)
logger = logging.getLogger("zaida.wshub")


async def register(websocket, client_id):
  connected[client_id] = websocket
  logger.info("Registered %s websocket connection", client_id)


async def unregister(client_id):
  connected.pop(client_id, None)
  logger.info("Unregistered %s websocket connection", client_id)


async def route_message(sender_id, message):
  # Determine the destination client
  target_id = routing_map.get(sender_id)

  if target_id and target_id in connected:
    # Send the message to the target client
    logger.info(
        "Sending from %s to %s payload of length %s",
        sender_id,
        target_id,
        len(message),
    )
    await connected[target_id].send(message)
  else:
    print(f"Error: No route defined for client {sender_id} "
          f"or target client {target_id} not connected.")


async def websocket_handler(websocket, path):  # pylint: disable=unused-argument
  client_id = None
  try:
    # The first message from the client should be its identifier
    client_id = await websocket.recv()
    await register(websocket, client_id)

    async for message in websocket:
      await route_message(client_id, message)
  finally:
    if client_id:
      await unregister(client_id)


start_server = websockets.serve(
    websocket_handler,
    "0.0.0.0",
    os.environ["PORT_1"],
    max_size=10**9,
)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
