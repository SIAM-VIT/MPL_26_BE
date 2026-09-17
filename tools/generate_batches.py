import docx, re, json

doc = docx.Document("d:/MPL/Programming_Question_Sets_20x3_With_3_Test_Cases.docx")
full_text = "\n".join([p.text for p in doc.paragraphs])
set_blocks = re.split(r"\n(?=SET\s+\d+)", full_text)

def build_batch(start_set, end_set, is_first=False, is_last=False):
    lines = []
    if is_first:
        lines.append("ROLLBACK;")
        lines.append("BEGIN;")
        lines.append("-- 1. Clear old Question Sets & MAIN data")
        lines.append("UPDATE question_sets SET debug_question_id = NULL, math_question_id = NULL, leetcode_question_id = NULL, is_allocated = FALSE, allocated_team_id = NULL, allocated_at = NULL;")
        lines.append("DELETE FROM submission_results WHERE submission_id IN (SELECT id FROM submissions WHERE question_id IN (SELECT id FROM questions WHERE type = 'MAIN'));")
        lines.append("DELETE FROM submissions WHERE question_id IN (SELECT id FROM questions WHERE type = 'MAIN');")
        lines.append("DELETE FROM team_question_states WHERE question_id IN (SELECT id FROM questions WHERE type = 'MAIN');")
        lines.append("DELETE FROM test_cases WHERE question_id IN (SELECT id FROM questions WHERE type = 'MAIN');")
        lines.append("DELETE FROM questions WHERE type = 'MAIN';")
        lines.append("DELETE FROM question_sets;\n")

    q_inserts = []
    tc_inserts = []

    for block_idx in range(start_set, end_set + 1):
        block = set_blocks[block_idx]
        q_matches = list(re.finditer(r"(DEBUGGING|MATHEMATICAL PROGRAMMING|PROGRAMMING \(HARD\))\s*[-—]\s*(Q\d+:[^\n]+)", block))

        for i, match in enumerate(q_matches):
            q_category = match.group(1).strip()
            q_raw_title = match.group(2).strip()
            start_pos = match.start()
            end_pos = q_matches[i+1].start() if i+1 < len(q_matches) else len(block)
            q_text = block[start_pos:end_pos].strip()

            title_clean = q_raw_title
            if ":" in title_clean:
                title_clean = title_clean.split(":", 1)[1].strip()

            if q_category == "DEBUGGING":
                q_id = 100 + block_idx
                sub_type = "DEBUGGING"
                title = f"Debug: {title_clean}"
                difficulty = "EASY"
            elif q_category == "MATHEMATICAL PROGRAMMING":
                q_id = 200 + block_idx
                sub_type = "MATH"
                title = f"Math: {title_clean}"
                difficulty = "MEDIUM"
            else:
                q_id = 300 + block_idx
                sub_type = "DSA"
                title = f"Programming: {title_clean}"
                difficulty = "HARD"

            tc_blocks = re.split(r"Test Case \d+", q_text)
            body_before_tc = tc_blocks[0].strip()

            starter_code_str = "NULL"
            if sub_type == "DEBUGGING":
                lines_body = body_before_tc.split("\n")
                code_lines = []
                capturing = False
                for line in lines_body:
                    line_s = line.strip()
                    if line_s.startswith("def ") or line_s.startswith("class "):
                        capturing = True
                    if capturing:
                        if line_s.startswith("print(") or line_s.startswith("Platform Format") or line_s.startswith("IndexError") or line_s.startswith("Sample Test Cases") or line_s.startswith("Task:"):
                            break
                        code_lines.append(line)
                if code_lines:
                    starter_py = "\n".join(code_lines).strip()
                    starter_json = json.dumps({"python": starter_py})
                    starter_code_str = f"$s${starter_json}$s$"

            q_desc_val = f"$d${body_before_tc}$d$"
            q_title_val = f"$t${title}$t$"

            q_inserts.append(
                f"({q_id}, {q_title_val}, {q_desc_val}, '[]', 'MAIN', '{difficulty}', 0, '{sub_type}', {starter_code_str}, '[\"python\",\"c\",\"cpp\",\"java\"]', 'TRIM', 100, 5.0, 10.0, 256000, {block_idx})"
            )

            tc_counter = 1
            for tc_chunk in tc_blocks[1:]:
                lines_tc = [line.strip() for line in tc_chunk.strip().split("\n") if line.strip()]
                inp = ""
                outp = ""
                state = None
                for line in lines_tc:
                    if line.lower() == "input":
                        state = "input"
                        continue
                    elif line.lower() == "expected output":
                        state = "output"
                        continue
                    if state == "input":
                        inp += (line if not inp else "\n" + line)
                    elif state == "output":
                        outp += (line if not outp else "\n" + line)

                tc_id = q_id * 10 + tc_counter
                inp_val = f"$i${inp.strip()}$i$"
                out_val = f"$o${outp.strip()}$o$"
                hidden_str = "FALSE" if tc_counter <= 2 else "TRUE"
                pos = tc_counter - 1
                tc_inserts.append(
                    f"({tc_id}, {q_id}, {inp_val}, {out_val}, {hidden_str}, 1.0, {pos})"
                )
                tc_counter += 1

    lines.append(f"-- INSERT QUESTIONS (Sets {start_set} to {end_set})")
    lines.append("INSERT INTO questions (id, title, description, test_cases, type, difficulty, reward_value, sub_type, starter_code, allowed_languages, compare_mode, points, cpu_time_limit, wall_time_limit, memory_limit_kb, order_index) VALUES")
    lines.append(",\n".join(q_inserts) + ";\n")

    lines.append(f"-- INSERT TEST CASES (Sets {start_set} to {end_set})")
    lines.append("INSERT INTO test_cases (id, question_id, stdin, expected_output, is_hidden, weight, position) VALUES")
    lines.append(",\n".join(tc_inserts) + ";\n")

    if is_last:
        set_inserts = []
        for s_idx in range(1, 21):
            set_inserts.append(f"({s_idx}, 'Set {s_idx}', {100 + s_idx}, {200 + s_idx}, {300 + s_idx}, FALSE)")
        lines.append("-- INSERT 20 QUESTION SETS")
        lines.append("INSERT INTO question_sets (id, name, debug_question_id, math_question_id, leetcode_question_id, is_allocated) VALUES")
        lines.append(",\n".join(set_inserts) + ";\n")
        lines.append("-- UPDATE SEQUENCES")
        lines.append("SELECT setval('questions_id_seq', (SELECT COALESCE(MAX(id), 1) FROM questions));")
        lines.append("SELECT setval('test_cases_id_seq', (SELECT COALESCE(MAX(id), 1) FROM test_cases));")
        lines.append("SELECT setval('question_sets_id_seq', (SELECT COALESCE(MAX(id), 1) FROM question_sets));\n")
        lines.append("COMMIT;")

    return "\n".join(lines)

b1 = build_batch(1, 7, is_first=True, is_last=False)
b2 = build_batch(8, 14, is_first=False, is_last=False)
b3 = build_batch(15, 20, is_first=False, is_last=True)

with open("d:/MPL/batch1.sql", "w", encoding="utf-8") as f: f.write(b1)
with open("d:/MPL/batch2.sql", "w", encoding="utf-8") as f: f.write(b2)
with open("d:/MPL/batch3.sql", "w", encoding="utf-8") as f: f.write(b3)
print("Saved batch1, batch2, batch3")
