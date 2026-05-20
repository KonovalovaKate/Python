import sqlite3
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


# System prompts for both roles
CONSULTANT_PROMPT = (
    "You are an expert consultant for the 'Dokasport.com.ua' sports store. "
    "Your goal: provide personalized recommendations for equipment based on user needs."
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


def run_consultant_turn(llm, messages):
    return stream_response(llm, CONSULTANT_PROMPT, messages, '34', 'Consultant')


def run_conversation_turn(llm, db, messages):
    user_result = run_user_turn(llm, messages)
    db.save_message("user", user_result)
    messages.append(HumanMessage(content=user_result))
    time.sleep(1)

    consultant_result = run_consultant_turn(llm, messages)
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

    initial_msg = "Привіт! Чим можу допомогти у виборі спорядження?"
    print(f"Consultant: {initial_msg}")

    messages = [AIMessage(content=initial_msg)]
    db.save_message("assistant", initial_msg)

    while True:
        messages = run_conversation_turn(llm, db, messages)


if __name__ == "__main__":
    main()
