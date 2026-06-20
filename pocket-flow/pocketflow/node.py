"""Core node and flow primitives for pocketflow.

This module defines the building blocks of a pocketflow pipeline:

* :class:`BaseNode` — minimal node with prep/exec/post lifecycle and
  successor wiring via ``>>`` and ``- "action" >>``.
* :class:`Node` — synchronous node with retry/back-off support.
* :class:`BatchNode` — runs ``exec`` over an iterable of items.
* :class:`Flow` / :class:`BatchFlow` — synchronous orchestrators.
* :class:`AsyncNode` and friends — asyncio-based counterparts.

Public behaviour is unchanged from the original implementation; this file
only adds type hints, formatting, and docstrings.
"""

from __future__ import annotations

import asyncio
import copy
import time
import warnings
from typing import Any, Dict, Iterable, List, Optional


Shared = Any
PrepRes = Any
ExecRes = Any
PostRes = Any
Action = Optional[str]
Params = Dict[str, Any]


class _ConditionalTransition:
    """
    node - "action"`` 表达式产生的中间对象，用于将带标签的后继节点连接到源节点。

    Args:
        src (BaseNode): 发起条件转移的源节点。
        action (str): 后继节点对应的动作标签，用于在 Flow 中按标签选择分支。

    Returns:
        BaseNode: ``__rshift__`` 返回源节点通过 ``next(target, action)`` 注册后的目标节点。
    """
    def __init__(self, src: "BaseNode", action: str) -> None:
        self.src = src
        self.action = action

    def __rshift__(self, target: "BaseNode") -> "BaseNode":
        return self.src.next(target, self.action)


class BaseNode:
    """Minimal node with a prep/exec/post lifecycle and successor wiring."""

    def __init__(self) -> None:
        self.params: Params = {}
        self.successors: Dict[str, "BaseNode"] = {}

    def set_params(self, params: Params) -> None:
        self.params = params

    def next(self, node: "BaseNode", action: str = "default") -> "BaseNode":
        if action in self.successors:
            warnings.warn(f"Overwriting successor for action `{action}`")
        self.successors[action] = node
        return node

    # --- lifecycle hooks (override in subclasses) -------------------------

    def prep(self, shared: Shared) -> PrepRes:
        """「准备」，从Shared拿取数据。仅做只读操作"""
        pass

    def exec(self, prep_res: PrepRes) -> ExecRes:
        """「执行」，处理数据，返回结果，纯计算不读不写，可安全重试"""
        pass

    def _exec(self, prep_res: PrepRes) -> ExecRes:
        """执行节点的核心逻辑，子类可重写以添加重试等策略。"""
        return self.exec(prep_res)

    def post(self, shared: Shared, prep_res: PrepRes, exec_res: ExecRes) -> Action:
        """「收尾」，更新Shared，返回下一步动作"""
        pass

    def _run(self, shared: Shared) -> Action:
        """将 上述三步整合起来"""
        prep_res = self.prep(shared)
        exec_res = self._exec(prep_res)
        return self.post(shared, prep_res, exec_res)

    # --- internal runners -------------------------------------------------

    def run(self, shared: Shared) -> Action:
        if self.successors:
            warnings.warn("Node don't run successors. Use Flow.")
        return self._run(shared)

    # --- operator sugar ---------------------------------------------------

    def __rshift__(self, other: "BaseNode") -> "BaseNode":
        """「然后」对接下一个节点"""
        return self.next(other)

    def __sub__(self, action: str) -> _ConditionalTransition:
        if not isinstance(action, str):
            raise TypeError("Action must be a string")
        return _ConditionalTransition(self, action)


class Node(BaseNode):
    """Synchronous node with retry/back-off around :meth:`exec`."""

    def __init__(self, max_retries: int = 1, wait: int = 0) -> None:
        super().__init__()
        self.max_retries = max_retries
        self.wait = wait
        self.cur_retry: int = 0

    def exec_fallback(self, prep_res: Any, exception: Exception) -> Any:
        raise exception

    def _exec(self, prep_res: Any) -> Any:
        for self.cur_retry in range(self.max_retries):
            try:
                return self.exec(prep_res)
            except Exception as e:
                if self.cur_retry == self.max_retries - 1:
                    return self.exec_fallback(prep_res, e)
                if self.wait > 0:
                    time.sleep(self.wait)
        return None


class BatchNode(Node):
    """Runs the wrapped :meth:`exec` over each item in an iterable."""

    def _exec(self, items: Optional[Iterable[Any]]) -> List[Any]:
        return [super(BatchNode, self)._exec(i) for i in (items or [])]


