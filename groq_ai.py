import time
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
Give useful and shortly answers,
Don't forget to add, "sir".
"""

chat_history = []

def get_best_model():
    try:
        model_list = client.models.list()
        available = [m.id for m in model_list.data]
        
        priority = [
            "llama-3.3-70b",
            "llama-3.2-90b",
            "llama-3.2-70b",
            "llama-3.1-8b",
            "mixtral-8x7b",
            "gemma2-9b-it"
        ]

        for name in priority:
            for model_id in available:
                if name in model_id.lower():
                    print(f"✔ Selected model: {model_id}")
                    return model_id
        return available[0]
    except Exception as e:
        print(f"Error fetching models: {e}")
        return "llama-3.3-70b" # Fallback

BEST_MODEL = get_best_model()

def get_response_stream(user_text, start_time):
    global chat_history

    chat_history.append({"role": "user", "content": user_text})

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + chat_history[-5:]
    )

    first_token_time = None

    completion = client.chat.completions.create(
        model=BEST_MODEL,
        messages=messages,
        max_tokens=200,
        stream=True
    )

    full_response = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            if first_token_time is None:
                first_token_time = time.time()
                latency = first_token_time - start_time
                print(f"[LLM FIRST TOKEN] {latency:.3f}s")
            
            token = chunk.choices[0].delta.content
            full_response += token
            yield token

    chat_history.append({"role": "assistant", "content": full_response})

def reset_history():
    global chat_history
    chat_history = []
