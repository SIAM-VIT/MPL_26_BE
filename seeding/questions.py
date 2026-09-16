"""Demo teams and the three demo MAIN questions with their test cases.

Extracted verbatim from seed.py; starter code blobs live in starters.py.
Each question dict carries a transient "_cases" key that seed.py pops and
posts to the test-cases endpoint.
"""
import json

from seeding.starters import (
    DEBUG_STARTER, MATH_STARTER, LEETCODE_STARTER,
    DEBUG_STARTER_2, MATH_STARTER_2, LEETCODE_STARTER_2,
    DEBUG_STARTER_3, MATH_STARTER_3, LEETCODE_STARTER_3,
)

TEAMS = [
    {"name": "Team Alpha", "passcode": "alpha123"},
    {"name": "Team Beta", "passcode": "beta123"},
    {"name": "Team Gamma", "passcode": "gamma123"},
]

def q(title, description, sub_type, points, starter, cases, compare_mode="TRIM",
      difficulty="MEDIUM", order=0):
    return {
        "title": title,
        "description": description,
        "test_cases": "[]",
        "type": "MAIN",
        "difficulty": difficulty,
        "reward_value": 0,
        "sub_type": sub_type,
        "starter_code": json.dumps(starter),
        "allowed_languages": json.dumps(["python", "c", "cpp", "java"]),
        "compare_mode": compare_mode,
        "points": points,
        "cpu_time_limit": 5.0,
        "wall_time_limit": 10.0,
        "memory_limit_kb": 256000,
        "order_index": order,
        "_cases": cases,
    }


