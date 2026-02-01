import os
import re
import json
from html import unescape

INPUT_FILE = input("Input file: ") or "input.json"
base, ext = os.path.splitext(INPUT_FILE)
if not ext:
    candidate = INPUT_FILE + ".json"
    if os.path.isfile(candidate):
        INPUT_FILE = candidate
    else:
        if not os.path.isfile(INPUT_FILE):
            print(f"Error: Neither '{INPUT_FILE}' nor '{candidate}' exists.")
            exit(1)
else:
    if not os.path.isfile(INPUT_FILE):
        print(f"Error: File '{INPUT_FILE}' does not exist.")
        exit(1)
OUTPUT_FILE = base + ".txt"

def clean_text_block(raw_text):
    if not raw_text:
        return ""
    text = unescape(raw_text)
    text = re.sub(r'<sup[^>]*>.*?</sup>', '', text, flags=re.IGNORECASE|re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s+([.!?])', r'\1', text)
    return text

def should_insert_blank_before(label):
    return label in ('h1', 'h2')

def process_jsonl_to_text(input_path, output_path):
    first_block = True
    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            label = obj.get('label', '')
            raw_text = obj.get('text', '')
            text = clean_text_block(raw_text)
            if not text:
                continue
            if should_insert_blank_before(label):
                if not first_block:
                    fout.write('\n')
                fout.write(text + '\n')
            else:
                fout.write(text + '\n')
            first_block = False

def main():
    process_jsonl_to_text(INPUT_FILE, OUTPUT_FILE)
    print(f"Clean text written to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()

