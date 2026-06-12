import re

from langchain_core.messages import SystemMessage
from langgraph.graph.message import MessagesState

from services.llm_factory import get_llm
from tools.corset import suggest_corset_size

GUIDE_PROMPT = (
    "Ти експерт-консультант магазину 'Dokasport.com.ua'. "
    "Допомагаєш підібрати корсет DOKA PRO. "
    "Якщо користувач вказав обхват талії (см) — використай інформацію про розмір у відповіді. "
    "Відповідай українською, коротко і чітко."
)

_llm = get_llm()


def _extract_waist(text: str) -> float | None:
    match = re.search(r"(\d{2,3})\s*см", text)
    if match:
        return float(match.group(1))
    match = re.search(r"талі[яі][^\d]*(\d{2,3})", text)
    if match:
        return float(match.group(1))
    return None


def guide_node(state: MessagesState) -> dict:
    last_msg = state["messages"][-1].content
    waist = _extract_waist(last_msg)

    extra = ""
    if waist:
        extra = "\n\nІнформація про розмір:\n" + suggest_corset_size.invoke({
            "waist_cm": waist,
            "goal": "waist_training",
        })

    system = SystemMessage(content=GUIDE_PROMPT + extra)
    response = _llm.invoke([system] + state["messages"])
    return {"messages": [response]}
