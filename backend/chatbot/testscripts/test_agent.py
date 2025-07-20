import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
# print(sys.path) 

from langchain_core.messages import HumanMessage
from agenticai.agent import build_agent

if __name__ == "__main__":
    agent = build_agent()

    # Try different test messages
    test_messages = [
        "Plan a 3-day trip to Tokyo",
        "What's the weather in Rome?",
        "Show me places near the Eiffel Tower",
        "Tell me a joke"
    ]

    for msg in test_messages:
        print(f"\nUser: {msg}")
        result = agent.invoke({
            "messages": [HumanMessage(content=msg)]
        })
        reply = result["messages"][-1].content
        print(f"Bot: {reply}")
