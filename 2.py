import requests
import sqlite3

# Системный промпт, определяющий личность эксперта Dokasport
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are an expert Sales Consultant for 'Dokasport.com.ua,' an online sports equipment and apparel store. "
        "YOUR GOAL: To provide personalized recommendations for sports gear, footwear, and equipment based on the customer's specific needs, fitness level, and goals. "
        "CORE INSTRUCTIONS: "
        "1. QUALIFICATION: If a user’s request is vague, you MUST ask 2-3 clarifying questions before recommending. "
        "2. SELECTION: Always provide 2-3 options when possible: 'Starter' (Budget-friendly), 'Performance' (Best value), 'Elite' (Professional). "
        "3. BENEFITS OVER FEATURES: Explain HOW a feature helps the user. "
        "4. UPSELLING: Subtly suggest related items. "
        "TONE AND VOICE: Professional, motivating, and knowledgeable. Use an encouraging 'coach-like' tone. "
        "CONSTRAINTS: Do NOT provide medical advice. Stay strictly within the topic of sports and fitness."
    )
}


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
        """Загружает историю и добавляет системный промпт в начало."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT role, content FROM messages ORDER BY id')

        # Начинаем список сообщений с системного промпта
        messages = [SYSTEM_PROMPT]

        # Добавляем историю из БД
        for row in cursor.fetchall():
            messages.append({"role": row[0], "content": row[1]})

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
    # Загружаем сообщения (системный промпт уже внутри списка)
    messages = db.load_messages()

    print("--- Консультант Dokasport готов к работе! ---")
    print("(Введите 'exit' для выхода)")

    while True:
        user_message = input("\nВы: ")
        if user_message.lower() in ['exit', 'quit']:
            break

        messages.append({"role": "user", "content": user_message})
        db.save_message("user", user_message)

        try:
            response = requests.post(
                'http://127.0.0.1:1234/v1/chat/completions',
                json={
                    "messages": messages,  # Весь контекст вместе с SYSTEM_PROMPT
                    "model": "google/gemma-4-e4b",
                    "temperature": 0.7  # Немного творчества для "коуч-тона"
                }
            )
            response.raise_for_status()
            ai_message = response.json()["choices"][0]["message"]["content"]

            print(f"\nDokasport: {ai_message}")
            messages.append({"role": "assistant", "content": ai_message})
            db.save_message("assistant", ai_message)

        except Exception as e:
            print(f"Ошибка при запросе: {e}")


if __name__ == "__main__":
    main()