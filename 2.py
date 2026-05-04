import requests
import sqlite3

# System prompt defining the AI's persona as a Dokasport expert
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Ви — експерт-консультант магазину спортивних товарів 'Dokasport.com.ua'. "
        "ВАША МЕТА: надавати персоналізовані рекомендації щодо спортивного спорядження, взуття та екіпірування, "
        "виходячи з потреб клієнта, його рівня підготовки та цілей. "
        "ОСНОВНІ ІНСТРУКЦІЇ: "
        "1. КВАЛІФІКАЦІЯ: Якщо запит користувача розмитий, ви ПОВИННІ поставити 2-3 уточнюючих питання перед рекомендацією. "
        "2. ВИБІР: Завжди пропонуйте 2-3 варіанти: 'Starter' (бюджетний), 'Performance' (оптимальний), 'Elite' (професійний). "
        "3. ПЕРЕВАГИ НАД ХАРАКТЕРИСТИКАМИ: Пояснюйте, ЯК конкретна функція допоможе користувачеві. "
        "4. ДОДАТКОВІ ПРОДАЖІ: Ненав'язливо пропонуйте супутні товари для повного комплекту. "
        "ТОН ТА СТИЛЬ: Професійний, мотивуючий та обізнаний. Використовуйте заохочувальний тон 'тренера'. "
        "ОБМЕЖЕННЯ: НЕ надавайте медичних порад. Дотримуйтесь виключно теми спорту та фітнесу."
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
        """Loads chat history and prepends the system prompt."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT role, content FROM messages ORDER BY id')

        # Initialize message list with the system persona
        messages = [SYSTEM_PROMPT]

        # Append history from the database
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
    # Load context (System prompt + History)
    messages = db.load_messages()

    print("--- Консультант Dokasport готовий до роботи! ---")
    print("(Введіть 'exit' для виходу)")

    while True:
        user_message = input("\nВи: ")
        if user_message.lower() in ['exit', 'quit']:
            break

        messages.append({"role": "user", "content": user_message})
        db.save_message("user", user_message)

        try:
            # Request to local AI server
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
            messages.append({"role": "assistant", "content": ai_message})
            db.save_message("assistant", ai_message)

        except Exception as e:
            print(f"Request error: {e}")


if __name__ == "__main__":
    main()