
from pocketflow import Flow
from chap02.chain import AddOne, MultiplyByTwo


if __name__ == '__main__':
    # 内部flow
    add1 = AddOne()
    add2 = AddOne()
    add1 >> add2
    inner_flow = Flow(start=add1)
    # 外部flow
    multiply = MultiplyByTwo()
    inner_flow >> multiply
    outer_flow = Flow(start=inner_flow)
    shared_store = {"number": 5}
    outer_flow.run(shared_store)
    print(shared_store["number"])  # 14: (5 + 1 + 1) * 2
