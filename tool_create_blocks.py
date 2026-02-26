import json

def collapse_tables(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    inside_table = False
    table_buffer = []
    blocks = []
    for raw_line in lines:
        line = raw_line.rstrip("\n")
        if not inside_table:
            if "<table" in line:
                inside_table = True
                table_buffer.append(line.strip())
                if "</table>" in line:
                    inside_table = False
                    blocks.append("".join(table_buffer))
                    table_buffer = []
            else:
                stripped = line.strip()
                if stripped != "":
                    blocks.append(stripped)
        else:
            table_buffer.append(line.strip())
            if "</table>" in line:
                inside_table = False
                blocks.append("".join(table_buffer))
                table_buffer = []
    if inside_table and table_buffer:
        blocks.append("".join(table_buffer))
    with open(output_path, "w", encoding="utf-8") as out:
        for block in blocks:
            label = "p"
            text = block.lstrip()
            if text.startswith("#"):
                i = 0
                length = len(text)
                while i < length and text[i] == "#":
                    i += 1
                text = text[i:].lstrip()
                label = "h1"
            elif text.startswith(">"):
                i = 0
                length = len(text)
                while i < length and text[i] == ">":
                    i += 1
                text = text[i:].lstrip()
                label = "blockquote"
            obj = {"label": label, "text": text}
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")

def main():
    input_path = "input.txt"
    output_path = "input.json"
    collapse_tables(input_path, output_path)

if __name__ == "__main__":
    main()
