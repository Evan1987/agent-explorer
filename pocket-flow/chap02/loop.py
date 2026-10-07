from typing import Any

from pydantic import BaseModel
from pocketflow import Node, Flow


class ShareStore(BaseModel):
    number: int
    path: str = ""

    def model_post_init(self, context: Any, /) -> None:
        self.path = str(self.number)

    def set_number(self, number: int):
        self.number = number
        self.path += f" -> {number}"


class DivTwo(Node):
    def prep(self, shared: ShareStore) -> int:
        return shared.number
    def exec(self, prep_res: int) -> int:
        return prep_res // 2
    def post(self, shared: ShareStore, prep_res: int, exec_res: int) -> None:
        shared.set_number(exec_res)


class Multiply3AndAddOne(Node):
    def prep(self, shared: ShareStore) -> int:
        return shared.number
    def exec(self, prep_res: int) -> int:
        return prep_res * 3 + 1
    def post(self, shared: ShareStore, prep_res: int, exec_res: int) -> None:
        shared.set_number(exec_res)


class Exit(Node):
    def prep(self, shared: ShareStore) -> None:
        pass
    def exec(self, prep_res: None) -> None:
        pass
    def post(self, shared: ShareStore, prep_res: None, exec_res: None) -> None:
        print("Collatz Conjecture Loop finished!")
        print(shared.path)


class CheckOddEven(Node):
    def prep(self, shared: ShareStore) -> int:
        return shared.number
    def exec(self, prep_res: int) -> str:
        if prep_res == 1:
            return "done"
        if prep_res % 2 == 0:
            return "even"
        return "odd"
    def post(self, shared: ShareStore, prep_res: int, exec_res: str) -> str:
        return exec_res


if __name__ == '__main__':
    div_two = DivTwo()
    multiply_3_and_add_one = Multiply3AndAddOne()
    check_odd_even = CheckOddEven()
    exit = Exit()
    check_odd_even - "odd" >> multiply_3_and_add_one >> check_odd_even
    check_odd_even - "even" >> div_two >> check_odd_even
    check_odd_even - "done" >> exit
    flow = Flow(start=check_odd_even)
    shared_store = ShareStore(number=28)
    flow.run(shared_store)
