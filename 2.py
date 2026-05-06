import requests
import sqlite3

# System prompt defining the AI's persona as a Dokasport expert
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are an expert consultant for the 'Dokasport.com.ua' sports store. "
        "Your goal: provide personalized recommendations for equipment based on user needs."
    )
}

class ChatDatabase:
    def __init__(self, db_path='chat_history.db'):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        """Creates the database schema if it doesn't exist."""
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
        """Loads only the 10 most recent messages and prepends the system prompt."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Subquery: get the last 10 records descending, then re-order them ascending for the AI context
        cursor.execute('''
            SELECT role, content FROM (
                SELECT id, role, content FROM messages 
                ORDER BY id DESC LIMIT 10
            ) ORDER BY id ASC
        ''')

        # Start with the mandatory system persona
        messages = [SYSTEM_PROMPT]

        # Append the retrieved history
        for row in cursor.fetchall():
            messages.append({"role": row[0], "content": row[1]})

        conn.close()
        return messages

    def save_message(self, role, content):
        """Persists a new message to the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (role, content) VALUES (?, ?)', (role, content))
        conn.commit()
        conn.close()

def main():
    db = ChatDatabase()
    # Load limited context (System prompt + last 10 messages)
    messages = db.load_messages()

    print("--- Dokasport Consultant is ready! ---")
    print("(Type 'exit' to quit)")

    while True:
        user_message = input("\nYou: ")
        if user_message.lower() in ['exit', 'quit']:
            break

        # Save and add user input to the current session list
        messages.append({"role": "user", "content": user_message})
        db.save_message("user", user_message)

        try:
            # POST request to the local inference server
            response = requests.post(
                'http://127.0.0.1:1234/v1/chat/completions',
                json={
                    "messages": messages,
                    "model": "google/gemma-4-e4b",
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            ai_message = response.json()["choices"][0]["message"]["content"]

            print(f"\nDokasport: {ai_message}")

            # Save and add AI response to session list
            messages.append({"role": "assistant", "content": ai_message})
            db.save_message("assistant", ai_message)

        except Exception as e:
            print(f"Request error: {e}")

if __name__ == "__main__":
    main()