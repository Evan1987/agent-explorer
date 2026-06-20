
import os
from pydantic import BaseModel
from litellm import completion, acompletion
from typing import List


def _normalize_messages(messages: List[dict] | str | dict) -> List[dict]:
    if isinstance(messages, str):
        messages = {"role": "user", "content": messages}
    if isinstance(messages, dict):
        messages = [messages]
    return messages


def call_llm(messages: List[dict] | str | dict, model: str = None, output_model: type[BaseModel] = None) -> str:
    messages = _normalize_messages(messages)
    model = model or "dashscope/qwen3.6-flash-2026-04-16"

    response = completion(
        model=model,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        messages=messages,
        response_format=output_model
    )
    return response.choices[0].message.content


async def call_llm_async(messages: List[dict] | str | dict, model: str = None, output_model: type[BaseModel] = None) -> str:
    messages = _normalize_messages(messages)
    model = model or "dashscope/qwen3.6-flash-2026-04-16"

    response = await acompletion(
        model=model,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        messages=messages,
        response_format=output_model
    )
    return response.choices[0].message.content
