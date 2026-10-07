
import os
from pathlib import Path
from dotenv import load_dotenv

# 以本文件所在目录为基准定位项目根的 .env，避免工作目录不同导致读取失败
_BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BASE_DIR / ".env")

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
VOLCENGINE_API_KEY = os.getenv("VOLCENGINE_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

