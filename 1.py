import requests


def main():
    messages = []
    while True:
        user_message = input("\nYou: ")
        messages.append({"role": "user", "content": user_message})

        response = requests.request(
            method='POST',
            url='http://127.0.0.1:1234/v1/chat/completions',
            json={
                "messages": messages,
                "model": "google/gemma-4-e4b"
            }
        )

        ai_message = response.json()["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": ai_message})
        print("\nAI: " + ai_message)


if __name__ == '__main__':
    main()
