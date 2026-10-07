
# 必须最先导入 settings，触发 load_dotenv()，
# 保证后续 model/tool 中的 os.getenv 能读到 .env
from . import settings  # noqa: F401
from .types import Message, Role
from .model import call_llm, call_llm_async
from .tool import search_web_brave

__all__ = [
    "Message",
    "Role",
    "call_llm",
    "call_llm_async",
    "search_web_brave",
]
