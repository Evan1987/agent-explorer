
from typing import List, Union

from pydantic import BaseModel
from litellm import completion, acompletion

from .settings import DASHSCOPE_API_KEY, VOLCENGINE_API_KEY
from .types import Message

# 单条消息可以是任意上述形态，也可是一条 Message；整体支持裸字符串/字典/单条/列表
MessageInput = Union[str, dict, Message, List[Union[str, dict, Message]]]

# 原 DashScope（阿里云）配置，保留备用
# DEFAULT_MODEL = "dashscope/qwen3.7-plus"
# BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 火山引擎 Ark 的 Anthropic 兼容端点（与 Claude Code 同一套）
# 模型名去掉 [1m] 上下文窗口标记；anthropic/ 前缀让 litellm 走 Anthropic Messages 协议
DEFAULT_MODEL = "anthropic/deepseek-v4-flash"
BASE_URL = "https://ark.cn-beijing.volces.com/api/coding"
API_KEY = VOLCENGINE_API_KEY


def _to_dict(message: str | dict | Message) -> dict:
    """把任意单条消息归一化成 LiteLLM 期望的字典。"""
    if isinstance(message, Message):
        return message.to_dict()
    if isinstance(message, str):
        return {"role": "user", "content": message}
    if isinstance(message, dict):
        return message
    raise TypeError(f"Unsupported message type: {type(message)!r}")


def _normalize_messages(messages: MessageInput) -> List[dict]:
    """把各种输入形态统一成 ``List[dict]``。

    支持裸字符串、单条 dict、单条 Message，以及它们的列表。
    """
    if isinstance(messages, (str, dict, Message)):
        return [_to_dict(messages)]
    return [_to_dict(m) for m in messages]


def call_llm(
    messages: MessageInput,
    model: str = None,
    output_model: type[BaseModel] = None,
    **kwargs
) -> str:
    messages = _normalize_messages(messages)
    model = model or DEFAULT_MODEL

    response = completion(
        model=model,
        base_url=BASE_URL,
        api_key=API_KEY,
        messages=messages,
        response_format=output_model,
        **kwargs
    )
    return response.choices[0].message.content


async def call_llm_async(
    messages: MessageInput,
    model: str = None,
    output_model: type[BaseModel] = None,
) -> str:
    messages = _normalize_messages(messages)
    model = model or DEFAULT_MODEL

    response = await acompletion(
        model=model,
        base_url=BASE_URL,
        api_key=API_KEY,
        messages=messages,
        response_format=output_model,
    )
    return response.choices[0].message.content
