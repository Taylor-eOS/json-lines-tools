import sys
import tkinter as tk
from tkinter import filedialog
import nltk
import os

def load_wordlist():
    try:
        nltk.data.find('corpora/words')
    except LookupError:
        nltk.download('words', quiet=True)
    from nltk.corpus import words
    return set(w.lower() for w in words.words() if w.isalpha())

def read_input():
    if not sys.stdin.isatty():
        return sys.stdin.read(), None
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Select text file",
        filetypes=[("Text files", "*.txt *.json *.md"), ("All files", "*.*")]
    )
    root.destroy()
    if not path:
        sys.exit(0)
    with open(path, "r", encoding="utf-8") as f:
        return f.read(), path

def get_context(tokens, start, end, width=10):
    start_idx = max(0, start - width)
    end_idx = min(len(tokens), end + width)
    return ' '.join(tokens[start_idx:end_idx])

def find_all_candidates(lines, wordlist, max_seq):
    all_candidates = {}
    for line_idx, line in enumerate(lines):
        tokens = line.split()
        for length in range(max_seq, 1, -1):
            for i in range(len(tokens) - length + 1):
                seq_tokens = tokens[i:i+length]
                if all(t.isalpha() for t in seq_tokens):
                    joined = ''.join(seq_tokens).lower()
                    if joined in wordlist and not all(t.lower() in wordlist for t in seq_tokens):
                        seq_key = tuple(t.lower() for t in seq_tokens)
                        if seq_key not in all_candidates:
                            all_candidates[seq_key] = {
                                'seq_tokens': seq_tokens,
                                'joined': joined,
                                'context': get_context(tokens, i, i+length),
                                'count': 0
                            }
                        all_candidates[seq_key]['count'] += 1
    return all_candidates

def ask_user(candidate_info, stats):
    root = tk.Tk()
    root.title("OCR Space Correction")
    decision = tk.StringVar()
    seq_tokens = candidate_info['seq_tokens']
    joined = candidate_info['joined']
    context = candidate_info['context']
    count = candidate_info['count']
    stats_label = tk.Label(root, text=f"Total: {stats['total']}   Confirmed: {stats['confirmed']}   Remaining: {stats['remaining']}", font=("Arial", 11))
    stats_label.pack(pady=10)
    tk.Label(root, text=f"Found {count} occurrence(s)", font=("Arial", 12, "bold")).pack(pady=5)
    tk.Label(root, text=f"Separate: {' '.join(seq_tokens)}", font=("Arial", 14)).pack(pady=5)
    tk.Label(root, text=f"Joined: {joined}", font=("Arial", 14)).pack(pady=5)
    tk.Label(root, text="Context (first occurrence):", font=("Arial", 12)).pack()
    tk.Label(root, text=context, wraplength=750, justify="left", font=("Arial", 11)).pack(pady=10)
    def resolve(value):
        stats["confirmed"] += 1
        stats["remaining"] -= 1
        stats_label.config(text=f"Total: {stats['total']}   Confirmed: {stats['confirmed']}   Remaining: {stats['remaining']}")
        decision.set(value)
        root.after(150, root.destroy)
    tk.Button(root, text=f"Join ALL {count} occurrence(s)", width=30, command=lambda: resolve("merge")).pack(pady=5)
    tk.Button(root, text="Keep spaces", width=30, command=lambda: resolve("keep")).pack(pady=5)
    tk.Button(root, text="Quit program", width=30, command=lambda: sys.exit(0)).pack(pady=15)
    root.geometry("850x550")
    root.mainloop()
    return decision.get()

def apply_decisions(lines, decisions):
    new_lines = []
    for line in lines:
        tokens = line.split()
        i = 0
        new_tokens = []
        while i < len(tokens):
            matched = False
            for length in range(4, 1, -1):
                if i + length <= len(tokens):
                    seq_tokens = tokens[i:i+length]
                    if all(t.isalpha() for t in seq_tokens):
                        seq_key = tuple(t.lower() for t in seq_tokens)
                        if seq_key in decisions and decisions[seq_key] == "merge":
                            new_tokens.append(''.join(seq_tokens))
                            i += length
                            matched = True
                            break
            if not matched:
                new_tokens.append(tokens[i])
                i += 1
        new_lines.append(' '.join(new_tokens))
    return new_lines

def process_text(lines, wordlist, max_seq=4):
    candidates = find_all_candidates(lines, wordlist, max_seq)
    stats = {"total": len(candidates), "confirmed": 0, "remaining": len(candidates)}
    decisions = {}
    for seq_key, candidate_info in candidates.items():
        dec = ask_user(candidate_info, stats)
        decisions[seq_key] = dec
    return apply_decisions(lines, decisions)

def main():
    wordlist = load_wordlist()
    text, filepath = read_input()
    if filepath is None:
        print("No file selected")
        sys.exit(0)
    lines = text.splitlines()
    lines = process_text(lines, wordlist, max_seq=4)
    base, ext = os.path.splitext(filepath)
    outpath = f"{base}_corrected{ext}"
    with open(outpath, "w", encoding="utf-8") as f:
        f.write('\n'.join(lines))

if __name__ == "__main__":
    main()
