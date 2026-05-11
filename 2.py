import sqlite3
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# System prompt configuration
SYSTEM_PROMPT_CONTENT = (
    "You are an expert consultant for the 'Dokasport.com.ua' sports store. "
    "Your goal: provide personalized recommendations for equipment based on user needs."
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
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           role
                           TEXT,
                           content
                           TEXT
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

        # Start with the mandatory system persona
        messages = [SystemMessage(content=SYSTEM_PROMPT_CONTENT)]

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
    messages = db.load_messages()

    # Initialize model via LangChain
    # Using 'openai' provider as LM Studio emulates OpenAI API
    llm = init_chat_model(
        model="google/gemma-4-e4b",
        model_provider="openai",
        base_url="http://127.0.0.1:1234/v1",
        api_key="not-needed",
    )

    print("--- Dokasport Consultant (LangChain Mode) is ready! ---")
    print("(Type 'exit' to quit)")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            break

        # Persist user input and add to session memory
        db.save_message("user", user_input)
        messages.append(HumanMessage(content=user_input))

        try:
            # Model invocation
            response = llm.invoke(messages)
            ai_message = response.content

            print(f"\nDokasport: {ai_message}")

            # Persist AI response
            db.save_message("assistant", ai_message)
            messages.append(AIMessage(content=ai_message))

            # Context management: Keep system prompt + last 10 messages in memory
            if len(messages) > 11:
                messages = [messages[0]] + messages[-10:]

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()