class Flow(BaseNode):
    """Synchronous orchestrator that walks node successors by action."""

    def __init__(self, start: Optional[BaseNode] = None) -> None:
        super().__init__()
        self.start_node = start

    def start(self, start: BaseNode) -> BaseNode:
        self.start_node = start
        return start

    def get_next_node(self, curr: BaseNode, action: Action) -> Optional[BaseNode]:
        nxt = curr.successors.get(action or "default")
        if not nxt and curr.successors:
            warnings.warn(f"Flow ends: '{action}' not found in {list(curr.successors)}")
        return nxt

    def _orch(self, shared: Shared, params: Optional[Params] = None) -> Action:
        """按 action 依次驱动节点链执行，完成一次编排调度。从起始节点开始，逐节点执行 _run，根据返回的 action 查找后继节点，
        循环推进直至无后继可走。每个节点均以浅拷贝运行，避免状态污染。
        """
        curr: Optional[BaseNode] = copy.copy(self.start_node)
        p: Params = params or {**self.params}
        last_action: Action = None
        while curr:
            curr.set_params(p)
            last_action = curr._run(shared)
            curr = copy.copy(self.get_next_node(curr, last_action))
        return last_action

    def _run(self, shared: Shared) -> Action:
        p = self.prep(shared)
        o = self._orch(shared)
        return self.post(shared, p, o)

    def post(self, shared: Shared, prep_res: Any, exec_res: Any) -> Action:
        return exec_res


class BatchFlow(Flow):
    """Runs :meth:`_orch` once per item produced by :meth:`prep`."""

    def _run(self, shared: Shared) -> Action:
        pr = self.prep(shared) or []
        for bp in pr:
            self._orch(shared, {**self.params, **bp})
        return self.post(shared, pr, None)


class AsyncNode(Node):
    """Asyncio counterpart of :class:`Node`."""

    async def prep_async(self, shared: Shared) -> Any:
        pass

    async def exec_async(self, prep_res: Any) -> Any:
        pass

    async def exec_fallback_async(self, prep_res: Any, exc: Exception) -> Any:
        raise exc

    async def post_async(
        self, shared: Shared, prep_res: Any, exec_res: Any
    ) -> Action:
        pass

    async def _exec(self, prep_res: Any) -> Any:
        for self.cur_retry in range(self.max_retries):
            try:
                return await self.exec_async(prep_res)
            except Exception as e:
                if self.cur_retry == self.max_retries - 1:
                    return await self.exec_fallback_async(prep_res, e)
                if self.wait > 0:
                    await asyncio.sleep(self.wait)

    async def run_async(self, shared: Shared) -> Action:
        if self.successors:
            warnings.warn("Node won't run successors. Use AsyncFlow.")
        return await self._run_async(shared)

    async def _run_async(self, shared: Shared) -> Action:
        p = await self.prep_async(shared)
        e = await self._exec(p)
        return await self.post_async(shared, p, e)

    def _run(self, shared: Shared) -> Action:
        raise RuntimeError("Use run_async.")


class AsyncBatchNode(AsyncNode, BatchNode):
    """Sequential async batch node — awaits each item in order."""

    async def _exec(self, items: Iterable[Any]) -> List[Any]:
        return [await super(AsyncBatchNode, self)._exec(i) for i in items]


class AsyncParallelBatchNode(AsyncNode, BatchNode):
    """Parallel async batch node — awaits all items via :func:`asyncio.gather`."""

    async def _exec(self, items: Iterable[Any]) -> List[Any]:
        return await asyncio.gather(
            *(super(AsyncParallelBatchNode, self)._exec(i) for i in items)
        )


class AsyncFlow(Flow, AsyncNode):
    """Asyncio counterpart of :class:`Flow` (mixed sync/async successors OK)."""

    async def _orch_async(
        self, shared: Shared, params: Optional[Params] = None
    ) -> Action:
        curr: Optional[BaseNode] = copy.copy(self.start_node)
        p: Params = params or {**self.params}
        last_action: Action = None
        while curr:
            curr.set_params(p)
            last_action = (
                await curr._run_async(shared)
                if isinstance(curr, AsyncNode)
                else curr._run(shared)
            )
            curr = copy.copy(self.get_next_node(curr, last_action))
        return last_action

    async def _run_async(self, shared: Shared) -> Action:
        p = await self.prep_async(shared)
        o = await self._orch_async(shared)
        return await self.post_async(shared, p, o)

    async def post_async(
        self, shared: Shared, prep_res: Any, exec_res: Any
    ) -> Action:
        return exec_res


class AsyncBatchFlow(AsyncFlow, BatchFlow):
    """Sequential async batch flow."""

    async def _run_async(self, shared: Shared) -> Action:
        pr = await self.prep_async(shared) or []
        for bp in pr:
            await self._orch_async(shared, {**self.params, **bp})
        return await self.post_async(shared, pr, None)


class AsyncParallelBatchFlow(AsyncFlow, BatchFlow):
    """Parallel async batch flow — schedules all items concurrently."""

    async def _run_async(self, shared: Shared) -> Action:
        pr = await self.prep_async(shared) or []
        await asyncio.gather(
            *(self._orch_async(shared, {**self.params, **bp}) for bp in pr)
        )
        return await self.post_async(shared, pr, None)
