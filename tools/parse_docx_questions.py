import docx
import re
import json
import os

def parse_docx():
    doc = docx.Document("d:/MPL/Programming_Question_Sets_20x3_With_3_Test_Cases.docx")
    full_text = "\n".join([p.text for p in doc.paragraphs])

    set_blocks = re.split(r"\n(?=SET\s+\d+)", full_text)
    print(f"Total set blocks found: {len(set_blocks) - 1}")

    all_sets = []

    for block_idx, block in enumerate(set_blocks[1:], start=1):
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        set_name = f"Set {block_idx}"
        
        q_matches = list(re.finditer(r"(DEBUGGING|MATHEMATICAL PROGRAMMING|PROGRAMMING \(HARD\))\s*[-—]\s*(Q\d+:[^\n]+)", block))
        
        set_questions = []
        for i, match in enumerate(q_matches):
            q_category = match.group(1).strip()
            q_raw_title = match.group(2).strip()
            start_pos = match.start()
            end_pos = q_matches[i+1].start() if i+1 < len(q_matches) else len(block)
            q_text = block[start_pos:end_pos].strip()

            # Clean Title
            title_clean = q_raw_title
            # e.g. Q1: Palindrome Checker -> Palindrome Checker
            if ":" in title_clean:
                title_clean = title_clean.split(":", 1)[1].strip()

            # Parse sub-type and category
            if q_category == "DEBUGGING":
                sub_type = "DEBUGGING"
                prefix = f"Debug: {title_clean}"
            elif q_category == "MATHEMATICAL PROGRAMMING":
                sub_type = "MATH"
                prefix = f"Math: {title_clean}"
            else:
                sub_type = "DSA"
                prefix = f"Programming: {title_clean}"

            # Extract Test Cases:
            # Pattern: Test Case 1 ... Input ... Expected Output ...
            test_cases = []
            tc_blocks = re.split(r"Test Case \d+", q_text)
            
            # The body before test cases is description / starter code
            body_before_tc = tc_blocks[0]

            for tc_idx, tc_chunk in enumerate(tc_blocks[1:], start=1):
                # Look for Input and Expected Output
                # Format:
                # Input\n<input text>\nExpected Output\n<output text>
                m_io = re.search(r"Input\s*\n(.*?)\nExpected Output\s*\n(.*)", tc_chunk, re.DOTALL)
                if m_io:
                    inp = m_io.group(1).strip()
                    outp = m_io.group(2).strip()
                    # Clean any trailing sections if any
                    outp = outp.split("\n\n")[0].strip()
                    test_cases.append({
                        "case_num": tc_idx,
                        "stdin": inp,
                        "expected_output": outp,
                        "is_hidden": False if tc_idx <= 2 else True
                    })
                else:
                    print(f"WARNING: Could not parse TC {tc_idx} in Set {block_idx} - {q_category} - {q_raw_title}")
                    print("Chunk snippet:", repr(tc_chunk[:200]))

            # Starter code for debugging questions:
            starter_code = None
            if sub_type == "DEBUGGING":
                # Find python code block between "Concept:" or title and "print(" or "IndexError" or "Platform Format"
                # In body_before_tc
                lines_body = body_before_tc.split("\n")
                code_lines = []
                capturing = False
                for line in lines_body:
                    if line.strip().startswith("def ") or line.strip().startswith("class "):
                        capturing = True
                    if capturing:
                        if line.strip().startswith("print(") or line.strip().startswith("Platform Format") or "IndexError" in line or "Error" in line or "Sample Test" in line:
                            break
                        code_lines.append(line)
                if code_lines:
                    starter_py = "\n".join(code_lines).strip()
                    starter_code = json.dumps({"python": starter_py})

            # Description
            description = body_before_tc.strip()

            set_questions.append({
                "set_num": block_idx,
                "category": q_category,
                "sub_type": sub_type,
                "raw_title": q_raw_title,
                "title": prefix,
                "description": description,
                "starter_code": starter_code,
                "test_cases": test_cases
            })

        all_sets.append({
            "set_num": block_idx,
            "set_name": set_name,
            "questions": set_questions
        })

    return all_sets

if __name__ == "__main__":
    sets = parse_docx()
    print(f"Successfully parsed {len(sets)} sets.")
    total_q = sum(len(s["questions"]) for s in sets)
    total_tc = sum(len(q["test_cases"]) for s in sets for q in s["questions"])
    print(f"Total questions: {total_q}, Total test cases: {total_tc}")
    
    with open("d:/MPL/parsed_questions_data.json", "w", encoding="utf-8") as f:
        json.dump(sets, f, indent=2)
    print("Saved to d:/MPL/parsed_questions_data.json")
