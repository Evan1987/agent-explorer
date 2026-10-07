
import yaml
from pocketflow import Node, Flow
from utils import call_llm
from typing import List


class ExtractFacts(Node):
    def prep(self, shared: dict) -> str:
        return shared["article"]
    def exec(self, prep_res: str) -> List[str]:
        prompt = f"""从这篇文章中提取事实，并以YAML格式输出。
{prep_res}

```yaml
facts:
    - 事实1
    - 事实2
    ...
```
"""
        response = call_llm(prompt)
        result = yaml.safe_load(response)
        assert isinstance(result["facts"], list)
        return result["facts"]
    def post(self, shared: dict, prep_res: str, exec_res: List[str]) -> None:
        shared["facts"] = exec_res


class FindHook(Node):
    def prep(self, shared: dict) -> List[str]:
        return shared["facts"]
    def exec(self, facts: List[str]) -> str:
        facts_str = "\n".join(f"- {f}" for f in facts)
        prompt = f"""这些事实里哪个最反直觉?哪个能让人停下看？
{facts_str}
```yaml
hook: <用一句话写出那个令人意外的角度>
```
"""
        response = call_llm(prompt)
        result = yaml.safe_load(response)
        assert result["hook"] is not None
        return result["hook"]
    def post(self, shared: dict, facts: List[str], exec_res: str) -> None:
        shared["hook"] = exec_res


class WritePost(Node):
    def prep(self, shared: dict) -> tuple[List[str], str]:
        return shared["facts"], shared["hook"]
    def exec(self, inputs: tuple[List[str], str]) -> str:
        facts, hook = inputs
        facts_str = "\n".join(f"- {f}" for f in facts)
        prompt = f"""用这个切入角度和事实写一条爆款帖子。暴论风格，挑衅、对抗、Grok 级别的阴阳怪气。最大化互动能量。让人气到忍不住评论
切入角度：{hook}
事实：{facts_str}
只输出帖子内容:
"""
        response = call_llm(prompt)
        return response
    def post(self, shared: dict, hook: str, exec_res: str) -> None:
        shared["post"] = exec_res


if __name__ == '__main__':
    extract = ExtractFacts()
    hook = FindHook()
    write = WritePost()
    extract >> hook >> write  # workflow的精髓

    flow = Flow(start=extract)
    shared_store = {"article": "文章内容"}
    flow.run(shared_store)
    print(shared_store["post"])

