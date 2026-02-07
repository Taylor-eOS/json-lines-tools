import tkinter as tk
from tkinter import messagebox, simpledialog
import re
import os
import glob
from pathlib import Path

CONTEXT_LENGTH = 27
FILTER_YEARS = False

def to_bold(num_str):
    bold_digits = {'0':'𝟎','1':'𝟏','2':'𝟐','3':'𝟑','4':'𝟒','5':'𝟓',
                   '6':'𝟔','7':'𝟕','8':'𝟖','9':'𝟗'}
    return ''.join(bold_digits.get(ch, ch) for ch in num_str)

class FootnoteXHTMLProcessor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("XHTML Footnote → <sup> Processor")
        self.geometry("780x720")
        self.current_file = None
        self.current_content = ""
        self.header_end_pos = 0
        self.tokens = []
        self.create_widgets()
        self.ask_and_load_first_file()

    def create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE,
                                  font=("Consolas", 10), exportselection=False)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind("<Button-1>", self.on_listbox_click)
        self.listbox.bind("<<ListboxSelect>>", self.on_selection_change)
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=6)
        tk.Button(btn_frame, text="Apply <sup> → Save", command=self.apply_and_save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Skip this file", command=self.skip_file).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Next file", command=self.load_next_file).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Quit", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        self.status_var = tk.StringVar(value="No file loaded")
        tk.Label(self, textvariable=self.status_var, anchor="w", padx=10).pack(fill=tk.X, pady=(0,4))

    def ask_and_load_first_file(self):
        folder = simpledialog.askstring("Folder path", "Full path to folder with .xhtml files\n(leave empty = current directory):",
                                        initialvalue=str(Path.cwd()))
        if not folder:
            folder = "."
        self.xhtml_files = sorted(glob.glob(os.path.join(folder, "*.xhtml")))
        if not self.xhtml_files:
            messagebox.showerror("No files", "No .xhtml files found in the selected folder.")
            self.destroy()
            return
        self.file_index = 0
        self.load_current_file()

    def load_current_file(self):
        if self.file_index >= len(self.xhtml_files):
            messagebox.showinfo("Finished", "All files processed.")
            self.destroy()
            return
        self.current_file = self.xhtml_files[self.file_index]
        self.status_var.set(f"File {self.file_index+1}/{len(self.xhtml_files)}: {os.path.basename(self.current_file)}")
        try:
            with open(self.current_file, "r", encoding="utf-8") as f:
                self.current_content = f.read()
        except Exception as e:
            messagebox.showerror("Read error", f"Cannot read file:\n{self.current_file}\n{e}")
            self.skip_file()
            return
        self.find_header_end()
        self.extract_potential_footnotes()
        self.listbox.delete(0, tk.END)
        for token in self.tokens:
            self.listbox.insert(tk.END, token["snippet"])

    def find_header_end(self):
        self.header_end_pos = 0
        match = re.search(r"</head>\s*<body", self.current_content, re.IGNORECASE | re.DOTALL)
        if match:
            self.header_end_pos = match.end()
        else:
            match = re.search(r"<body", self.current_content, re.IGNORECASE)
            if match:
                self.header_end_pos = match.end()

    def is_inside_p_tag(self, context, pos_in_context):
        before = context[:pos_in_context]
        after = context[pos_in_context:]
        last_open = before.rfind('<p ')
        last_close_before = before.rfind('>')
        next_close = after.find('>')
        if last_open == -1:
            return False
        if last_close_before > last_open:
            return False
        if next_close == -1:
            return False
        return True

    def extract_potential_footnotes(self):
        self.tokens = []
        pattern = re.compile(r"\b\d{1,3}\b")
        search_text = self.current_content[self.header_end_pos:]
        offset = self.header_end_pos
        for m in pattern.finditer(search_text):
            num_str = m.group()
            num_val = int(num_str)
            if FILTER_YEARS and re.match(r"^(19\d{2}|20\d{2})$", num_str):
                continue
            global_start = offset + m.start()
            global_end   = offset + m.end()
            context_start = max(0, global_start - 50)
            context_end = min(len(self.current_content), global_end + 50)
            context = self.current_content[context_start:context_end]
            if '<p style="display: inline;">' in context or '<p style="font-size: 0.8em; color: gray;">' in context:
                pos_in_context = global_start - context_start
                if self.is_inside_p_tag(context, pos_in_context):
                    continue
            snippet_start = max(0, global_start - 36)
            snippet_end   = min(len(self.current_content), global_end + CONTEXT_LENGTH)
            snippet = self.current_content[snippet_start:snippet_end]
            snippet = snippet.replace("\n", " ").strip()
            while "  " in snippet:
                snippet = snippet.replace("  ", " ")
            snippet = snippet.replace(num_str, to_bold(num_str), 1)
            self.tokens.append({
                "global_start": global_start,
                "global_end":   global_end,
                "number":       num_val,
                "text":         num_str,
                "snippet":      snippet
            })

    def on_listbox_click(self, event):
        index = self.listbox.nearest(event.y)
        self.listbox.activate(index)
        if index in self.listbox.curselection():
            self.listbox.selection_clear(index)
        else:
            self.listbox.selection_set(index)
            self.on_selection_change(None)
        return "break"

    def find_forward_consecutive(self, anchor_idx):
        if anchor_idx >= len(self.tokens):
            return []
        anchor_num = self.tokens[anchor_idx]["number"]
        result = []
        next_expected = anchor_num + 1
        for i in range(anchor_idx + 1, len(self.tokens)):
            if self.tokens[i]["number"] == next_expected:
                result.append(i)
                next_expected += 1
        return result

    def on_selection_change(self, event):
        self.listbox.unbind("<<ListboxSelect>>")
        try:
            sel = list(self.listbox.curselection())
            if not sel:
                return
            anchor = self.listbox.index(tk.ACTIVE)
            if anchor not in sel:
                sel.append(anchor)
            for i in range(anchor + 1, len(self.tokens)):
                self.listbox.selection_clear(i)
            for idx in self.find_forward_consecutive(anchor):
                self.listbox.selection_set(idx)
        finally:
            self.listbox.bind("<<ListboxSelect>>", self.on_selection_change)

    def apply_and_save(self):
        sel = self.listbox.curselection()
        if not sel:
            if messagebox.askyesno("No selection", "No numbers selected. Skip file?"):
                self.skip_file()
            return
        selected = [self.tokens[i] for i in sel]
        selected.sort(key=lambda x: x["global_start"], reverse=True)
        content = self.current_content
        for tok in selected:
            start = tok["global_start"]
            end   = tok["global_end"]
            content = content[:start] + f"<sup>{tok['text']}</sup>" + content[end:]
        backup_path = self.current_file + ".bak"
        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.load_next_file()
        except Exception as e:
            messagebox.showerror("Write failed", str(e))
            try:
                os.replace(backup_path, self.current_file)
            except:
                pass

    def skip_file(self):
        self.load_next_file()

    def load_next_file(self):
        self.file_index += 1
        self.load_current_file()

if __name__ == '__main__':
    app = FootnoteXHTMLProcessor()
    app.mainloop()
