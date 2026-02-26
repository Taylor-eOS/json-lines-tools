import sys
import json
from pathlib import Path

def extract_texts(json_path, output_txt_path):
    json_path = Path(json_path)
    output_txt_path = Path(output_txt_path)
    if not json_path.is_file():
        print(f"Error: File not found: {json_path}", file=sys.stderr)
        return
    try:
        with json_path.open(encoding="utf-8") as fin, \
             output_txt_path.open("w", encoding="utf-8") as fout:
            for line_number, line in enumerate(fin, start=1):
                line = line.rstrip("\r\n")
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    text = obj.get("text", "")
                    if isinstance(text, str):
                        fout.write(text)
                        fout.write("\n")
                    else:
                        print(f"Warning: 'text' is not a string (line {line_number})", file=sys.stderr)
                except json.JSONDecodeError as e:
                    print(f"JSON error on line {line_number}: {e}", file=sys.stderr)
        print(f"Done. Wrote texts to: {output_txt_path}")
    except Exception as e:
        print(f"Failed: {e}", file=sys.stderr)

if __name__ == "__main__":
    default = "input.json"
    input_file = input(f"Input file ({default}): ") or default
    output_file = "output.txt"
    extract_texts(input_file, output_file)

