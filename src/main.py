"""Entry point — interactive CLI chat with the Innovation Hub Agent."""
import uuid
import os

from dotenv import load_dotenv

from src.agent.core import create_agent


def main():
    load_dotenv()

    print("Initializing Innovation Hub Agent...")
    agent = create_agent()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("Agent ready. Type your question (or 'quit' to exit).\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
        )

        # Print the last AI message
        for msg in reversed(result["messages"]):
            if msg.type == "ai" and msg.content:
                print(f"\nAgent: {msg.content}\n")
                break


if __name__ == "__main__":
    main()
