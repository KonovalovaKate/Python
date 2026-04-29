import requests
import sqlite3


class ChatDatabase:
    def __init__(self, db_path='chat_history.db'):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        """Creates the messages table if it does not exist."""
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
        """Loads chat history to provide context for the AI."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT role, content FROM messages ORDER BY id')
        messages = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
        conn.close()
        return messages

    def save_message(self, role, content):
        """Saves a new message to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (role, content) VALUES (?, ?)', (role, content))
        conn.commit()
        conn.close()


def main():
    db = ChatDatabase()
    # Load existing history from DB so the bot remembers past conversations
    messages = db.load_messages()

    print("Chatbot is ready! (Type 'exit' to quit)")

    while True:
        user_message = input("\nYou: ")
        if user_message.lower() in ['exit', 'quit']:
            break

        # 1. Store user message in DB and current context
        messages.append({"role": "user", "content": user_message})
        db.save_message("user", user_message)

        try:
            # 2. Send request to local AI server (e.g., LM Studio)
            response = requests.post(
                'http://127.0.0.1:1234/v1/chat/completions',
                json={
                    "messages": messages,
                    "model": "google/gemma-4-e4b"
                }
            )
            response.raise_for_status()

            ai_message = response.json()["choices"][0]["message"]["content"]

            # 3. Store AI response in DB and current context
            print(f"\nAI: {ai_message}")
            messages.append({"role": "assistant", "content": ai_message})
            db.save_message("assistant", ai_message)

        except Exception as e:
            print(f"Error during request: {e}")


if __name__ == "__main__":
    main()