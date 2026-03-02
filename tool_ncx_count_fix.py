import sys
from pathlib import Path

input_file = "input.ncx"

def renumber_text_headings(input_path: Path, output_path: Path | None = None) -> None:
    if not input_path.exists():
        print(f"Error: File {input_path} does not exist.")
        sys.exit(1)
    text = input_path.read_text(encoding="utf-8")
    open_tag = "<text>"
    close_tag = "</text>"
    parts = text.split(open_tag)
    counter = 1
    substitutions = 0
    result_parts = [parts[0]]
    for part in parts[1:]:
        end_idx = part.find(close_tag)
        if end_idx == -1:
            result_parts.append(open_tag + part)
            continue
        content = part[:end_idx]
        after = part[end_idx:]
        if content.isdigit():
            result_parts.append(open_tag + str(counter) + after)
            counter += 1
            substitutions += 1
        else:
            result_parts.append(open_tag + part)
    new_text = "".join(result_parts)
    if substitutions == 0:
        print("No numeric <text> elements were found.")
    else:
        print(f"Renumbered {substitutions} <text> elements (now 1 to {substitutions}).")
    output_file = output_path or input_path
    output_file.write_text(new_text, encoding="utf-8")
    print(f"Result written to {output_file}")

if __name__ == "__main__":
    renumber_text_headings(Path(input_file))

