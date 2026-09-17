#!/usr/bin/env python3
"""MPL Event Platform - seed script.

Creates demo teams and the three MAIN questions (debugging, math, leetcode)
with both visible and hidden test cases.

Usage:
    python seed.py
    python seed.py --url http://localhost:8000

Re-running is safe: existing teams/questions are skipped and test cases are
replaced.
"""
import sys

import requests

from seeding.questions import QUESTIONS, TEAMS, QUESTION_SETS_CONFIG

BASE_URL = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--url" else "http://localhost:8000"
ADMIN_HEADERS = {"admin-passcode": os.getenv("ADMIN_PASSCODE", "SunSunSunday"), "Content-Type": "application/json"}


def api_call(method, path, data=None, params=None):
    """Never explode on a non-JSON response (the old seeder did)."""
    try:
        r = requests.request(
            method, f"{BASE_URL}{path}", json=data, params=params,
            headers=ADMIN_HEADERS, timeout=30,
        )
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Cannot reach {BASE_URL}. Start the server with: "
              "uvicorn app.main:app --reload")
        sys.exit(1)

    try:
        body = r.json()
    except ValueError:
        body = {"detail": r.text[:200]}
    return r.status_code, body


def main():
    print("=" * 60)
    print("  MPL Event Platform - Seed Script")
    print(f"  Target: {BASE_URL}")
    print("=" * 60)

    print("\nCreating MAIN questions...")
    title_to_id = {}
    for question in QUESTIONS:
        cases = question.pop("_cases") if "_cases" in question else []
        code, res = api_call("POST", "/api/admin/questions", question)
        if code != 200:
            print(f"  FAIL  {question['title']}: {res}")
            continue

        qid = res["id"]
        title_to_id[question["title"]] = qid
        code, res = api_call(
            "POST", f"/api/admin/questions/{qid}/test-cases", cases, params={"replace": "true"}
        )
        status = "OK" if code == 200 else "FAIL"
        print(f"  {status}   [{question['sub_type']:<9}] {question['title']} "
              f"(id={qid}, {len(cases)} tests, {question['points']} pts)")

    print("\nCreating Question Sets (3 layers: Debug, Math, Leetcode)...")
    for qset in QUESTION_SETS_CONFIG:
        payload = {
            "name": qset["name"],
            "debug_question_id": title_to_id.get(qset["debug"]),
            "math_question_id": title_to_id.get(qset["math"]),
            "leetcode_question_id": title_to_id.get(qset["leetcode"]),
        }
        code, res = api_call("POST", "/api/admin/question-sets", payload)
        if code == 200:
            print(f"  OK    {qset['name']} -> Debug: {payload['debug_question_id']}, "
                  f"Math: {payload['math_question_id']}, Leetcode: {payload['leetcode_question_id']}")
        else:
            print(f"  FAIL  {qset['name']}: {res}")

    print("\nCreating TIME_BOOST (Bidding) questions...")
    from seeding.questions import TIME_BOOST_QUESTIONS
    for boost in TIME_BOOST_QUESTIONS:
        cases = boost.pop("_cases") if "_cases" in boost else []
        code, res = api_call("POST", "/api/admin/questions", boost)
        if code == 200:
            qid = res["id"]
            api_call("POST", f"/api/admin/questions/{qid}/test-cases", cases, params={"replace": "true"})
            print(f"  OK    [{boost['difficulty']:<6}] {boost['title']} (id={qid}, +{boost['reward_value'] // 60}m bonus)")
        else:
            print(f"  FAIL  {boost['title']}: {res}")

    print("\n" + "=" * 60)
    print("Done! Ready for teams to log in and get unique Question Sets.")
    print(f"  API docs    -> {BASE_URL}/docs")
    print(f"  Leaderboard -> {BASE_URL}/api/admin/leaderboard")
    print("=" * 60)


if __name__ == "__main__":
    main()

