from langchain_core.messages import SystemMessage
from langgraph.graph.message import MessagesState

from services.llm_factory import get_llm
from tools.corset import suggest_corset_size

GUIDE_TOOLS = [suggest_corset_size]

_guide_llm = get_llm().bind_tools(GUIDE_TOOLS)

GUIDE_PROMPT = (
    "You are an expert consultant for the 'Dokasport.com.ua' sports store. "
    "Your goal: provide personalized recommendations for corsets based on user needs. "
    "When the customer gives waist size (cm), training goal, or asks which corset to choose, "
    "call suggest_corset_size with waist_cm and goal (e.g. waist_training). "
    "Explain the recommended size, DOKA PRO 25 vs 30 cm model, and product link in Ukrainian."
)


def guide_node(state: MessagesState) -> dict:
    messages = [SystemMessage(content=GUIDE_PROMPT)] + state["messages"]
    response = _guide_llm.invoke(messages)
    return {"messages": [response]}