QUESTIONS = [
    # ── Set 1 Questions ──────────────────────────────────────────────────────
    q(
        "Debug: Sum 1..N",
        "The program below should print the sum of every integer from 1 to n.\n"
        "It runs without crashing, but the answer is wrong. Find the bug and fix it.\n\n"
        "Input:  one integer n\n"
        "Output: the sum of 1..n",
        "DEBUGGING",
        300,
        DEBUG_STARTER,
        [
            {"stdin": "5", "expected_output": "15", "is_hidden": False, "position": 0},
            {"stdin": "10", "expected_output": "55", "is_hidden": True, "position": 1},
            {"stdin": "1", "expected_output": "1", "is_hidden": True, "position": 2},
            {"stdin": "100", "expected_output": "5050", "is_hidden": True, "position": 3},
        ],
        compare_mode="TRIM",
        difficulty="EASY",
        order=1,
    ),
    q(
        "Math: Compound Interest",
        "Compute compound interest:  A = P * (1 + r)^t\n\n"
        "Input:  P, r and t (one per line)\n"
        "Output: A rounded to exactly 2 decimal places",
        "MATH",
        400,
        MATH_STARTER,
        [
            {"stdin": "1000\n0.05\n2", "expected_output": "1102.50", "is_hidden": False, "position": 0},
            {"stdin": "500\n0.1\n3", "expected_output": "665.50", "is_hidden": True, "position": 1},
            {"stdin": "1000\n0\n5", "expected_output": "1000.00", "is_hidden": True, "position": 2},
            {"stdin": "250\n0.07\n10", "expected_output": "491.79", "is_hidden": True, "position": 3},
        ],
        compare_mode="FLOAT",
        difficulty="MEDIUM",
        order=2,
    ),
    q(
        "Coding: Two Sum",
        "Given an array and a target, print the two 0-based indices i j (i < j)\n"
        "whose values add up to the target.\n\n"
        "Input:  line 1: n\n"
        "        line 2: n space-separated integers\n"
        "        line 3: target\n"
        "Output: the two indices separated by a space",
        "CODING",
        500,
        LEETCODE_STARTER,
        [
            {"stdin": "4\n2 7 11 15\n9", "expected_output": "0 1", "is_hidden": False, "position": 0},
            {"stdin": "3\n3 2 4\n6", "expected_output": "1 2", "is_hidden": True, "position": 1},
            {"stdin": "5\n1 1 1 1 1\n2", "expected_output": "0 1", "is_hidden": True, "position": 2},
            {"stdin": "6\n10 20 30 40 50 60\n100", "expected_output": "3 5", "is_hidden": True, "position": 3},
        ],
        compare_mode="TRIM",
        difficulty="HARD",
        order=3,
    ),

    # ── Set 2 Questions ──────────────────────────────────────────────────────
    q(
        "Debug: Factorial Loop",
        "The program below should compute the factorial of non-negative integer n (n!).\n"
        "It runs without crashing, but the answer is wrong. Find the bug and fix it.\n\n"
        "Input:  one integer n (0 <= n <= 12)\n"
        "Output: the value of n!",
        "DEBUGGING",
        300,
        DEBUG_STARTER_2,
        [
            {"stdin": "5", "expected_output": "120", "is_hidden": False, "position": 0},
            {"stdin": "0", "expected_output": "1", "is_hidden": True, "position": 1},
            {"stdin": "1", "expected_output": "1", "is_hidden": True, "position": 2},
            {"stdin": "6", "expected_output": "720", "is_hidden": True, "position": 3},
        ],
        compare_mode="TRIM",
        difficulty="EASY",
        order=4,
    ),
    q(
        "Math: Circle Geometry",
        "Given radius r, compute the area (pi * r^2) and circumference (2 * pi * r).\n"
        "Use pi = 3.141592653589793.\n\n"
        "Input:  radius r (float)\n"
        "Output: Line 1: Area rounded to 2 decimals\n"
        "        Line 2: Circumference rounded to 2 decimals",
        "MATH",
        400,
        MATH_STARTER_2,
        [
            {"stdin": "5.0", "expected_output": "78.54\n31.42", "is_hidden": False, "position": 0},
            {"stdin": "1.0", "expected_output": "3.14\n6.28", "is_hidden": True, "position": 1},
            {"stdin": "10.5", "expected_output": "346.36\n65.97", "is_hidden": True, "position": 2},
            {"stdin": "0.0", "expected_output": "0.00\n0.00", "is_hidden": True, "position": 3},
        ],
        compare_mode="TRIM",
        difficulty="MEDIUM",
        order=5,
    ),
    q(
        "Coding: Maximum Subarray",
        "Given an integer array nums, find the subarray with the largest sum and print its sum.\n\n"
        "Input:  Line 1: n\n"
        "        Line 2: n space-separated integers\n"
        "Output: the maximum subarray sum",
        "CODING",
        500,
        LEETCODE_STARTER_2,
        [
            {"stdin": "9\n-2 1 -3 4 -1 2 1 -5 4", "expected_output": "6", "is_hidden": False, "position": 0},
            {"stdin": "1\n1", "expected_output": "1", "is_hidden": True, "position": 1},
            {"stdin": "5\n5 4 -1 7 8", "expected_output": "23", "is_hidden": True, "position": 2},
            {"stdin": "4\n-3 -2 -1 -4", "expected_output": "-1", "is_hidden": True, "position": 3},
        ],
        compare_mode="TRIM",
        difficulty="HARD",
        order=6,
    ),

    # ── Set 3 Questions ──────────────────────────────────────────────────────
    q(
        "Debug: Reverse Words",
        "Given a space-separated sentence, reverse the characters in each word while preserving word order.\n"
        "Find and fix the bug in the solution.\n\n"
        "Input:  a line of words\n"
        "Output: words with characters reversed, separated by space",
        "DEBUGGING",
        300,
        DEBUG_STARTER_3,
        [
            {"stdin": "hello world", "expected_output": "olleh dlrow", "is_hidden": False, "position": 0},
            {"stdin": "code fast", "expected_output": "edoc tsaf", "is_hidden": True, "position": 1},
            {"stdin": "a", "expected_output": "a", "is_hidden": True, "position": 2},
            {"stdin": "apple pie", "expected_output": "elppa eip", "is_hidden": True, "position": 3},
        ],
        compare_mode="TRIM",
        difficulty="EASY",
        order=7,
    ),
    q(
        "Math: Fibonacci Sequence",
        "Compute the n-th Fibonacci number where F_0 = 0, F_1 = 1, and F_n = F_{n-1} + F_{n-2}.\n\n"
        "Input:  n (0 <= n <= 30)\n"
        "Output: F_n",
        "MATH",
        400,
        MATH_STARTER_3,
        [
            {"stdin": "6", "expected_output": "8", "is_hidden": False, "position": 0},
            {"stdin": "0", "expected_output": "0", "is_hidden": True, "position": 1},
            {"stdin": "1", "expected_output": "1", "is_hidden": True, "position": 2},
            {"stdin": "10", "expected_output": "55", "is_hidden": True, "position": 3},
        ],
        compare_mode="TRIM",
        difficulty="MEDIUM",
        order=8,
    ),
    q(
        "Coding: Majority Element",
        "Given an array nums of size n, return the majority element (the element that appears more than floor(n / 2) times).\n\n"
        "Input:  Line 1: n\n"
        "        Line 2: n space-separated integers\n"
        "Output: the majority element",
        "CODING",
        500,
        LEETCODE_STARTER_3,
        [
            {"stdin": "3\n3 2 3", "expected_output": "3", "is_hidden": False, "position": 0},
            {"stdin": "7\n2 2 1 1 1 2 2", "expected_output": "2", "is_hidden": True, "position": 1},
            {"stdin": "1\n99", "expected_output": "99", "is_hidden": True, "position": 2},
            {"stdin": "5\n6 6 6 7 7", "expected_output": "6", "is_hidden": True, "position": 3},
        ],
        compare_mode="TRIM",
        difficulty="HARD",
        order=9,
    ),
]

