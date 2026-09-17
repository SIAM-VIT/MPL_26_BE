import docx, re, json

def clean_ascii(text):
    if not text:
        return ""
    replacements = {
        "—": "-",
        "–": "-",
        "←": "<-",
        "→": "->",
        "✅": "[OK]",
        "≡": "==",
        "×": "*",
        "²": "^2",
        "³": "^3",
        "⌊": "",
        "⌋": "",
        "π": "pi",
        "Σ": "sum",
        "√": "sqrt",
        "Δ": "Delta",
        "μ": "mean",
        "•": "*",
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
    text = text.encode("ascii", "ignore").decode("ascii")
    return text

doc = docx.Document("d:/MPL/Programming_Question_Sets_20x3_With_3_Test_Cases.docx")
full_text = "\n".join([clean_ascii(p.text) for p in doc.paragraphs])
set_blocks = re.split(r"\n(?=SET\s+\d+)", full_text)

def generate_clean_set_query(set_idx):
    block = set_blocks[set_idx]
    q_matches = list(re.finditer(r"(DEBUGGING|MATHEMATICAL PROGRAMMING|PROGRAMMING \(HARD\))\s*[-—]\s*(Q\d+:[^\n]+)", block))

    q_inserts = []
    tc_inserts = []

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
            q_id = 100 + set_idx
            sub_type = "DEBUGGING"
            title = f"Debug: {title_clean}"
            difficulty = "EASY"
        elif q_category == "MATHEMATICAL PROGRAMMING":
            q_id = 200 + set_idx
            sub_type = "MATH"
            title = f"Math: {title_clean}"
            difficulty = "MEDIUM"
        else:
            q_id = 300 + set_idx
            sub_type = "CODING"  # ENUM is 'CODING'
            title = f"Programming: {title_clean}"
            difficulty = "HARD"

        tc_blocks = re.split(r"Test Case \d+", q_text)
        body_before_tc = clean_ascii(tc_blocks[0].strip())

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
            f"({q_id}, {q_title_val}, {q_desc_val}, '[]', 'MAIN', '{difficulty}', 0, '{sub_type}', {starter_code_str}, '[\"python\",\"c\",\"cpp\",\"java\"]', 'TRIM', 100, 5.0, 10.0, 256000, {set_idx})"
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
            inp_val = f"$i${clean_ascii(inp.strip())}$i$"
            out_val = f"$o${clean_ascii(outp.strip())}$o$"
            hidden_str = "FALSE" if tc_counter <= 2 else "TRUE"
            pos = tc_counter - 1
            tc_inserts.append(
                f"({tc_id}, {q_id}, {inp_val}, {out_val}, {hidden_str}, 1.0, {pos})"
            )
            tc_counter += 1

    sql = f"""-- ==================== SET {set_idx} ====================
INSERT INTO questions (id, title, description, test_cases, type, difficulty, reward_value, sub_type, starter_code, allowed_languages, compare_mode, points, cpu_time_limit, wall_time_limit, memory_limit_kb, order_index) VALUES
{",".join(q_inserts)};

INSERT INTO test_cases (id, question_id, stdin, expected_output, is_hidden, weight, position) VALUES
{",".join(tc_inserts)};

INSERT INTO question_sets (id, name, debug_question_id, math_question_id, leetcode_question_id, is_allocated) VALUES
({set_idx}, 'Set {set_idx}', {100 + set_idx}, {200 + set_idx}, {300 + set_idx}, FALSE);
"""
    return sql

all_sets_sql = [generate_clean_set_query(i) for i in range(1, 21)]

for idx, s in enumerate(all_sets_sql, start=1):
    with open(f"d:/MPL/set_{idx}.sql", "w", encoding="utf-8") as f:
        f.write(s)

print("Generated all 20 corrected sets with 'CODING' enum!")
