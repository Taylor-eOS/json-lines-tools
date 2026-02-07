import tkinter as tk
from tkinter import messagebox
import re
import json
import os

CONTEXT_LENGTH = 27
FILTER_YEARS = False

def to_bold(num_str):
    bold_digits = {'0':'𝟎','1':'𝟏','2':'𝟐','3':'𝟑','4':'𝟒','5':'𝟓',
                   '6':'𝟔','7':'𝟕','8':'𝟖','9':'𝟗'}
    return ''.join(bold_digits.get(ch, ch) for ch in num_str)

class FootnoteSelector(tk.Tk):
    def __init__(self):
        filename = input("Input file: ") or 'input.json'
        super().__init__()
        self.title("Footnote Reference Selector")
        self.geometry("740x700")
        self.filename = filename
        self.blocks = []
        self.tokens = []
        self.load_file()
        self.extract_tokens()
        self.create_widgets()

    def load_file(self):
        self.blocks = []
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    block = json.loads(line)
                    self.blocks.append(block)
        except Exception as e:
            messagebox.showerror("File Error", f"Could not load {self.filename}:\n{e}")
            self.blocks = []

    def is_year(self, text):
        if FILTER_YEARS:
            return bool(re.match(r"^(19[0-9]\d|20[0-9]\d|18[0-9]\d)$", text))
        else:
            return False

    def extract_tokens(self):
        self.tokens = []
        pattern = re.compile(r"\d+")
        for block_idx, block in enumerate(self.blocks):
            if block.get("label") == "exclude":
                continue
            if block.get("label") in ["h1", "h2", "h3"]:
                continue
            text = block.get("text", "")
            for m in pattern.finditer(text):
                num_str = m.group()
                if self.is_year(num_str):
                    continue
                num_val = int(num_str)
                snippet = (text[max(0, m.start() - 33):m.start()] +
                           to_bold(num_str) +
                           text[m.end():min(len(text), m.end() + CONTEXT_LENGTH)])
                snippet = snippet.replace("\n", " ").strip()
                while "  " in snippet:
                    snippet = snippet.replace("  ", " ")
                self.tokens.append({
                    "block_idx": block_idx,
                    "local_start": m.start(),
                    "local_end": m.end(),
                    "number": num_val,
                    "text": num_str,
                    "snippet": snippet,
                    "is_year": False})

    def create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, font=("Consolas", 10), exportselection=False)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind("<Button-1>", self.on_click)
        self.listbox.bind("<<ListboxSelect>>", self.on_selection_change)
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        for token in self.tokens:
            self.listbox.insert(tk.END, token["snippet"])
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        process_button = tk.Button(button_frame, text="Apply <sup> Tags", command=self.apply_sup_tags)
        process_button.pack(side=tk.LEFT, padx=5)
        quit_button = tk.Button(button_frame, text="Quit", command=self.destroy)
        quit_button.pack(side=tk.RIGHT, padx=5)

    def on_click(self, event):
        index = self.listbox.nearest(event.y)
        self.listbox.activate(index)
        if index in self.listbox.curselection():
            self.listbox.selection_clear(index)
        else:
            self.listbox.selection_set(index)
            self.on_selection_change(None)
        return "break"

    def find_forward_consecutive_indices(self, anchor_index):
        result_indices = []
        anchor_token = self.tokens[anchor_index]
        anchor_number = anchor_token["number"]
        next_expected = anchor_number + 1
        current_search_start = anchor_index + 1
        while current_search_start < len(self.tokens):
            found = False
            for i in range(current_search_start, len(self.tokens)):
                token = self.tokens[i]
                if token["number"] == next_expected:
                    result_indices.append(i)
                    next_expected += 1
                    current_search_start = i + 1
                    found = True
                    break
            if not found:
                break
        return result_indices

    def on_selection_change(self, event):
        self.listbox.unbind("<<ListboxSelect>>")
        try:
            selected_indices = list(self.listbox.curselection())
            if not selected_indices:
                return
            try:
                anchor_index = self.listbox.index(tk.ACTIVE)
            except Exception:
                anchor_index = max(selected_indices)
            if anchor_index not in selected_indices:
                selected_indices.append(anchor_index)
            for i in range(anchor_index + 1, len(self.tokens)):
                self.listbox.selection_clear(i)
            forward_indices = self.find_forward_consecutive_indices(anchor_index)
            for idx in forward_indices:
                self.listbox.selection_set(idx)
        finally:
            self.listbox.bind("<<ListboxSelect>>", self.on_selection_change)

    def apply_sup_tags(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("No Selection", "No tokens selected. Please select tokens to wrap in <sup> tags.")
            return
        selected_tokens = [self.tokens[i] for i in selected_indices]
        tokens_by_block = {}
        for token in selected_tokens:
            bidx = token["block_idx"]
            tokens_by_block.setdefault(bidx, []).append(token)
        for bidx, btokens in tokens_by_block.items():
            btokens.sort(key=lambda t: t["local_start"], reverse=True)
            text = self.blocks[bidx]["text"]
            for token in btokens:
                start = token["local_start"]
                end = token["local_end"]
                text = text[:start] + f"<sup>{token['text']}</sup>" + text[end:]
            self.blocks[bidx]["text"] = text
        base, ext = os.path.splitext(self.filename)
        output_filename = base + "_sup" + ext
        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                for block in self.blocks:
                    json.dump(block, f, ensure_ascii=False)
                    f.write("\n")
            messagebox.showinfo("Success", f"Processed file saved as '{output_filename}'.")
        except Exception as e:
            messagebox.showerror("Write Error", f"Could not write output file:\n{e}")

    def reload_file(self):
        self.load_file()
        self.extract_tokens()
        self.listbox.delete(0, tk.END)
        for token in self.tokens:
            self.listbox.insert(tk.END, token["snippet"])

if __name__ == '__main__':
    app = FootnoteSelector()
    app.mainloop()

