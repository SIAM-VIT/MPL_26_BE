import asyncio
import httpx

async def test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("--- 1. Testing Judge Health with Piston ---")
        r = await client.get("http://localhost:8000/api/admin/judge/health", headers={"admin-passcode": "SunSunSunday"})
        print("Health check:", r.status_code, r.json())

        print("\n--- 2. Logging in as Team Alpha ---")
        r = await client.post("http://localhost:8000/api/auth/login", json={"name": "Team Alpha", "passcode": "alpha123"})
        team = r.json()
        token = team["session_token"]
        print("Team Auth:", r.status_code, team["name"])

        print("\n--- 3. Fetching Team Questions ---")
        r = await client.get("http://localhost:8000/api/main/questions", headers={"X-Team-Token": token})
        questions = r.json()
        q1 = questions[0]
        print(f"Question {q1['id']}: {q1['title']}")
        print("Visible Test Cases:", q1.get("visible_test_cases"))

        print("\n--- 4. Testing POST /api/main/run (Sample Execution via Piston) ---")
        # Let's inspect what Question 1 wants:
        # Question 1 is Prime Sum / Two Sum / etc.
        test_case = q1.get("visible_test_cases", [{}])[0]
        sample_input = test_case.get("input", "")
        expected = test_case.get("expected_output", "")
        print(f"Input: '{sample_input}' -> Expected: '{expected}'")

        # Let's write a python solution that echoes or computes correctly:
        solution = f"""
import sys
# Python solution
input_data = sys.stdin.read().strip()
print('{expected.strip()}')
"""
        r = await client.post(
            "http://localhost:8000/api/main/run",
            headers={"X-Team-Token": token},
            json={
                "question_id": q1["id"],
                "language": "python",
                "source_code": solution.strip()
            }
        )
        print("Run Status:", r.status_code)
        res = r.json()
        print("Run Verdict:", res.get("status"))
        print("Test Case Results:", res.get("results"))

        print("\n--- 5. Testing POST /api/main/submit (Scored Submission via Piston) ---")
        r = await client.post(
            "http://localhost:8000/api/main/submit",
            headers={"X-Team-Token": token},
            json={
                "question_id": q1["id"],
                "language": "python",
                "source_code": solution.strip()
            }
        )
        print("Submit Status:", r.status_code)
        sub_res = r.json()
        print("Submit Verdict:", sub_res.get("status"))
        print("Points Awarded:", sub_res.get("points_awarded"))
        print("Test Case Results:", sub_res.get("results"))

if __name__ == "__main__":
    asyncio.run(test())
