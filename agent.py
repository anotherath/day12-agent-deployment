import os
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

# 1. Đọc System Prompt

with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# 2. Khai báo State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 3. Khởi tạo LLM và Tools
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
            print(f"---> [LOG] Gọi tool: {tc['name']}({tc['args']})")
    else:
        print("---> [LOG] Trả lời trực tiếp")

    return {"messages": [response]}

# 5. Xây dựng Graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)

tool_node = ToolNode(tools_list)
builder.add_node("tools", tool_node)

# Khai báo edges
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

graph = builder.compile()

# 6. Chat loop
if __name__ == "__main__":
    print("=" * 70)
    print("VinFast AI Assistant — Trợ lý Tư vấn xe Ô tô điện thông minh")
    print(" Gõ 'quit' để thoát")
    print("=" * 70)

    # Lưu trữ lịch sử hội thoại (Stateful Memory)
    chat_history = []

    while True:
        user_input = input("\nKhách hàng: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break

        print("\nVinFast AI đang suy nghĩ...")
        chat_history.append(("human", user_input))
        
        try:
            # Truyền toàn bộ lịch sử tin nhắn (bao gồm user, AI, tool) vào StateGraph
            result = graph.invoke({"messages": chat_history})
            
            # Cập nhật lại chat_history bằng State mới nhất từ Graph để nhớ context
            chat_history = result["messages"]
            
            final = chat_history[-1]
            print(f"\nAI: {final.content}")
        except Exception as e:
            print(f"\n[Lỗi API / Graph]: {e}")
