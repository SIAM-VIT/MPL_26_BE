import docx
import re
import json

def generate_dollar_quoted_sql():
    doc = docx.Document("d:/MPL/Programming_Question_Sets_20x3_With_3_Test_Cases.docx")
    full_text = "\n".join([p.text for p in doc.paragraphs])

    set_blocks = re.split(r"\n(?=SET\s+\d+)", full_text)

    sql_lines = []
    sql_lines.append("-- ===========================================================================")
    sql_lines.append("-- MPL PLATFORM: REFRESH ALL MAIN QUESTIONS, TEST CASES & 20 SETS")
    sql_lines.append("-- Generated with PostgreSQL Dollar-Quoting ($$..$$) for safe execution")
    sql_lines.append("-- ===========================================================================")
    sql_lines.append("\nROLLBACK;\n")
    sql_lines.append("BEGIN;\n")

    sql_lines.append("-- 1. Clear old Question Sets mapping & MAIN submissions / states")
    sql_lines.append("UPDATE question_sets SET debug_question_id = NULL, math_question_id = NULL, leetcode_question_id = NULL, is_allocated = FALSE, allocated_team_id = NULL, allocated_at = NULL;")
    sql_lines.append("DELETE FROM submission_results WHERE submission_id IN (SELECT id FROM submissions WHERE question_id IN (SELECT id FROM questions WHERE type = 'MAIN'));")
    sql_lines.append("DELETE FROM submissions WHERE question_id IN (SELECT id FROM questions WHERE type = 'MAIN');")
    sql_lines.append("DELETE FROM team_question_states WHERE question_id IN (SELECT id FROM questions WHERE type = 'MAIN');")
    sql_lines.append("DELETE FROM test_cases WHERE question_id IN (SELECT id FROM questions WHERE type = 'MAIN');")
    sql_lines.append("DELETE FROM questions WHERE type = 'MAIN';")
    sql_lines.append("DELETE FROM question_sets;\n")

    question_inserts = []
    test_case_inserts = []
    set_inserts = []
    tc_id_counter = 1001

    for block_idx, block in enumerate(set_blocks[1:], start=1):
        q_matches = list(re.finditer(r"(DEBUGGING|MATHEMATICAL PROGRAMMING|PROGRAMMING \(HARD\))\s*[-—]\s*(Q\d+:[^\n]+)", block))
        set_q_ids = {}

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
                points = 100
                set_q_ids["debug"] = q_id
            elif q_category == "MATHEMATICAL PROGRAMMING":
                q_id = 200 + block_idx
                sub_type = "MATH"
                title = f"Math: {title_clean}"
                difficulty = "MEDIUM"
                points = 100
                set_q_ids["math"] = q_id
            else:
                q_id = 300 + block_idx
                sub_type = "DSA"
                title = f"Programming: {title_clean}"
                difficulty = "HARD"
                points = 100
                set_q_ids["leetcode"] = q_id

            tc_blocks = re.split(r"Test Case \d+", q_text)
            body_before_tc = tc_blocks[0].strip()

            test_cases = []
            for tc_idx, tc_chunk in enumerate(tc_blocks[1:], start=1):
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

                test_cases.append({
                    "stdin": inp.strip(),
                    "expected_output": outp.strip(),
                    "is_hidden": False if tc_idx <= 2 else True,
                    "position": tc_idx - 1
                })

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
                    starter_code_str = f"$starter${starter_json}$starter$"

            # Using dollar quotes $qdesc$...$qdesc$ and $qtitle$...$qtitle$
            q_desc_val = f"$qdesc${body_before_tc}$qdesc$"
            q_title_val = f"$qtitle${title}$qtitle$"

            question_inserts.append(
                f"({q_id}, {q_title_val}, {q_desc_val}, '[]', 'MAIN', '{difficulty}', 0, '{sub_type}', {starter_code_str}, '[\"python\",\"c\",\"cpp\",\"java\"]', 'TRIM', {points}, 5.0, 10.0, 256000, {block_idx})"
            )

            for tc in test_cases:
                tc_id = tc_id_counter
                tc_id_counter += 1
                inp_val = f"$tc_in${tc['stdin']}$tc_in$"
                out_val = f"$tc_out${tc['expected_output']}$tc_out$"
                hidden_str = "TRUE" if tc["is_hidden"] else "FALSE"
                pos = tc["position"]
                test_case_inserts.append(
                    f"({tc_id}, {q_id}, {inp_val}, {out_val}, {hidden_str}, 1.0, {pos})"
                )

        set_inserts.append(
            f"({block_idx}, 'Set {block_idx}', {set_q_ids['debug']}, {set_q_ids['math']}, {set_q_ids['leetcode']}, FALSE)"
        )

    sql_lines.append("-- 2. INSERT 60 MAIN QUESTIONS")
    sql_lines.append("INSERT INTO questions (id, title, description, test_cases, type, difficulty, reward_value, sub_type, starter_code, allowed_languages, compare_mode, points, cpu_time_limit, wall_time_limit, memory_limit_kb, order_index)\nVALUES")
    sql_lines.append(",\n".join(question_inserts) + ";\n")

    sql_lines.append("-- 3. INSERT 180 TEST CASES")
    sql_lines.append("INSERT INTO test_cases (id, question_id, stdin, expected_output, is_hidden, weight, position)\nVALUES")
    sql_lines.append(",\n".join(test_case_inserts) + ";\n")

    sql_lines.append("-- 4. INSERT 20 QUESTION SETS")
    sql_lines.append("INSERT INTO question_sets (id, name, debug_question_id, math_question_id, leetcode_question_id, is_allocated)\nVALUES")
    sql_lines.append(",\n".join(set_inserts) + ";\n")

    sql_lines.append("-- 5. UPDATE SEQUENCES")
    sql_lines.append("SELECT setval('questions_id_seq', (SELECT COALESCE(MAX(id), 1) FROM questions));")
    sql_lines.append("SELECT setval('test_cases_id_seq', (SELECT COALESCE(MAX(id), 1) FROM test_cases));")
    sql_lines.append("SELECT setval('question_sets_id_seq', (SELECT COALESCE(MAX(id), 1) FROM question_sets));\n")

    sql_lines.append("COMMIT;\n")

    full_sql = "\n".join(sql_lines)
    with open("d:/MPL/populate_main_questions_sets.sql", "w", encoding="utf-8") as f:
        f.write(full_sql)
    print("Generated dollar-quoted SQL at d:/MPL/populate_main_questions_sets.sql")

if __name__ == "__main__":
    generate_dollar_quoted_sql()
