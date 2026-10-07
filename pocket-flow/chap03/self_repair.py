
import subprocess
import logging
from pocketflow.node import Node, Flow
from utils import call_llm
from pydantic import BaseModel, Field
from typing import Optional

class Attempt(BaseModel):
    code: str
    error: str


class SharedStore(BaseModel):
    task: str
    attempts: list[Attempt] = Field(default_factory=list)
    chart: Optional[str] = None

    def add_attempt(self, code: str, error: str):
        self.attempts.append(Attempt(code=code, error=error))


class WriteChart(Node):
    def prep(self, shared: SharedStore):
        logging.info(f"执行第 {len(shared.attempts) + 1} 次写作")
        return {"task": shared.task, "attempts": shared.attempts}
    def exec(self, prep_res: dict) -> str:
        history = []
        for i, attempt in enumerate(prep_res["attempts"]):
            history.append(f"""第 {i + 1} 次尝试:
```mermaid
{attempt.code}
```
错误信息: {attempt.error}
""")
        history = "\n\n".join(history)
        prompt = f"""为以下内容写一个mermaid图：{prep_res["task"]}
只输出```mermaid```代码块中的mermaid代码
"""
        if history:
            prompt += f"\n\n历史尝试：\n{history}\n\n修复语法错误"
        response = call_llm(prompt)
        code = response.split("```mermaid")[1].split("```")[0].strip()
        logging.info(f"写作成功，mermaid代码如下：\n{code}")
        return code
    def post(self, shared: SharedStore, prep_res: dict, exec_res: str) -> None:
        shared.chart = exec_res


class CompileChart(Node):
    def prep(self, shared: SharedStore) -> str:
        assert shared.chart is not None, "chart is None"
        return shared.chart

    def exec(self, code: str) -> dict:
        mmd_path = "chart.mmd"
        svg_path = "chart.svg"
        with open(mmd_path, "w") as f:
            f.write(code)
        result = subprocess.run(
            ["npx", "@mermaid-js/mermaid-cli", "-i", mmd_path, "-o", svg_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            logging.error(f"编译失败，错误信息：{result.stderr}")
            return {"success": False, "error": result.stderr}
        return {"success": True}

    def post(self, shared: SharedStore, code: str, exec_res: dict) -> str:
        if exec_res["success"]:
            return "done"
        shared.add_attempt(code, exec_res["error"])
        return "fix"


if __name__ == '__main__':
    writer = WriteChart()
    compiler = CompileChart()
    writer >> compiler
    compiler - "fix" >> writer
    shared_store = SharedStore(
        task="绘制一个错误处理流程图，Request -> Parse JSON -> "
             "Validate(检查必填字段) -> Process -> DB[Insert into orders(id, total)] -> Response[返回201: {order_id}]."
             "用一个名为 'Happy Path(v2)'的subgraph 把 validate、process和db包起来")
    flow = Flow(start=writer)
    flow.run(shared_store)
    print(shared_store.chart)
