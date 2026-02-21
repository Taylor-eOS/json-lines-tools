import sys
import json
from pathlib import Path

INPUT_FILE = 'input.json'

def main():
    filepath = INPUT_FILE
    input_path = validate_file_exists(filepath)
    if input_path is None:
        sys.exit(1)
    print(f"Checking file: {input_path}")
    process_jsonl_file(input_path)
    print("Scan finished.")

def validate_file_exists(filepath):
    path = Path(filepath)
    if not path.is_file():
        print(f"File not found: {filepath}")
        return None
    return path

def process_jsonl_file(path):
    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            analyze_line(line, line_num)

def analyze_line(line, line_num):
    try:
        json.loads(line)
    except json.JSONDecodeError as e:
        diagnose_error(line, line_num, e)

def diagnose_error(line, line_num, error):
    print(f"ERROR on line {line_num:5d}: {error}")
    print(f"Content : {line}")
    check_odd_quotes(line)
    check_suspicious_characters(line, error.pos)
    check_latex_commands(line)
    check_control_characters(line)

def check_odd_quotes(line):
    if '"' in line and line.count('"') % 2 == 1:
        print("  odd number of quotes, likely unescaped or missing closing \"")

def check_suspicious_characters(line, error_pos):
    start = max(0, error_pos - 10)
    end = min(len(line), error_pos + 15)
    window = line[start:end]
    suspicious = [c for c in window if ord(c) < 32 or c in '\\"']
    if suspicious:
        print(f"  suspicious char(s) near error: {repr(''.join(suspicious))}")

def check_latex_commands(line):
    if "\\mathbb" in line or "\\mathbf" in line or "\\mathcal" in line:
        print("  LaTeX command detected,  must be inside string and properly escaped")
        print("  Example correct:  \"text with \\\\mathbb{R}\"")

def check_control_characters(line):
    if any(ord(c) < 32 and c not in "\t\n\r" for c in line):
        print("  control character(s) present (not allowed outside strings)")

if __name__ == "__main__":
    main()

