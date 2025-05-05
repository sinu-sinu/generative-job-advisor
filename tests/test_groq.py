import asyncio
from app.services.groq_service import chat_completion

def test_groq_basic_response():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What are some good careers for a data analyst?"}
    ]
    result = asyncio.run(chat_completion(messages))
    assert isinstance(result, str)
    assert len(result) > 10
