import os
import sys
import string
import tkinter as tk
from tkinter import filedialog
import nltk

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
    path = filedialog.askopenfilename(title="Select text file", filetypes=[("Text files", "*.txt *.json *.md"), ("All files", "*.*")])
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
    punctuation = string.punctuation
    for line in lines:
        tokens = line.split()
        for i in range(len(tokens) - 1):
            left = tokens[i]
            right = tokens[i + 1]
            if not left.isalpha():
                continue
            right_clean = right.rstrip(punctuation)
            if not (right_clean.isalpha() and right_clean):
                continue
            l_lower = left.lower()
            r_lower = right_clean.lower()
            joined_lower = l_lower + r_lower
            separate_valid = l_lower in wordlist and r_lower in wordlist
            joined_valid = joined_lower in wordlist
            if not separate_valid or joined_valid:
                key = (l_lower, r_lower)
                if key not in candidates:
                    candidates[key] = {
                        'seq_tokens': [left, right],
                        'joined': left + right_clean,
                        'context': get_context(tokens, i, i + 2),
                        'count': 0}
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
    tk.Label(root, text="", font=("Arial", 12)).pack()
    text_widget = tk.Text(root, wrap="word", font=("Arial", 11), height=6, width=90, padx=8, pady=8, bg=root.cget("bg"), relief="flat", highlightthickness=0)
    text_widget.pack(pady=10, padx=20, fill="x")
    text_widget.insert("1.0", context)
    text_widget.config(state="disabled")
    target_phrase = seq_tokens[0] + " " + seq_tokens[1]
    start_idx = context.find(target_phrase)
    if start_idx != -1:
        start = f"1.0 + {start_idx} chars"
        end = f"1.0 + {start_idx + len(target_phrase)} chars"
        text_widget.tag_add("redpair", start, end)
        text_widget.tag_config("redpair", foreground="red")
    else:
        pos = 0
        for token in seq_tokens:
            pos = context.find(token, pos)
            if pos != -1:
                start = f"1.0 + {pos} chars"
                end = f"1.0 + {pos + len(token)} chars"
                text_widget.tag_add("redpair", start, end)
                pos += len(token)
    def resolve(value):
        stats["confirmed"] += 1
        stats["remaining"] -= 1
        stats_label.config(text=f"Total: {stats['total']}   Confirmed: {stats['confirmed']}   Remaining: {stats['remaining']}")
        decision.set(value)
        root.after(150, root.destroy)
    def on_key(event):
        if event.char == "j":
            resolve("merge")
        elif event.char == "k":
            resolve("keep")
    tk.Button(root, text="Join", width=30, command=lambda: resolve("merge")).pack(pady=5)
    tk.Button(root, text="Keep separate", width=30, command=lambda: resolve("keep")).pack(pady=5)
    tk.Button(root, text="Quit", width=30, command=lambda: sys.exit(0)).pack(pady=15)
    root.bind("<Key>", on_key)
    root.geometry("900x600")
    root.mainloop()
    return decision.get()

def apply_decisions(lines, decisions, wordlist):
    new_lines = []
    punctuation = string.punctuation
    for line in lines:
        tokens = line.split()
        changed = True
        while changed:
            changed = False
            i = 0
            while i < len(tokens) - 1:
                left = tokens[i]
                right = tokens[i + 1]
                if not left.isalpha():
                    i += 1
                    continue
                right_clean = right.rstrip(punctuation)
                if not (right_clean.isalpha() and right_clean):
                    i += 1
                    continue
                l_lower = left.lower()
                r_lower = right_clean.lower()
                joined_lower = l_lower + r_lower
                key = (l_lower, r_lower)
                merge = False
                if key in decisions and decisions[key] == "merge":
                    merge = True
                if joined_lower in wordlist and not (l_lower in wordlist and r_lower in wordlist):
                    merge = True
                if merge:
                    tokens[i] = left + right_clean
                    if right != right_clean:
                        tokens[i] += right[len(right_clean):]
                    del tokens[i + 1]
                    changed = True
                    i = max(0, i - 1)
                else:
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
        outpath = f"output{ext}"
        with open(outpath, "w", encoding="utf-8") as f:
            f.write('\n'.join(lines))
    else:
        sys.stdout.write('\n'.join(lines) + '\n')

if __name__ == "__main__":
    main()

