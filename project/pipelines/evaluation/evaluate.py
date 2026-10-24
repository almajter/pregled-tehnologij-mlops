# /// script
# dependencies = ["openai==3.37.0"]
# ///
import os

from openai import OpenAI

client = OpenAI(
    base_url="https://vllm.apps.okd.alters.si/v1",
    api_key=os.environ["VLLM_API_KEY"],
)

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    messages=[{"role": "user", "content": "What is 12 × 8?"}],
    temperature=0,
)
print(response.choices[0].message.content)
