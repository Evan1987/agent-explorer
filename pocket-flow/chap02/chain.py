from pocketflow import Node, Flow


class AddOne(Node):
    def prep(self, shared: dict[str, int]) -> int:
        return shared["number"]

    def exec(self, prep_res: int) -> int:
        return prep_res + 1

    def post(self, shared: dict[str, int], prep_res: int, exec_res: int) -> None:
        shared["number"] = exec_res


class MultiplyByTwo(Node):
    def prep(self, shared: dict[str, int]) -> int:
        return shared["number"]

    def exec(self, prep_res: int) -> int:
        return prep_res * 2

    def post(self, shared: dict[str, int], prep_res: int, exec_res: int) -> None:
        shared["number"] = exec_res


if __name__ == '__main__':
    add = AddOne()
    multiply = MultiplyByTwo()
    add >> multiply
    flow = Flow(start=add)
    shared_store = {"number": 8}
    flow.run(shared_store)
    print(shared_store["number"])  # 18

