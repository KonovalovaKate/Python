from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from services.llm_factory import get_llm
from tools.corset import suggest_corset_size

CONSULTANT_TOOLS = [suggest_corset_size]

consultant_llm = get_llm().bind_tools(CONSULTANT_TOOLS)

CONSULTANT_PROMPT = (
    "You are an expert consultant for the 'Dokasport.com.ua' sports store. "
    "Your goal: provide personalized recommendations for equipment based on user needs. "
    "When the customer gives waist size (см), training goal, or asks which corset to choose, "
    "call suggest_corset_size with waist_cm and goal (e.g. waist_training). "
    "Explain the recommended size, DOKA PRO 25 vs 30 cm model, and product link in Ukrainian."
)


def consultant_node(state: MessagesState):
    messages = [SystemMessage(content=CONSULTANT_PROMPT)] + state["messages"]
    response = consultant_llm.invoke(messages)
    return {"messages": [response]}


builder = StateGraph(MessagesState)
builder.add_node("consultant", consultant_node)
builder.add_node("tools", ToolNode(CONSULTANT_TOOLS))
builder.add_edge(START, "consultant")
builder.add_conditional_edges("consultant", tools_condition)
builder.add_edge("tools", "consultant")

# Compiled graph exported for LangGraph Studio / API (referenced in langgraph.json)
agent = builder.compile()


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage
    messages = []
    while True:
        user_input = input("You: ")
        messages.append(HumanMessage(content=user_input))
        result = agent.invoke({"messages": messages})
        messages = result["messages"]
        print(f"Consultant: {messages[-1].content}\n")
