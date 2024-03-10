"""
https://python.langchain.com/docs/integrations/chat/llama2_chat
"""

import os
import logging
import asyncio

import websockets

from huggingface_hub import hf_hub_download
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks import StdOutCallbackHandler
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_community.llms import LlamaCpp  # HuggingFaceTextGenInference
from langchain_experimental.chat_models import Llama2Chat

prompt = ChatPromptTemplate.from_messages([
    ("system", os.environ["SYSTEM_PROMPT"]),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{text}"),
])

memory = ConversationBufferMemory(
    memory_key="history",
    return_messages=True,
)
# Callbacks support token-wise streaming
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
models = {
    "llama2chat": {
        "repo": "amanpreetsingh459/llama-2-7b-chat_q4_quantized_cpp",
        "file": "ggml-model-q4_0.bin",
    },
    "zephyr": {
        "repo": "TheBloke/zephyr-7B-beta-GGUF",
        "file": "zephyr-7b-beta.Q5_K_M.gguf",
    },
}
model_path = hf_hub_download(
    repo_id=os.environ.get(
        "LLM_REPO",
        models["llama2chat"]["repo"],
    ),
    filename=os.environ.get(
        "LLM_FILE",
        models["llama2chat"]["file"],
    ),
)
llm = LlamaCpp(
    model_path=model_path,
    streaming=True,
    # Change this value based on your model and your GPU VRAM pool.
    n_gpu_layers=os.environ.get("N_GPU_LAYERS", 20),
    n_ctx=2048,
    # Should be between 1 and n_ctx, consider the amount of VRAM in your GPU.
    n_batch=os.environ.get("N_BATCH", 128),  # 512
    callback_manager=callback_manager,
    # Verbose is required to pass to the callback manager
    verbose=True,
)
model = Llama2Chat(llm=llm)

chain = LLMChain(
    llm=model,
    prompt=prompt,
    memory=memory,
)

logging.basicConfig(
    level=os.environ.get("LOGLEVEL", logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

handler = StdOutCallbackHandler()


async def process(text):
  logging.info("Received message: %s", text)
  async for token in chain.astream_events(
      text,
      version="v1",
      callbacks=[handler],
  ):
    if token["event"] == "on_chat_model_stream":
      logging.info("token: %s", token["data"]["chunk"])
      yield token["data"]["chunk"]


async def main():
  async with websockets.connect(os.environ["WSHUB_URI"]) as ws:
    await ws.send("langchain")
    while True:
      data = await ws.recv()
      async for result in process(data):
        await ws.send(result)


asyncio.run(main())
