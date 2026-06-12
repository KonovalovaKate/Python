from langchain_core.messages import SystemMessage
from langgraph.graph.message import MessagesState

from services.llm_factory import get_llm

PAYMENT_PROMPT = (
    "Ти асистент з оформлення замовлень магазину 'Dokasport.com.ua'. "
    "Відповідай українською. "
    "Способи оплати: оплата при отриманні (Нова Пошта / Укрпошта), "
    "онлайн-оплата карткою на сайті, передоплата на картку ПриватБанку. "
    "Для замовлення: https://dokasport.com.ua . "
    "Допоможи клієнту оформити замовлення."
)

_llm = get_llm()


def payment_node(state: MessagesState) -> dict:
    system = SystemMessage(content=PAYMENT_PROMPT)
    response = _llm.invoke([system] + state["messages"])
    return {"messages": [response]}
