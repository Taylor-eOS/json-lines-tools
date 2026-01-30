import os
import sys
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
    wl.update({'i','you','he','she','it','we','they','the','a','an','and','or','but','to','of','in','on','at'})
    return wl

def read_input():
    if not sys.stdin.isatty():
        return sys.stdin.read(), None
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title="Select text file", filetypes=[("Text files", "*.txt *.md *.json"), ("All files", "*.*")])
    root.destroy()
    if not path:
        return None, None
    with open(path, "r", encoding="utf-8") as f:
        return f.read(), path

def tokenize_line(line):
    result = []
    current = ""
    for char in line:
        if char == ',':
            if current: result.append(current); current=""
            result.append(',')
        elif char == ' ':
            if current: result.append(current); current=""
        else:
            current += char
    if current: result.append(current)
    return result

def get_context(tokens, start, end, width=15):
    start_idx = max(0, start - width)
    end_idx = min(len(tokens), end + width)
    return ' '.join(tokens[start_idx:end_idx])

def check_word_status(tokens, i, wordlist):
    w1, w2 = tokens[i], tokens[i+1]
    w1l, w2l = w1.lower(), w2.lower()
    merged = w1l + w2l
    w1_valid = w1l in wordlist
    w2_valid = w2l in wordlist
    merged_valid = merged in wordlist
    print(f"'{w1}' + '{w2}' → {w1_valid} {w2_valid}, merged: {merged_valid}")
    return {
        'w1_valid': w1_valid,
        'w2_valid': w2_valid,
        'merged_valid': merged_valid,
        'w1l': w1l,
        'w2l': w2l,
        'merged': merged
    }

def find_all_pairs(lines, wordlist):
    candidates = {}
    auto_decisions = {}
    for lineno, line in enumerate(lines):
        tokens = tokenize_line(line)
        for i in range(len(tokens)-1):
            if tokens[i]==',' or tokens[i+1]==',':
                continue
            info = check_word_status(tokens, i, wordlist)
            key = (info['w1l'], info['w2l'])
            if info['w1_valid'] and info['w2_valid']:
                if info['merged_valid']:
                    pass
                else:
                    auto_decisions[key] = 'keep'
                    continue
            elif info['w1_valid'] and not info['w2_valid']:
                if info['merged_valid']:
                    auto_decisions[key] = 'merge'
                    continue
                else: #cannot decide automatically
                    pass
            elif not info['w1_valid'] and info['w2_valid']:
                if info['merged_valid']:
                    auto_decisions[key] = 'merge'
                    continue
                    pass
            elif not info['w1_valid'] and not info['w2_valid']:
                if info['merged_valid']:
                    auto_decisions[key] = 'merge'
                    continue
                else:
                    pass
            if key not in candidates:
                candidates[key] = {'seq_tokens':[tokens[i],tokens[i+1]],
                                   'joined':info['merged'],
                                   'count':0,
                                   'examples':[],
                                   'positions':[]}
            candidates[key]['count'] +=1
            ctx = get_context(tokens, i, i+2)
            candidates[key]['examples'].append(ctx)
            candidates[key]['positions'].append((lineno,i))
    for k in list(candidates.keys()):
        if k in auto_decisions: del candidates[k]
    return candidates, auto_decisions

def apply_decisions(lines, decisions):
    new_lines = []
    for line in lines:
        tokens = tokenize_line(line)
        i=0
        new_tokens=[]
        while i<len(tokens):
            if tokens[i]==',':
                new_tokens.append(',')
                i+=1
                continue
            if i<len(tokens)-1 and tokens[i+1]!=',':
                key=(tokens[i].lower(), tokens[i+1].lower())
                if key in decisions and decisions[key]=='merge':
                    new_tokens.append(tokens[i]+tokens[i+1])
                    i+=2
                    continue
            new_tokens.append(tokens[i])
            i+=1
        result=""
        for j in range(len(new_tokens)):
            if new_tokens[j]==',':
                result+=','
                if j<len(new_tokens)-1: result+=' '
            else:
                if j>0 and new_tokens[j-1]!=',':
                    result+=' '
                result+=new_tokens[j]
        new_lines.append(result)
    return new_lines

def ask_user(candidate_info, stats):
    root=tk.Tk()
    root.title("Space Correction")
    decision=tk.StringVar()
    seq_tokens=candidate_info['seq_tokens']
    context=candidate_info['examples'][0] if candidate_info['examples'] else ""
    tk.Label(root, text=f"Total: {stats['total']}  Confirmed: {stats['confirmed']}  Remaining: {stats['remaining']}", font=("Arial",11)).pack(pady=10)
    tk.Label(root, text=f"Found {candidate_info['count']} occurrence(s)", font=("Arial",12,"bold")).pack(pady=5)
    text_widget=tk.Text(root, wrap="word", font=("Arial",16), height=8, width=90, padx=15, pady=15, bg=root.cget("bg"), relief="flat", highlightthickness=0)
    text_widget.pack(pady=20,padx=20,fill="both",expand=True)
    text_widget.insert("1.0",context)
    text_widget.config(state="disabled")
    target_phrase=seq_tokens[0]+" "+seq_tokens[1]
    start_idx=context.find(target_phrase)
    if start_idx!=-1:
        start=f"1.0 + {start_idx} chars"
        end=f"1.0 + {start_idx+len(target_phrase)} chars"
        text_widget.tag_add("highlight", start, end)
        text_widget.tag_config("highlight", foreground="red", font=("Arial",16,"bold"))
    def resolve(value):
        stats['confirmed']+=1
        stats['remaining']-=1
        decision.set(value)
        root.after(100, root.destroy)
    def on_key(event):
        if event.char=='j': resolve('merge')
        elif event.char=='k': resolve('keep')
    tk.Button(root, text="Join", width=30, command=lambda:resolve('merge')).pack(pady=5)
    tk.Button(root, text="Keep separate", width=30, command=lambda:resolve('keep')).pack(pady=5)
    tk.Button(root, text="Quit", width=30, command=lambda:sys.exit(0)).pack(pady=10)
    root.bind("<Key>",on_key)
    root.geometry("900x600")
    root.mainloop()
    return decision.get()

def process_text(lines, wordlist):
    candidates, auto_decisions = find_all_pairs(lines, wordlist)
    if not candidates:
        return apply_decisions(lines, auto_decisions)
    stats={'total':len(candidates),'confirmed':0,'remaining':len(candidates)}
    user_decisions={}
    for seq_key, candidate_info in sorted(candidates.items(), key=lambda x:x[1]['count'], reverse=True):
        dec=ask_user(candidate_info, stats)
        if dec: user_decisions[seq_key]=dec
    all_decisions={}
    all_decisions.update(auto_decisions)
    all_decisions.update(user_decisions)
    return apply_decisions(lines, all_decisions)

def main():
    wordlist=load_wordlist()
    text, filepath=read_input()
    if text is None: sys.exit(0)
    lines=text.splitlines()
    lines=process_text(lines, wordlist)
    if filepath:
        base, ext=os.path.splitext(filepath)
        outpath=f"output{ext}"
        with open(outpath,"w",encoding="utf-8") as f:
            f.write('\n'.join(lines))
    else:
        sys.stdout.write('\n'.join(lines)+'\n')

if __name__=="__main__":
    main()

