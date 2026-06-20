import yaml
from pocketflow import Node
from utils import call_llm


class ParseResume(Node):
    def prep(self, shared: dict) -> str:
        return shared["resume_text"]

    def exec(self, resume_text: str) -> dict:
        prompt = f"""从这份简历中提取信息，并以YAML格式输出。
{resume_text}

```yaml
name: 全名
email: 邮箱
phone: 手机号
age: 年龄
skills: 技能
    - 技能1
    - 技能2
    ...
```
"""
        response = call_llm(prompt)
        yaml_content = response.split("```yaml")[1].split("```")[0].strip()
        result = yaml.safe_load(yaml_content)
        assert "name" in result
        assert "email" in result
        assert isinstance(result["skills"], list)
        return result

    def post(self, shared: dict, resume_text: str, exec_res: dict) -> None:
        shared["parsed"] = exec_res


resume = """张三，zhangsan@example.com，资深python开发者，5年经验。1990年出生
熟练掌握 python、fastapi、docker、aws、mysql等
"""

if __name__ == '__main__':
    parse_resume = ParseResume(max_retries=3)
    shared_store = {"resume_text": resume}
    parse_resume.run(shared_store)
    print(yaml.safe_dump(shared_store["parsed"], allow_unicode=True))

