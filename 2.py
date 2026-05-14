import sqlite3
import time
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# System prompt configuration
CONSULTANT_PROMPT = (
    "You are an expert consultant for the 'Dokasport.com.ua' sports store. "
    "Your goal: provide personalized recommendations for equipment based on user needs."
)

USER_BOT_PROMPT = (
    "You are a customer at the 'Dokasport' sports store. You want to buy sports equipment. "
    "Ask questions, describe your needs, and act like a real person. Keep your responses short."
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

    def load_messages(self):
        """Loads history and converts it into LangChain message objects."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT role, content
                       FROM (SELECT id, role, content FROM messages ORDER BY id DESC LIMIT 10)
                       ORDER BY id ASC
                       ''')

        messages = [SystemMessage(content=CONSULTANT_PROMPT)]

        for role, content in cursor.fetchall():
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        conn.close()
        return messages

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
        api_key="not-needed",
    )

    # Initial greeting from Consultant
    initial_greeting = "Добрий день! Вітаємо у магазині Dokasport. Чим можу допомогти вам сьогодні?"
    print(f"Consultant: {initial_greeting}")

    messages = [AIMessage(content=initial_greeting)]
    db.save_message("assistant", initial_greeting)

    print("\n--- Automatic Bot-to-Bot Dialogue Started ---")

    while True:
        # --- USER BOT TURN ---
        user_result = ''
        # Use USER_BOT_PROMPT to simulate a customer
        user_response = llm.stream([SystemMessage(content=USER_BOT_PROMPT)] + messages)

        print("\033[32mUser Bot: ", end='', flush=True)
        for chunk in user_response:
            user_result += chunk.content
            print(chunk.content, end='', flush=True)
        print('\033[0m')

        db.save_message("user", user_result)
        messages.append(HumanMessage(content=user_result))

        # Optional: Manual trigger to control flow
        input("\n(Press Enter for Consultant to reply...)")

        # --- CONSULTANT BOT TURN ---
        consultant_result = ''
        # Use CONSULTANT_PROMPT to reply as the store expert
        consultant_response = llm.stream([SystemMessage(content=CONSULTANT_PROMPT)] + messages)

        print("\033[34mConsultant: ", end='', flush=True)
        for chunk in consultant_response:
            consultant_result += chunk.content
            print(chunk.content, end='', flush=True)
        print('\033[0m')

        db.save_message("assistant", consultant_result)
        messages.append(AIMessage(content=consultant_result))

        # Context management: Keep last 10 messages in memory to prevent overflow
        if len(messages) > 11:
            messages = [messages[0]] + messages[-10:]


if __name__ == "__main__":
    main()