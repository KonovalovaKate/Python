from langchain_core.messages import SystemMessage
from langgraph.graph.message import MessagesState

from services.llm_factory import get_llm

PAYMENT_PROMPT = (
    "You are a checkout assistant for the 'Dokasport.com.ua' sports store. "
    "Your only goal is to help the customer place an order and complete payment. "
    "Always respond in Ukrainian. "
    "Guide the customer through these steps:\n"
    "1. Confirm the chosen product and size.\n"
    "2. Explain available payment methods: оплата при отриманні (Нова Пошта / Укрпошта), "
    "онлайн-оплата карткою на сайті, передоплата на картку ПриватБанку.\n"
    "3. Direct them to place the order: https://dokasport.com.ua\n"
    "If the customer has not yet chosen a product, politely ask them to consult the guide first."
)

_payment_llm = get_llm()


def payment_node(state: MessagesState) -> dict:
    messages = [SystemMessage(content=PAYMENT_PROMPT)] + state["messages"]
    response = _payment_llm.invoke(messages)
    return {"messages": [response]}
