from langchain.agents import create_agent

from services.llm_factory import get_llm
from tools.corset import suggest_corset_size

GUIDE_PROMPT = (
    "Ти експерт-консультант магазину 'Dokasport.com.ua'. "
    "Допомагаєш підібрати корсет DOKA PRO. "
    "Якщо користувач вказав обхват талії (см) — виклич інструмент suggest_corset_size. "
    "Відповідай українською, коротко і чітко."
)

guide_agent = create_agent(
    model=get_llm(),
    tools=[suggest_corset_size],
    system_prompt=GUIDE_PROMPT,
)
