import sys
import json
from pathlib import Path

INPUT_FILE = 'input.json'

def diagnose_jsonl_file(filepath):
    path = Path(filepath)
    if not path.is_file():
        print(f"File not found: {filepath}")
        return
    print(f"Checking file: {path}")
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                continue
            except json.JSONDecodeError as e:
                print(f"ERROR on line {i:5d}: {e}")
                print(f"Content : {line}")
                col = e.pos
                if col < len(line):
                    print("Position : " + " " * col + "^")
                else:
                    print("Position : (at or after end of line)")
                if '"' in line and line.count('"') % 2 == 1:
                    print("→ odd number of quotes → likely unescaped or missing closing \"")
                if "\\" in line:
                    before = line[:col]
                    after = line[col-10:col+15] if col >= 10 else line[:col+15]
                    if "\\u" not in before and "\\x" not in before:
                        suspicious = [c for c in after if ord(c) < 32 or c in "\\\""]
                        if suspicious:
                            print(f"→ suspicious char(s) near error: {repr(''.join(suspicious))}")
                if "\\mathbb" in line or "\\mathbf" in line or "\\mathcal" in line:
                    print("→ LaTeX command detected → must be inside string and properly escaped")
                    print("   Example correct:  \"text with \\\\mathbb{R}\"")
                if any(ord(c) < 32 and c not in "\t\n\r" for c in line):
                    print("→ control character(s) present (not allowed outside strings)")
                print()
    print("Scan finished.")

if __name__ == "__main__":
    diagnose_jsonl_file(INPUT_FILE)

