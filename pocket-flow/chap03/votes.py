
import yaml
from pocketflow import BatchNode, Node, Flow
from pydantic import BaseModel
from collections import Counter
from utils import call_llm


class SharedStore(BaseModel):
    review: str
    votes: list[str] = []
    result: str = ""


class ClassifyMulti(BatchNode):
    def prep(self, shared: SharedStore) -> list[str]:
        return [shared.review] * 5

    def exec(self, review: str) -> str:
        prompt = f"这条餐厅评论是正面还是负面的？\n\n{review}\n\n如果这条评论是正面，输出 POSITIVE，否则输出 NEGATIVE。"
        return call_llm(prompt, temperature=1.5)

    def post(self, shared: SharedStore, prep_res: str, exec_res: list[str]):
        shared.votes = exec_res


class PickConsensus(Node):

    def prep(self, shared: SharedStore) -> list[str]:
        return shared.votes

    def exec(self, votes: list[str]) -> str:
        counts = Counter(votes)
        return counts.most_common(1)[0][0]

    def post(self, shared: SharedStore, prep_res: list[str], exec_res: str):
        shared.result = exec_res


if __name__ == '__main__':
    classify_multi = ClassifyMulti()
    pick_consensus = PickConsensus()
    classify_multi >> pick_consensus
    flow = Flow(start=classify_multi)
    shared_store = SharedStore(review="这家的寿司是真功夫——鱼新鲜、厨师手艺好、摆盘漂亮。"
                                      "但我们等了20分钟才来水，前菜还漏上了，账单也算错了。"
                                      "说实话不知道该怎么评价这家店")
    flow.run(shared_store)
    print(shared_store.result)
