import os
import sys
import logging
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from tools import search_car, check_promotions, calculate_rolling_price
from dotenv import load_dotenv

load_dotenv()

# Fix stdout encoding for Vietnamese on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger(__name__)

# 1. Doc System Prompt

with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# 2. Khai bao State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 3. Khoi tao LLM va Tools
tools_list = [search_car, check_promotions, calculate_rolling_price]
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools_list)

# 4. Agent Node
def agent_node(state: AgentState):
    messages = state["messages"]
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)

    # === LOGGING ===
    if response.tool_calls:
        for tc in response.tool_calls:
            logger.info(f"[LOG] Goi tool: {tc['name']}({tc['args']})")
    else:
        logger.info("[LOG] Tra loi truc tiep")

    return {"messages": [response]}

# 5. Xay dung Graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)

tool_node = ToolNode(tools_list)
builder.add_node("tools", tool_node)

# Khai bao edges
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

graph = builder.compile()

# 6. Chat loop
if __name__ == "__main__":
    print("=" * 70)
    print("VinFast AI Assistant - Tro ly Tu van xe O to dien thong minh")
    print(" Go 'quit' de thoat")
    print("=" * 70)

    # Luu tru lich su hoi thoai (Stateful Memory)
    chat_history = []

    while True:
        user_input = input("\nKhach hang: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break

        print("\nVinFast AI dang suy nghi...")
        chat_history.append(("human", user_input))
        
        try:
            # Truyen toan bo lich su tin nhan (bao gom user, AI, tool) vao StateGraph
            result = graph.invoke({"messages": chat_history})
            
            # Cap nhat lai chat_history bang State moi nhat tu Graph de nho context
            chat_history = result["messages"]
            
            final = chat_history[-1]
            print(f"\nAI: {final.content}")
        except Exception as e:
            print(f"\n[Loi API / Graph]: {e}")
