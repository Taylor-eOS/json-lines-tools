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
        return None, None
    with open(path, "r", encoding="utf-8") as f:
        return f.read(), path

def get_context(tokens, start, end, width=15):
    start_idx = max(0, start - width)
    end_idx = min(len(tokens), end + width)
    return ' '.join(tokens[start_idx:end_idx])

def find_suspicious_pairs(lines, wordlist):
    candidates = {}
    for line in lines:
        tokens = line.split()
        for i in range(len(tokens) - 1):
            left = tokens[i]
            right = tokens[i + 1]
            if left.isalpha() and right.isalpha():
                l_lower = left.lower()
                r_lower = right.lower()
                if not (l_lower in wordlist and r_lower in wordlist):
                    key = (l_lower, r_lower)
                    if key not in candidates:
                        candidates[key] = {
                            'seq_tokens': [left, right],
                            'joined': left + right,
                            'context': get_context(tokens, i, i + 2),
                            'count': 0
                        }
                    candidates[key]['count'] += 1
    return candidates

def ask_user(candidate_info, stats):
    root = tk.Tk()
    root.title("Space Correction")
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
    tk.Label(root, text="Context:", font=("Arial", 12)).pack()
    tk.Label(root, text=context, wraplength=750, justify="left", font=("Arial", 11)).pack(pady=10)
    def resolve(value):
        stats["confirmed"] += 1
        stats["remaining"] -= 1
        stats_label.config(text=f"Total: {stats['total']}   Confirmed: {stats['confirmed']}   Remaining: {stats['remaining']}")
        decision.set(value)
        root.after(150, root.destroy)
    tk.Button(root, text=f"Join {count}", width=30, command=lambda: resolve("merge")).pack(pady=5)
    tk.Button(root, text="Keep separate", width=30, command=lambda: resolve("keep")).pack(pady=5)
    tk.Button(root, text="Quit", width=30, command=lambda: sys.exit(0)).pack(pady=15)
    root.geometry("900x600")
    root.mainloop()
    return decision.get()

def apply_decisions(lines, decisions, wordlist):
    new_lines = []
    for line in lines:
        tokens = line.split()
        i = 0
        while i < len(tokens):
            if i + 1 < len(tokens):
                left = tokens[i]
                right = tokens[i + 1]
                if left.isalpha() and right.isalpha():
                    l_lower = left.lower()
                    r_lower = right.lower()
                    key = (l_lower, r_lower)
                    joined = left + right
                    joined_lower = joined.lower()
                    merge = False
                    if key in decisions:
                        if decisions[key] == "merge":
                            merge = True
                    if joined_lower in wordlist and not (l_lower in wordlist and r_lower in wordlist):
                        merge = True
                    if merge:
                        tokens[i] = joined
                        del tokens[i + 1]
                        continue
            i += 1
        new_lines.append(' '.join(tokens))
    return new_lines

def process_text(lines, wordlist):
    candidates = find_suspicious_pairs(lines, wordlist)
    items = sorted(candidates.items(), key=lambda item: item[1]['count'], reverse=True)
    stats = {"total": len(candidates), "confirmed": 0, "remaining": len(candidates)}
    decisions = {}
    for seq_key, candidate_info in items:
        if stats["remaining"] <= 0:
            break
        dec = ask_user(candidate_info, stats)
        decisions[seq_key] = dec
    return apply_decisions(lines, decisions, wordlist)

def main():
    wordlist = load_wordlist()
    text, filepath = read_input()
    if text is None:
        sys.exit(0)
    lines = text.splitlines()
    lines = process_text(lines, wordlist)
    if filepath:
        base, ext = os.path.splitext(filepath)
        outpath = f"{base}_corrected{ext}"
        with open(outpath, "w", encoding="utf-8") as f:
            f.write('\n'.join(lines))
    else:
        sys.stdout.write('\n'.join(lines) + '\n')

if __name__ == "__main__":
    main()
