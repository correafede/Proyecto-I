from groq import Groq
import os

key = os.getenv('GROQ_API_KEY')
print(f"Key: {key}")
print(f"Length: {len(key)}")

try:
    client = Groq(api_key=key)
    # Try a simple test call
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": "Say 'test' in one word"}
        ],
        max_tokens=10
    )
    print("SUCCESS: API key is valid!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"ERROR: {e}")
    print(f"Error type: {type(e).__name__}")
