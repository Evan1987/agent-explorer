
from enum import Enum

from pydantic import BaseModel


class Role(str, Enum):
    """对话中的角色，对应 OpenAI / DashScope 消息协议。"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """一条对话消息。

    既可作为强类型对象在业务代码中流转，也能通过 :meth:`to_dict`
    转成 LiteLLM 期望的 ``{"role": ..., "content": ...}`` 字典。
    """

    role: Role
    content: str

    # ---- 工厂方法：让构造消息更语义化 ----
    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> "Message":
        return cls(role=Role.ASSISTANT, content=content)

    # ---- 与 LiteLLM 协议互转 ----
    def to_dict(self) -> dict:
        return {"role": self.role.value, "content": self.content}
