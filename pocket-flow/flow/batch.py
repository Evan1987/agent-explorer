
import asyncio
from pocketflow import BatchNode, AsyncParallelBatchNode
from utils import call_llm, call_llm_async
from typing import List


class SummarizeReviews(BatchNode):
    def prep(self, shared: dict) -> List[str]:
        return shared["reviews"]
    def exec(self, review: str) -> str:
        return call_llm(f"用一句话总结这条评论: {review}")
    def post(self, shared: dict, reviews: List[str], exec_res: List[str]) -> None:
        shared["summaries"] = exec_res


class ParallelSummarizeReviews(AsyncParallelBatchNode):
    async def prep_async(self, shared: dict) -> List[str]:
        return shared["reviews"]
    async def exec_async(self, review: str) -> str:
        return await call_llm_async(f"用一句话总结这条评论: {review}")
    async def post_async(self, shared: dict, reviews: List[str], exec_res: List[str]) -> None:
        shared["summaries"] = exec_res


if __name__ == '__main__':
    original_reviews = [
        "菜很好吃，但服务太慢了，我们等了三十分钟。",
        "全城最好的披萨，酥脆的饼底，新鲜的食材，还会再来。",
        "性价比太低了，意面没味道，分量还小。"
    ]
    shared_store = {"reviews": original_reviews}

    # summarize_reviews = SummarizeReviews(max_retries=3)
    # summarize_reviews.run(shared_store)
    # print(shared_store["summaries"])

    async_summarize_reviews = ParallelSummarizeReviews(max_retries=3)
    asyncio.run(async_summarize_reviews.run_async(shared_store))
    print(shared_store["summaries"])

