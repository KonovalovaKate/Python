from typing import Annotated, Literal
from typing_extensions import TypedDict

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from agents.guide import GUIDE_TOOLS, guide_node
from agents.payment import payment_node
from services.llm_factory import get_llm

ORCHESTRATOR_PROMPT = (
    "You are the routing orchestrator for the Dokasport corset store assistant. "
    "Analyze the user's latest message and decide which agent should handle it. "
    "Reply with exactly one word:\n"
    "- 'payment' — if the user wants to buy, pay, place an order, or asks about checkout/delivery\n"
    "- 'guide'   — if the user asks about products, sizes, or needs a recommendation"
)

_orchestrator_llm = get_llm()


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next: str


def orchestrator_node(state: AgentState) -> dict:
    messages = [SystemMessage(content=ORCHESTRATOR_PROMPT)] + state["messages"]
    response = _orchestrator_llm.invoke(messages)
    decision = response.content.strip().lower()
    return {"next": "payment" if "payment" in decision else "guide"}


def route_from_orchestrator(state: AgentState) -> Literal["payment", "guide"]:
    return state.get("next", "guide")


builder = StateGraph(AgentState)
builder.add_node("orchestrator", orchestrator_node)
builder.add_node("payment", payment_node)
builder.add_node("guide", guide_node)
builder.add_node("tools", ToolNode(GUIDE_TOOLS))

builder.add_edge(START, "orchestrator")
builder.add_conditional_edges("orchestrator", route_from_orchestrator)
builder.add_conditional_edges("guide", tools_condition)
builder.add_edge("tools", "guide")

agent = builder.compile()


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    messages = []
    while True:
        user_input = input("You: ")
        messages.append(HumanMessage(content=user_input))
        result = agent.invoke({"messages": messages})
        messages = result["messages"]
        print(f"Assistant: {messages[-1].content}\n")
