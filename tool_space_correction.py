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
    wl = set(w.lower() for w in words.words() if w.isalpha())
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'we', 'they', 'them', 'their', 'my', 'your', 'his', 'her', 'our'}
    wl.update(common_words)
    return wl

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

def tokenize_line(line):
    result = []
    current = ""
    for char in line:
        if char == ',':
            if current:
                result.append(current)
                current = ""
            result.append(',')
        elif char == ' ':
            if current:
                result.append(current)
                current = ""
        else:
            current += char
    if current:
        result.append(current)
    return result

def check_word_status_extended(tokens, i, wordlist):
    w1 = tokens[i]
    w2 = tokens[i + 1]
    w1l = w1.lower()
    w2l = w2.lower()
    merged = w1l + w2l
    w_before = tokens[i - 1].lower() if i > 0 and tokens[i - 1] != ',' else None
    w_after = tokens[i + 2].lower() if i + 2 < len(tokens) and tokens[i + 2] != ',' else None
    merged_before = (w_before + w1l) if w_before else None
    merged_after = (w2l + w_after) if w_after else None
    return {
        'w1l': w1l,
        'w2l': w2l,
        'merged_valid': merged in wordlist,
        'merged_before_valid': merged_before in wordlist if merged_before else False,
        'merged_after_valid': merged_after in wordlist if merged_after else False
    }

def determine_auto_decision(status):
    merged_valid = status['merged_valid']
    merged_before_valid = status['merged_before_valid']
    merged_after_valid = status['merged_after_valid']
    if merged_valid and not merged_before_valid and not merged_after_valid:
        return "merge"
    if not merged_valid and not merged_before_valid and not merged_after_valid:
        return "keep"
    return None

def find_all_pairs(lines, wordlist):
    candidates = {}
    auto_decisions = {}
    for line in lines:
        tokens = tokenize_line(line)
        n = len(tokens)
        for i in range(n - 1):
            w1 = tokens[i]
            w2 = tokens[i + 1]
            if w1 == ',' or w2 == ',':
                continue
            status = check_word_status_extended(tokens, i, wordlist)
            key = (status['w1l'], status['w2l'])
            auto_decision = determine_auto_decision(status)
            if auto_decision is not None:
                auto_decisions[key] = auto_decision
            else:
                if key not in candidates:
                    context = get_context(tokens, i, i + 2)
                    candidates[key] = {
                        "seq_tokens": [w1, w2],
                        "joined": w1 + w2,
                        "context": context,
                        "count": 0
                    }
                candidates[key]["count"] += 1
    return candidates, auto_decisions

def apply_decisions(lines, decisions):
    new_lines = []
    for line in lines:
        tokens = tokenize_line(line)
        i = 0
        new_tokens = []
        while i < len(tokens):
            if tokens[i] == ',':
                new_tokens.append(',')
                i += 1
                continue
            if i < len(tokens) - 1 and tokens[i + 1] != ',':
                key = (tokens[i].lower(), tokens[i + 1].lower())
                if key in decisions and decisions[key] == "merge":
                    new_tokens.append(tokens[i] + tokens[i + 1])
                    i += 2
                    continue
            new_tokens.append(tokens[i])
            i += 1
        result = ""
        for j in range(len(new_tokens)):
            if new_tokens[j] == ',':
                result += ','
                if j < len(new_tokens) - 1:
                    result += ' '
            else:
                if j > 0 and new_tokens[j - 1] != ',':
                    result += ' '
                result += new_tokens[j]
        new_lines.append(result)
    return new_lines

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
    text_widget = tk.Text(root, wrap="word", font=("Arial", 16), height=8, width=90, padx=15, pady=15, bg=root.cget("bg"), relief="flat", highlightthickness=0)
    text_widget.pack(pady=20, padx=20, fill="both", expand=True)
    text_widget.insert("1.0", context)
    text_widget.config(state="disabled")
    target_phrase = seq_tokens[0] + " " + seq_tokens[1]
    start_idx = context.find(target_phrase)
    if start_idx != -1:
        start = f"1.0 + {start_idx} chars"
        end = f"1.0 + {start_idx + len(target_phrase)} chars"
        text_widget.tag_add("redpair", start, end)
        text_widget.tag_config("redpair", foreground="red", font=("Arial", 16, "bold"))
    else:
        pos = 0
        for token in seq_tokens:
            pos = context.find(token, pos)
            if pos != -1:
                start = f"1.0 + {pos} chars"
                end = f"1.0 + {pos + len(token)} chars"
                text_widget.tag_add("redpair", start, end)
                pos += len(token)
        text_widget.tag_config("redpair", foreground="red", font=("Arial", 16, "bold"))
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

def process_text(lines, wordlist):
    candidates, auto_decisions = find_all_pairs(lines, wordlist)
    items = sorted(candidates.items(), key=lambda item: item[1]['count'], reverse=True)
    stats = {"total": len(candidates), "confirmed": 0, "remaining": len(candidates)}
    user_decisions = {}
    for seq_key, candidate_info in items:
        if stats["remaining"] <= 0:
            break
        dec = ask_user(candidate_info, stats)
        user_decisions[seq_key] = dec
    all_decisions = {}
    all_decisions.update(auto_decisions)
    all_decisions.update(user_decisions)
    return apply_decisions(lines, all_decisions)

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
