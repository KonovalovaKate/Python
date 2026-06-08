from langchain.chat_models import init_chat_model


def get_llm():
    return init_chat_model(
        model="google/gemma-4-e4b",
        model_provider="openai",
        base_url="http://127.0.0.1:1234/v1",
        api_key="dqssd",
    )
