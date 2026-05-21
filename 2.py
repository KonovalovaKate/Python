import sqlite3
import time

from dotenv import load_dotenv

load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

# Розмірна сітка DOKA PRO (талія у втягнутому стані, см)
SIZE_CHART = [
    ("3XS", 50, 55),
    ("XXS", 50, 57),
    ("XS", 58, 63),
    ("S", 64, 68),
    ("M", 69, 74),
    ("L", 75, 81),
    ("XL", 82, 88),
    ("2XL", 89, 95),
    ("3XL", 96, 101),
    ("4XL", 102, 109),
    ("5XL", 110, 117),
    ("6XL", 118, 126),
]


def _find_size(waist_cm: float):
    for name, waist_min, waist_max in SIZE_CHART:
        if waist_min <= waist_cm <= waist_max:
            return name, waist_min, waist_max
    if waist_cm < SIZE_CHART[0][1]:
        return SIZE_CHART[0]
    return SIZE_CHART[-1]


def _shift_size(size_name: str, step: int):
    names = [row[0] for row in SIZE_CHART]
    index = names.index(size_name) + step
    if 0 <= index < len(names):
        return names[index]
    return None


@tool
def suggest_corset_size(
    waist_cm: float,
    goal: str = "waist_training",
    hip_cm: float = None,
    torso_length: str = "average",
) -> str:
    """Підібрати розмір і модель корсета Dokasport.
    Параметри: waist_cm - обхват талії в см (у втягнутому стані);
    goal - мета: waist_training, weight_loss, postpartum, spine_support;
    hip_cm - обхват стегон в см (опційно);
    torso_length - довжина торсу: short, average, long (опційно)."""
    size_name, waist_min, waist_max = _find_size(waist_cm)
    recommended_size = size_name
    notes = []

    if hip_cm is not None and hip_cm >= waist_cm + 20:
        bigger = _shift_size(size_name, 1)
        if bigger:
            recommended_size = bigger
            notes.append(
                f"Стегна на 20+ см ширші за талію — рекомендовано розмір {bigger} замість {size_name}."
            )

    tighter_size = _shift_size(size_name, -1)
    if goal == "waist_training" and tighter_size:
        notes.append(
            f"Для тренування талії: стандарт {size_name}, або {tighter_size} з розширювачем "
            f"(жорсткіша утяжка, +5–7 см)."
        )

    if torso_length == "short":
        model = "DOKA PRO 25"
        height = 25
        price = 1470
        url = "https://dokasport.com.ua/lateksnij-korset-dlya-shudnennya-na-25-metalevih-vstavok-25-u-visotu"
        alt_model = "DOKA PRO 30"
        alt_height = 30
        model_note = "Короткий торс — краще 25 см."
    else:
        model = "DOKA PRO 30"
        height = 30
        price = 1490
        url = "https://dokasport.com.ua/ortopedichniy-korset-na-25-metalevih-vstavok"
        alt_model = "DOKA PRO 25"
        alt_height = 25
        model_note = "Більше покриття та утяжка — 30 см."

    lines = [
        f"Талія {waist_cm} см → розмір {recommended_size} (діапазон {waist_min}–{waist_max} см).",
        f"Модель: {model}, висота {height} см, {price} грн. {model_note}",
        f"Посилання: {url}",
        f"Альтернатива: {alt_model} ({alt_height} см).",
        "Вимір: талія у найвужчому місці у втягнутому стані.",
    ]
    lines.extend(notes)
    return "\n".join(lines)


CONSULTANT_TOOLS = [suggest_corset_size]
TOOL_BY_NAME = {tool.name: tool for tool in CONSULTANT_TOOLS}

# System prompts for both roles
CONSULTANT_PROMPT = (
    "You are an expert consultant for the 'Dokasport.com.ua' sports store. "
    "Your goal: provide personalized recommendations for equipment based on user needs. "
    "When the customer gives waist size (см), training goal, or asks which corset to choose, "
    "call suggest_corset_size with waist_cm and goal (e.g. waist_training). "
    "Explain the recommended size, DOKA PRO 25 vs 30 cm model, and product link in Ukrainian."
)

USER_PROMPT = (
    "You are a customer at the 'Dokasport' sports store. You want to buy sports equipment. "
    "Ask questions and act like a real person. Keep your responses short."
)


class ChatDatabase:
    def __init__(self, db_path='chat_history.db'):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS messages
                       (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           role TEXT,
                           content TEXT
                       )
                       ''')
        conn.commit()
        conn.close()

    def save_message(self, role, content):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (role, content) VALUES (?, ?)', (role, content))
        conn.commit()
        conn.close()


def stream_response(llm, system_prompt, messages, color_code, label):
    result = ''
    response = llm.stream([SystemMessage(content=system_prompt)] + messages)

    print(f'\033[{color_code}m{label}: ', end='', flush=True)
    for chunk in response:
        result += chunk.content
        print(chunk.content, end='', flush=True)
    print('\033[0m')

    return result


def run_user_turn(llm, messages):
    return stream_response(llm, USER_PROMPT, messages, '32', 'User')


def _execute_tool_calls(tool_calls):
    tool_messages = []
    for tool_call in tool_calls:
        tool = TOOL_BY_NAME.get(tool_call["name"])
        if tool is None:
            content = f"Unknown tool: {tool_call['name']}"
        else:
            content = tool.invoke(tool_call["args"])
        tool_messages.append(
            ToolMessage(content=content, tool_call_id=tool_call["id"])
        )
        print(f'\033[33m[tool] {tool_call["name"]}({tool_call["args"]})\033[0m')
    return tool_messages


def run_consultant_turn(consultant_llm, messages):
    prompt_messages = [SystemMessage(content=CONSULTANT_PROMPT)] + messages
    response = consultant_llm.invoke(prompt_messages)

    while getattr(response, "tool_calls", None):
        messages.append(response)
        messages.extend(_execute_tool_calls(response.tool_calls))
        response = consultant_llm.invoke([SystemMessage(content=CONSULTANT_PROMPT)] + messages)

    print(f'\033[34mConsultant: \033[0m{response.content}')
    return response.content


def run_conversation_turn(user_llm, consultant_llm, db, messages):
    user_result = run_user_turn(user_llm, messages)
    db.save_message("user", user_result)
    messages.append(HumanMessage(content=user_result))
    time.sleep(1)

    consultant_result = run_consultant_turn(consultant_llm, messages)
    print()
    db.save_message("assistant", consultant_result)
    messages.append(AIMessage(content=consultant_result))

    if len(messages) > 10:
        messages = messages[-10:]

    time.sleep(1)
    return messages


def main():
    db = ChatDatabase()

    llm = init_chat_model(
        model="google/gemma-4-e4b",
        model_provider="openai",
        base_url="http://127.0.0.1:1234/v1",
        api_key="dqssd",
    )
    consultant_llm = llm.bind_tools(CONSULTANT_TOOLS)

    initial_msg = "Привіт! Чим можу допомогти у виборі спорядження?"
    print(f"Consultant: {initial_msg}")

    messages = [AIMessage(content=initial_msg)]
    db.save_message("assistant", initial_msg)

    while True:
        messages = run_conversation_turn(llm, consultant_llm, db, messages)


if __name__ == "__main__":
    main()
