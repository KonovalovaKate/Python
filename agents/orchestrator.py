from typing import Annotated, Literal

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from agents.guide import guide_node
from agents.payment import payment_node

PAYMENT_KEYWORDS = [
    "купити", "купить", "оплата", "оплатити", "оплатить",
    "замовити", "замовлення", "заказать", "заказ",
    "buy", "pay", "order", "checkout",
]


class State(TypedDict):
    messages: Annotated[list, add_messages]
    next: str


def supervisor_node(state: State) -> dict:
    last = state["messages"][-1]
    # Only route to an agent when the last message is from a human
    if not isinstance(last, HumanMessage):
        return {"next": "__end__"}
    text = last.content.lower() if hasattr(last, "content") else ""
    if any(kw in text for kw in PAYMENT_KEYWORDS):
        return {"next": "payment_agent"}
    return {"next": "guide_agent"}


def route(state: State) -> Literal["guide_agent", "payment_agent", "__end__"]:
    return state["next"]


builder = StateGraph(State)
builder.add_node("supervisor", supervisor_node)
builder.add_node("guide_agent", guide_node)
builder.add_node("payment_agent", payment_node)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", route, ["guide_agent", "payment_agent", END])
builder.add_edge("guide_agent", "supervisor")
builder.add_edge("payment_agent", "supervisor")

agent = builder.compile()


if __name__ == "__main__":
    messages = []
    while True:
        user_input = input("You: ")
        messages.append(HumanMessage(content=user_input))
        result = agent.invoke({"messages": messages})
        messages = result["messages"]
        print(f"Assistant: {messages[-1].content}\n")
