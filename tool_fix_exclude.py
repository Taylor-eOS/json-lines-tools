import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

def main():
    root = tk.Tk()
    root.title("JSON Paragraph Merge Tool")
    root.geometry("950x400")
    root.blocks = None
    root.candidates = None
    root.choices = []
    current_index = 0
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill="both", expand=True)
    info_label = ttk.Label(main_frame, text="", wraplength=700, justify="left", font=("Sans", 10))
    info_label.pack(pady=8)
    preview_frame = ttk.Frame(main_frame)
    preview_frame.pack(fill="x", pady=12)
    left_label = tk.Label(preview_frame, text="", font=("Monospace", 12), anchor="e")
    left_label.pack(side="left")
    cursor = tk.Label(preview_frame, text="•", foreground="red", font=("Monospace", 16, "bold"))
    cursor.pack(side="left")
    right_label = tk.Label(preview_frame, text="", font=("Monospace", 12), anchor="w")
    right_label.pack(side="left")
    exclude_label = ttk.Label(main_frame, text="", wraplength=700, foreground="gray", font=("Sans", 9))
    exclude_label.pack(pady=10)
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=25)
    btn_skip = ttk.Button(button_frame, text="Skip", width=18)
    btn_skip.pack(side="left", padx=25)
    btn_no_space = ttk.Button(button_frame, text="Merge", width=18)
    btn_no_space.pack(side="left", padx=25)
    btn_space = ttk.Button(button_frame, text="Space", width=18)
    btn_space.pack(side="left", padx=25)
    btn_save = ttk.Button(button_frame, text="Save Progress", width=18)
    btn_save.pack(side="left", padx=25)

    def load_file():
        nonlocal current_index
        try:
            with open("input.json", "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            info_label.config(text="input.json not found in current folder")
            return
        blocks = []
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            try:
                blocks.append(json.loads(line))
            except json.JSONDecodeError:
                messagebox.showerror("Parse Error", f"Invalid JSON at line {i}")
                return
        candidates = []
        i = 0
        while i < len(blocks) - 2:
            p1 = blocks[i]
            ex = blocks[i + 1]
            p2 = blocks[i + 2]
            if (p1.get("label") == "p" and ex.get("label") == "exclude" and p2.get("label") == "p"):
                txt2 = p2.get("text", "")
                if txt2 and txt2[0].islower():
                    candidates.append({
                        "prev_idx": i,
                        "cont_idx": i + 2,
                        "prev_text": p1.get("text", ""),
                        "cont_text": txt2,
                        "excl_text": ex.get("text", ""),
                        "prev_page": p1.get("page", "?"),
                        "cont_page": p2.get("page", "?")
                    })
                    i += 3
                    continue
            i += 1
        if not candidates:
            info_label.config(text="No potential broken paragraphs found (no lowercase sentence starts after exclude)")
            return
        root.blocks = blocks
        root.candidates = candidates
        root.choices = ["skip"] * len(candidates)
        current_index = 0
        show_candidate()

    def show_candidate():
        if not root.candidates or current_index >= len(root.candidates):
            info_label.config(text="All candidates reviewed → saving now")
            btn_skip.config(state="disabled")
            btn_no_space.config(state="disabled")
            btn_space.config(state="disabled")
            apply_merges()
            return
        cand = root.candidates[current_index]
        prev = cand["prev_text"]
        cont = cand["cont_text"]
        left_part = prev[-38:] if len(prev) >= 38 else prev
        right_part = cont[:38] if len(cont) >= 38 else cont
        left_label.config(text=left_part)
        right_label.config(text=right_part)
        cursor.config(text="•")
        excl = cand["excl_text"]
        if len(excl) > 100:
            excl = excl[:97] + "…"
        exclude_label.config(text=f"Excluded between:  {excl}")
        info_label.config(text=f"Decision {current_index+1} of {len(root.candidates)} • pages {cand['prev_page']} → {cand['cont_page']}")

    def choose(choice):
        nonlocal current_index
        if current_index < len(root.choices):
            root.choices[current_index] = choice
        current_index += 1
        show_candidate()

    def apply_merges():
        if not root.blocks or not root.candidates:
            return
        blocks = root.blocks[:]
        merges = []
        for i, ch in enumerate(root.choices):
            if ch == "skip":
                continue
            cand = root.candidates[i]
            add_space = (ch == "with_space")  # "no_space" will be False, still merge
            merges.append((cand["prev_idx"], cand["cont_idx"], cand["prev_idx"]+1, add_space))
        merges.sort(key=lambda x: x[0], reverse=True)
        for prev_idx, cont_idx, excl_idx, add_space in merges:
            sp = " " if add_space else ""
            blocks[prev_idx]["text"] += sp + blocks[cont_idx]["text"]
            del blocks[excl_idx:cont_idx+1]  # remove the exclude block and continuation block
        save_path = filedialog.asksaveasfilename(
            title="Save merged file",
            initialfile="merged.json",
            defaultextension=".json",
            filetypes=[("JSON Lines", "*.json"), ("All files", "*.*")])
        if not save_path:
            messagebox.showinfo("Cancelled", "Save cancelled – application will close")
            root.quit()
            return
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                for block in blocks:
                    json.dump(block, f, ensure_ascii=False, separators=(", ", ": "))
                    f.write("\n")
            messagebox.showinfo("Done", f"Saved successfully:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Save failed", f"Could not write file:\n{str(e)}")
        root.quit()

    def save_progress():
        if not root.blocks or not root.candidates:
            return
        blocks = root.blocks[:]
        merges = []
        for i, ch in enumerate(root.choices[:current_index]):
            if ch == "skip":
                continue
            cand = root.candidates[i]
            add_space = (ch == "with_space")
            merges.append((cand["prev_idx"], cand["cont_idx"], cand["prev_idx"]+1, add_space))
        merges.sort(key=lambda x: x[0], reverse=True)
        for prev_idx, cont_idx, excl_idx, add_space in merges:
            sp = " " if add_space else ""
            blocks[prev_idx]["text"] += sp + blocks[cont_idx]["text"]
            del blocks[excl_idx:cont_idx+1]
        save_path = filedialog.asksaveasfilename(
            title="Save progress",
            initialfile="merged.json",
            defaultextension=".json",
            filetypes=[("JSON Lines", "*.json"), ("All files", "*.*")])
        if not save_path:
            messagebox.showinfo("Cancelled", "Save cancelled")
            return
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                for block in blocks:
                    json.dump(block, f, ensure_ascii=False, separators=(", ", ": "))
                    f.write("\n")
            messagebox.showinfo("Saved", f"Progress saved:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Save failed", f"Could not write file:\n{str(e)}")

    btn_skip.config(command=lambda: choose("skip"))
    btn_no_space.config(command=lambda: choose("no_space"))
    btn_space.config(command=lambda: choose("with_space"))
    btn_save.config(command=save_progress)
    load_file()
    root.mainloop()

if __name__ == "__main__":
    main()

