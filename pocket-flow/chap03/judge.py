
from pocketflow import Node, Flow
from pydantic import BaseModel
from utils import call_llm


class SharedStore(BaseModel):
    task: str
    feedback: str = ""
    draft: str = ""


class Generator(Node):
    def prep(self, shared: SharedStore) -> dict:
        return {"task": shared.task, "feedback": shared.feedback}

    def exec(self, prep_res: dict) -> str:
        prompt = f"""为以下产品写一段描述：{prep_res['task']}"""
        feedback = prep_res['feedback']
        if feedback:
            prompt += f"\n\n上一版被打回了，反馈：{feedback}"
        response = call_llm(prompt, model="anthropic/deepseek-v4-flash")
        return response

    def post(self, shared: SharedStore, prep_res: dict, exec_res: str):
        shared.draft = exec_res


class Judge(Node):
    def prep(self, shared: SharedStore) -> str:
        return shared.draft

    def exec(self, draft: str):
        prompt = f"""给以下这段产品描述的清晰度和说服力打分（1-10分），如果分数 ＞= 7，输出PASS。否则输出 FAIL: <具体反馈> 
产品描述：{draft}"""
        return call_llm(prompt, model="anthropic/deepseek-v4-pro")

    def post(self, shared: SharedStore, prep_res: str, exec_res: str):
        if "PASS" in exec_res:
            return "pass"
        shared.feedback = exec_res
        return "fail"


if __name__ == '__main__':
    generator = Generator()
    judge = Judge()
    generator >> judge
    judge - "fail" >> generator

    flow = Flow(start=generator)
    shared_store = SharedStore(task="降噪耳机")
    flow.run(shared_store)
    print(shared_store.draft)



