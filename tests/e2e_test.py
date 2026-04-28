"""End-to-end test for Innovation Hub Agent — detailed logging."""
import os
import sys

# Setup env before any imports
os.environ.setdefault('WIKI_PATH', '/home/aiteam-linux/gnust/innovation_hub_wiki')

from dotenv import load_dotenv
load_dotenv('/home/aiteam-linux/gnust/innovation_hub_agent/.env')

from src.agent.core import create_agent

LOG_FILE = '/home/aiteam-linux/gnust/innovation_hub_agent/tests/e2e_report.md'

TESTS = [
    ("Test 1: General knowledge", "Innovation Hub là gì?"),
    ("Test 2: Feature question", "Làm sao để tham gia một event?"),
    ("Test 3: Technical question", "API endpoint để tạo problem là gì?"),
    ("Test 4: Permission question", "Role admin và member khác gì nhau?"),
    ("Test 5: Multi-hop question", "Workflow của một problem từ lúc tạo đến khi solved?"),
    ("Test 6: Deep link follow (2+ hops)", "Cách chấm điểm trong event? Chi tiết từng criteria?"),
    ("Test 7: Cross-domain link follow", "Từ problem tạo room brainstorm, rồi room đó nộp idea vào event — chi tiết toàn bộ flow?"),
]


def run_tests():
    agent = create_agent()

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("# Innovation Hub Agent — E2E Test Report\n\n")

        for title, question in TESTS:
            print(f"\n{'='*60}")
            print(f"  {title}")
            print(f"  Q: {question}")
            print(f"{'='*60}")

            f.write(f"## {title}\n\n")
            f.write(f"**Question:** {question}\n\n")

            result = agent.invoke(
                {'messages': [{'role': 'user', 'content': question}]},
                config={'configurable': {'thread_id': f'test-{title}'}, 'recursion_limit': 15},
            )

            # Log all messages (tool calls, observations, etc.)
            f.write("### Agent Trace\n\n")
            for i, msg in enumerate(result['messages']):
                msg_type = msg.type

                if msg_type == 'human':
                    f.write(f"**[USER]** {msg.content}\n\n")
                    print(f"  [USER] {msg.content[:80]}")

                elif msg_type == 'ai':
                    # Check for tool calls
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        f.write(f"**[AI — Tool Calls]**\n")
                        for tc in msg.tool_calls:
                            f.write(f"- `{tc['name']}({tc['args']})`\n")
                            print(f"  [AI → {tc['name']}] {tc['args']}")
                        f.write("\n")

                        # Log thinking/reasoning if available
                        if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                            reasoning = msg.additional_kwargs.get('reasoning_content')
                            if reasoning:
                                f.write(f"**[AI — Reasoning]**\n```\n{reasoning}\n```\n\n")
                                print(f"  [THINKING] {reasoning[:100]}...")

                    if msg.content:
                        f.write(f"**[AI — Answer]**\n{msg.content}\n\n")
                        print(f"  [AI] {msg.content[:120]}...")

                elif msg_type == 'tool':
                    content = msg.content[:500] if len(msg.content) > 500 else msg.content
                    f.write(f"**[Tool Result]**\n```\n{content}\n```\n\n")
                    print(f"  [TOOL RESULT] {content[:80]}...")

            f.write("---\n\n")
            f.flush()

        f.write("## Summary\n\n")
        f.write(f"- Total tests: {len(TESTS)}\n")
        f.write(f"- All tests completed\n")

    print(f"\n\nReport saved to: {LOG_FILE}")


if __name__ == "__main__":
    run_tests()
