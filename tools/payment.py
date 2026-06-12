from langchain_core.tools import tool


@tool
def get_payment_info() -> str:
    """Return available payment methods and order placement instructions."""
    return (
        "Способи оплати:\n"
        "1. Оплата при отриманні — Нова Пошта або Укрпошта\n"
        "2. Онлайн-оплата карткою на сайті\n"
        "3. Передоплата на картку ПриватБанку\n\n"
        "Оформити замовлення: https://dokasport.com.ua"
    )
