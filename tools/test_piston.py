import asyncio
import httpx

async def main():
    payload = {
        "language": "python",
        "version": "3.10.0",
        "files": [{"content": "import sys\nprint('Hello ' + sys.stdin.read().strip())"}],
        "stdin": "Judge0 replacement with Piston"
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post("https://emkc.org/api/v2/piston/execute", json=payload)
        print("Status:", r.status_code)
        print("Body:", r.json())

if __name__ == "__main__":
    asyncio.run(main())