# Mapping sets to question titles:
QUESTION_SETS_CONFIG = [
    {
        "name": "Set 1",
        "debug": "Debug: Sum 1..N",
        "math": "Math: Compound Interest",
        "leetcode": "Coding: Two Sum",
    },
    {
        "name": "Set 2",
        "debug": "Debug: Factorial Loop",
        "math": "Math: Circle Geometry",
        "leetcode": "Coding: Maximum Subarray",
    },
    {
        "name": "Set 3",
        "debug": "Debug: Reverse Words",
        "math": "Math: Fibonacci Sequence",
        "leetcode": "Coding: Majority Element",
    },
]


def boost_q(title, description, difficulty, reward_seconds, cases):
    return {
        "title": title,
        "description": description,
        "test_cases": "[]",
        "type": "TIME_BOOST",
        "difficulty": difficulty,
        "reward_value": reward_seconds,
        "points": reward_seconds,
        "sub_type": "MATH",
        "starter_code": "{}",
        "allowed_languages": json.dumps(["python", "c", "cpp", "java"]),
        "compare_mode": "TRIM",
        "cpu_time_limit": 5.0,
        "wall_time_limit": 10.0,
        "memory_limit_kb": 256000,
        "order_index": 0,
        "_cases": cases,
    }


TIME_BOOST_QUESTIONS = [
    # ── Easy (+5m / 300s) ───────────────────────────────────────────────────
    boost_q(
        "Time Boost (Easy): Palindrome Check",
        "Determine if a given string is a palindrome (reads the same backward as forward).\n"
        "Input:  a single string\n"
        "Output: 'YES' if palindrome, 'NO' otherwise",
        "EASY",
        300,
        [
            {"stdin": "racecar", "expected_output": "YES", "is_hidden": False, "position": 0},
            {"stdin": "hello", "expected_output": "NO", "is_hidden": True, "position": 1},
        ],
    ),
    boost_q(
        "Time Boost (Easy): Count Vowels",
        "Count the total number of vowels (a, e, i, o, u case-insensitive) in a sentence.\n"
        "Input:  a line of text\n"
        "Output: integer count of vowels",
        "EASY",
        300,
        [
            {"stdin": "programming league", "expected_output": "7", "is_hidden": False, "position": 0},
            {"stdin": "xyz", "expected_output": "0", "is_hidden": True, "position": 1},
        ],
    ),

    # ── Medium (+10m / 600s) ────────────────────────────────────────────────
    boost_q(
        "Time Boost (Medium): Prime Number Range",
        "Given integer N, count how many prime numbers exist between 2 and N inclusive.\n"
        "Input:  integer N (2 <= N <= 10000)\n"
        "Output: count of prime numbers",
        "MEDIUM",
        600,
        [
            {"stdin": "10", "expected_output": "4", "is_hidden": False, "position": 0},
            {"stdin": "30", "expected_output": "10", "is_hidden": True, "position": 1},
        ],
    ),
    boost_q(
        "Time Boost (Medium): Anagram Grouping",
        "Given two space-separated words, output 'ANAGRAM' if they contain identical characters, else 'NOT ANAGRAM'.\n"
        "Input:  two space-separated words\n"
        "Output: ANAGRAM or NOT ANAGRAM",
        "MEDIUM",
        600,
        [
            {"stdin": "silent listen", "expected_output": "ANAGRAM", "is_hidden": False, "position": 0},
            {"stdin": "apple pale", "expected_output": "NOT ANAGRAM", "is_hidden": True, "position": 1},
        ],
    ),

    # ── Hard (+15m / 900s) ──────────────────────────────────────────────────
    boost_q(
        "Time Boost (Hard): Longest Consecutive Sequence",
        "Given an array of integers, find the length of the longest consecutive elements sequence.\n"
        "Input:  Line 1: N\n        Line 2: N space-separated integers\n"
        "Output: length of longest consecutive elements sequence",
        "HARD",
        900,
        [
            {"stdin": "6\n100 4 200 1 3 2", "expected_output": "4", "is_hidden": False, "position": 0},
            {"stdin": "10\n0 3 7 2 5 8 4 6 0 1", "expected_output": "9", "is_hidden": True, "position": 1},
        ],
    ),
]


