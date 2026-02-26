import json

def read_input_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print("Reading input:", path, "lines:", len(lines))
    return lines

def collect_blocks(lines):
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
    print("Blocks detected:", len(blocks))
    return blocks

def classify_block(block):
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
    return {"label": label, "text": text}

def write_output(path, blocks):
    with open(path, "w", encoding="utf-8") as out:
        count = 0
        for block in blocks:
            obj = classify_block(block)
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            count += 1
    print("Written output:", path, "entries:", count)

def check_output(path):
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'“”«»‹›-")
    allowed_prefixes = ("<table", "<sup", "<span")
    warnings = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except Exception:
                print("Warning: malformed json line, skipping:", line[:80])
                warnings += 1
                continue
            t = obj.get("text", "").lstrip()
            if t:
                if t.startswith(allowed_prefixes):
                    continue
                c = t[0]
                if c not in allowed:
                    print("Warning: unusual start character: ", repr(c), "| text:", t[:80])
                    warnings += 1
    print("Warnings:", warnings)

def collapse_tables(input_path, output_path):
    lines = read_input_lines(input_path)
    blocks = collect_blocks(lines)
    write_output(output_path, blocks)
    check_output(output_path)
    print("Done successfully")

def main():
    input_path = "input.txt"
    output_path = "input.json"
    collapse_tables(input_path, output_path)

if __name__ == "__main__":
    main()

