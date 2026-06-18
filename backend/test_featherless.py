import asyncio
import openai

async def main():
    client = openai.AsyncOpenAI(
        base_url="https://api.featherless.ai/v1",
        api_key="rc_beb3000a93c1d574b42d99df37e7528492eea2de7bb7477711bfb8031fd754c5",
        default_headers={"Authorization": "Bearer rc_beb3000a93c1d574b42d99df37e7528492eea2de7bb7477711bfb8031fd754c5"}
    )
    
    try:
        resp = await client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=10
        )
        print("Success! Response:")
        print(resp.choices[0].message.content)
    except Exception as e:
        print(f"Failed: {type(e).__name__} - {e}")

asyncio.run(main())
