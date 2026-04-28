"""Entry point — interactive CLI chat with the Innovation Hub Agent."""
import uuid
import os

from dotenv import load_dotenv

from src.agent.core import create_agent, run_query, stream_query
from src.agent.config import AgentConfig


def main():
    load_dotenv()

    config = AgentConfig()
    print(f"Innovation Hub Agent (model={config.model_name}, "
          f"max_tools={config.max_tool_calls}, max_tokens={config.max_tokens})")

    agent, config = create_agent(config)
    thread_id = str(uuid.uuid4())

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

        output = run_query(agent, user_input, thread_id, config)
        result = output["result"]
        trace = output["trace"]

        # Print the last AI message
        for msg in reversed(result["messages"]):
            if msg.type == "ai" and msg.content:
                print(f"\nAgent: {msg.content}\n")
                break

        # Print trace summary
        print(f"  [tools: {trace.tools_called} | files: {len(trace.files_read)} | "
              f"time: {trace.duration_seconds:.1f}s]")


if __name__ == "__main__":
    main()
