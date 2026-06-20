
from pocketflow import Node, Flow
from utils import call_llm
from typing import List


class ChatNode(Node):

    def prep(self, shared: dict) -> List[dict] | None:
        messages = shared.setdefault("messages", [])
        if not messages:
            print("Welcome to the chat! Type 'exit' to end the conversation.")
        user_input = input("You: ")
        if user_input.lower().strip() == "exit":
            return None
        messages.append({"role": "user", "content": user_input})
        return messages

    def exec(self, messages: List[dict]) -> str | None:
        if not messages:
            return None
        return call_llm(messages=messages)

    def post(self, shared, prep_res, exec_res):
        if not prep_res or not exec_res:
            print("\nGoodbye!")
            return None   # End conversation

        # Add assistant message to history
        shared["messages"].append({"role": "assistant", "content": exec_res})
        # Print the assistant's response
        print(f"\nAssistant: {exec_res}")
        # Loop back to continue the conversation
        return "continue"


if __name__ == '__main__':
    chat_node = ChatNode()
    chat_node - "continue" >> chat_node
    flow = Flow(start=chat_node)
    history = {}
    flow.run(history)
