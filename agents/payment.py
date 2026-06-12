from langchain.agents import create_agent

from services.llm_factory import get_llm
from tools.payment import get_payment_info

PAYMENT_PROMPT = (
    "Ти асистент з оформлення замовлень магазину 'Dokasport.com.ua'. "
    "Відповідай українською. "
    "Для інформації про способи оплати та оформлення замовлення — виклич get_payment_info."
)

payment_agent = create_agent(
    model=get_llm(),
    tools=[get_payment_info],
    system_prompt=PAYMENT_PROMPT,
)