def challenge_q(title, description, difficulty="HARD", reward=100):
    return {
        "title": title,
        "description": description,
        "test_cases": "[]",
        "type": "CHALLENGE",
        "difficulty": difficulty,
        "reward_value": reward,
        "points": reward,
        "sub_type": "CODING",
        "starter_code": "{}",
        "allowed_languages": json.dumps(["python", "c", "cpp", "java"]),
        "compare_mode": "TRIM",
        "cpu_time_limit": 5.0,
        "wall_time_limit": 10.0,
        "memory_limit_kb": 256000,
        "order_index": 0,
    }


CHALLENGE_QUESTIONS = [
    challenge_q(
        "Challenge: Longest Balanced Parentheses",
        "Given a string containing just the characters '(' and ')', find the length of the longest valid (well-formed) parentheses substring.\n\n"
        "Input:  a string of parentheses\n"
        "Output: maximum length of valid parentheses substring\n\n"
        "First team in the 1v1 / 1v1v1 battle to demonstrate working code and volunteer-verify wins 100 points from the opponents!",
        "HARD",
        100,
    ),
    challenge_q(
        "Challenge: Shortest Path in Obstacle Grid",
        "You are given an m x n integer matrix grid where grid[i][j] = 0 (empty) or 1 (obstacle). "
        "Find the minimum steps to walk from top-left (0, 0) to bottom-right (m-1, n-1).\n\n"
        "Input:  Line 1: m n\n        Next m lines: n space-separated integers\n"
        "Output: minimum steps or -1 if unreachable",
        "HARD",
        100,
    ),
    challenge_q(
        "Challenge: Maximum XOR of Two Numbers",
        "Given an integer array nums, return the maximum result of nums[i] XOR nums[j], where 0 <= i <= j < n.\n\n"
        "Input:  Line 1: n\n        Line 2: n space-separated integers\n"
        "Output: maximum XOR value",
        "HARD",
        100,
    ),
    challenge_q(
        "Challenge: Matrix Transpose & Trace",
        "Given an N x N matrix, calculate its transpose and the sum of its diagonal elements (trace).\n\n"
        "Input:  Line 1: N\n        Next N lines: N space-separated integers\n"
        "Output: Line 1: trace\n        Next N lines: transposed matrix",
        "MEDIUM",
        100,
    ),
]


