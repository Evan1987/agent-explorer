
import yaml
from pocketflow import Node, Flow
from pydantic import BaseModel
from utils import call_llm
from typing import List


class ShareStore(BaseModel):
    thoughts: List[str] = []
    question: str
    result: str = None


class Thinker(Node):

    def prep(self, shared: ShareStore) -> dict:
        return {"thoughts": "\n".join(shared.thoughts), "question": shared.question}
    def exec(self, prep_res: dict) -> dict:
        question = prep_res["question"]
        thoughts = prep_res["thoughts"]
        prompt = f"""一步步解决这个问题。
如果需要继续思考，请返回:
```yaml
action: think
thought: <你的下一步思考>
```

如果得到了最终答案，请返回:
```yaml
action: answer
result: <最终答案>
```

问题：{question}
之前的思考：{thoughts}
"""
        response = call_llm(prompt)
        result = yaml.safe_load(response)
        assert result["action"] in ["think", "answer"]
        return result
    def post(self, shared: ShareStore, prep_res: dict, exec_res: dict) -> str:
        action = exec_res["action"]
        if action == "think":
            shared.thoughts.append(exec_res["thought"])
        else:
            shared.result = exec_res["result"]
        return action


if __name__ == '__main__':
    thinker = Thinker()
    thinker - "think" >> thinker
    flow = Flow(thinker)
    question = (
        "你的APP有2000个用户，数据分析显示，1200人用移动端，800人用网页端，500人用API，"
        "400人同时用移动端和网页端，200人同时用移动端和API，150人同时用网页端和API，100人三个都用。"
        "有多少用户从未使用过任何功能？"
    )
    shared = ShareStore(question=question)
    flow.run(shared)
    print(f"最终答案: {shared.result}")
