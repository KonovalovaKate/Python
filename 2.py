import sqlite3
import time
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


def main():
    db = ChatDatabase()

    # Initialize model via LangChain
    llm = init_chat_model(
        model="google/gemma-4-e4b",
        model_provider="openai",
        base_url="http://127.0.0.1:1234/v1",
        api_key="dqssd",
    )

    # Initial state
    initial_msg = "Привіт! Чим можу допомогти у виборі спорядження?"
    print(f"Consultant: {initial_msg}")

    messages = [AIMessage(content=initial_msg)]
    db.save_message("assistant", initial_msg)

    while True:
        # --- USER BOT TURN ---
        user_result = ''
        user_response = llm.stream([SystemMessage(content=USER_PROMPT)] + messages)

        print('\033[32mUser: ', end='', flush=True)
        for chunk in user_response:
            user_result += chunk.content
            print(chunk.content, end='', flush=True)
        print('\033[0m')

        db.save_message("user", user_result)
        messages.append(HumanMessage(content=user_result))
        time.sleep(1)

        # --- CONSULTANT BOT TURN ---
        consultant_result = ''
        consultant_response = llm.stream([SystemMessage(content=CONSULTANT_PROMPT)] + messages)

        print('\033[34mConsultant: ', end='', flush=True)
        for chunk in consultant_response:
            consultant_result += chunk.content
            print(chunk.content, end='', flush=True)
        print('\033[0m\n')

        db.save_message("assistant", consultant_result)
        messages.append(AIMessage(content=consultant_result))

        # Context management: keep last 10 messages
        if len(messages) > 10:
            messages = messages[-10:]

        time.sleep(1)


if __name__ == "__main__":
    main()