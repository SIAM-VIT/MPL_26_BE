import docx, re

def clean_ascii(text):
    if not text:
        return ""
    replacements = {
        "—": "-",
        "–": "-",
        "−": "-",
        "←": "<-",
        "→": "->",
        "✅": "[OK]",
        "≡": "==",
        "×": "*",
        "²": "^2",
        "³": "^3",
        "·": "-",
        "•": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "≤": "<=",
        "≥": ">=",
        "≠": "!=",
        "≈": "~=",
        "∞": "inf",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("ascii", "ignore").decode("ascii")

doc = docx.Document("d:/MPL/B.%20BIDDING_Final_Question_Bank_Indexed_No_Answers.docx")
lines = [clean_ascii(p.text).strip() for p in doc.paragraphs if p.text.strip()]
full_text = "\n".join(lines)

q_splits = list(re.finditer(r"(b\.[EMH]\d+\s*[-—–·•]?\s*Q\d+[^\n]*)", full_text))
print(f"Total bidding questions found: {len(q_splits)}")

parsed_bidding = []
id_counter = 501

for i, match in enumerate(q_splits):
    header = match.group(1).strip()
    start_pos = match.start()
    end_pos = q_splits[i+1].start() if i+1 < len(q_splits) else len(full_text)
    chunk = full_text[start_pos:end_pos].strip()

    diff = "MEDIUM"
    reward_sec = 600
    if header.startswith("b.E") or "Difficulty: Easy" in chunk:
        diff = "EASY"
        reward_sec = 300
    elif header.startswith("b.H") or "Difficulty: Hard" in chunk:
        diff = "HARD"
        reward_sec = 900

    title = f"Bidding: {header}"

    parsed_bidding.append({
        "id": id_counter,
        "title": title,
        "description": chunk,
        "difficulty": diff,
        "reward_value": reward_sec
    })
    id_counter += 1

q_inserts = []
for q in parsed_bidding:
    q_id = q["id"]
    title_val = f"$t${q['title']}$t$"
    desc_val = f"$d${q['description']}$d$"
    diff = q["difficulty"]
    reward = q["reward_value"]
    q_inserts.append(
        f"({q_id}, {title_val}, {desc_val}, '[]', 'TIME_BOOST', '{diff}', {reward}, NULL, NULL, '[]', 'TRIM', 0, 5.0, 10.0, 256000, {q_id - 500})"
    )

sql_lines = [
    "-- ===========================================================================",
    "-- MPL PLATFORM: REFRESH BIDDING / TIME_BOOST QUESTIONS (24 Questions)",
    "-- Source: B. BIDDING_Final_Question_Bank_Indexed_No_Answers.docx",
    "-- ===========================================================================",
    "\nBEGIN;\n",
    "DELETE FROM team_question_states WHERE question_id IN (SELECT id FROM questions WHERE type = 'TIME_BOOST');",
    "DELETE FROM questions WHERE type = 'TIME_BOOST';\n",
    "INSERT INTO questions (id, title, description, test_cases, type, difficulty, reward_value, sub_type, starter_code, allowed_languages, compare_mode, points, cpu_time_limit, wall_time_limit, memory_limit_kb, order_index) VALUES",
    ",\n".join(q_inserts) + ";\n",
    "SELECT setval('questions_id_seq', (SELECT COALESCE(MAX(id), 1) FROM questions));\n",
    "COMMIT;\n"
]

full_sql = "\n".join(sql_lines)
with open("d:/MPL/populate_bidding_questions.sql", "w", encoding="utf-8") as f:
    f.write(full_sql)

print(f"Generated d:/MPL/populate_bidding_questions.sql with {len(parsed_bidding)} questions.")
