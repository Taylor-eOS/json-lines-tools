import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

ROWS = 8

def main():
    root = tk.Tk()
    root.title("JSON Paragraph Merge Tool")
    root.geometry("1100x645")
    root.original_blocks = None
    root.merge_groups = None
    root.merge_decisions = None
    root.offset = 0
    menubar = tk.Menu(root)
    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Save", command=lambda: save_all(root))
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    root.config(menu=menubar)
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill="both", expand=True)
    info_label = ttk.Label(main_frame, text="", wraplength=900, justify="left", font=("Sans", 10))
    info_label.pack(pady=8)
    list_frame = ttk.Frame(main_frame)
    list_frame.pack(fill="both", expand=True, pady=10)
    row_widgets = []
    def set_row_state(row, will_merge_with_space):
        bg = "#d0e6ff" if will_merge_with_space else root.cget("bg")
        row.configure(bg=bg)
        for w in row.winfo_children():
            w.configure(bg=bg)
    for row_idx in range(ROWS):
        row = tk.Frame(list_frame, bd=1, relief="solid", padx=8, pady=6)
        row.pack(fill="x", pady=4)
        left = tk.Label(row, text="", font=("Monospace", 11), anchor="e", width=40)
        left.pack(side="left")
        mid = tk.Label(row, text="•", font=("Monospace", 14, "bold"), fg="red", width=3)
        mid.pack(side="left")
        right = tk.Label(row, text="", font=("Monospace", 11), anchor="w", width=40)
        right.pack(side="left")
        def make_toggle(local_row):
            def toggle(e=None):
                idx = root.offset + local_row
                if idx < len(root.merge_decisions):
                    root.merge_decisions[idx] = not root.merge_decisions[idx]
                    set_row_state(row_widgets[local_row][0], root.merge_decisions[idx])
            return toggle
        toggle_fn = make_toggle(row_idx)
        row.bind("<Button-1>", toggle_fn)
        left.bind("<Button-1>", toggle_fn)
        mid.bind("<Button-1>", toggle_fn)
        right.bind("<Button-1>", toggle_fn)
        row_widgets.append((row, left, mid, right))
    root.row_widgets = row_widgets
    nav_frame = ttk.Frame(main_frame)
    nav_frame.pack(pady=12)
    btn_prev = ttk.Button(nav_frame, text="Previous", width=16)
    btn_prev.pack(side="left", padx=15)
    btn_next = ttk.Button(nav_frame, text="Next", width=16)
    btn_next.pack(side="left", padx=15)
    def load_file():
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
        merge_groups = find_all_merge_groups(blocks)
        if not merge_groups:
            info_label.config(text="No potential broken paragraphs found")
            return
        root.original_blocks = blocks
        root.merge_groups = merge_groups
        root.merge_decisions = [True] * len(merge_groups)
        root.offset = 0
        refresh_page()
    def refresh_page():
        total = len(root.merge_groups)
        start = root.offset
        end = min(start + ROWS, total)
        info_label.config(text=f"Showing {start + 1}–{end} of {total}")
        for i in range(ROWS):
            row, left, mid, right = root.row_widgets[i]
            idx = start + i
            if idx < total:
                group = root.merge_groups[idx]
                prev_text = root.original_blocks[group["paragraph_indices"][0]]["text"]
                cont_text = root.original_blocks[group["paragraph_indices"][-1]]["text"]
                left.config(text=prev_text[-38:])
                right.config(text=cont_text[:38])
                set_row_state(row, root.merge_decisions[idx])
                row.pack(fill="x", pady=4)
            else:
                row.pack_forget()
    def go_next():
        root.offset += ROWS if root.offset + ROWS < len(root.merge_groups) else 0
        refresh_page()
    def go_prev():
        root.offset -= ROWS if root.offset - ROWS >= 0 else 0
        refresh_page()
    btn_next.config(command=go_next)
    btn_prev.config(command=go_prev)
    load_file()
    root.mainloop()

def find_all_merge_groups(blocks):
    merge_groups = []
    position = 0
    while position < len(blocks):
        group = try_find_merge_group_at(blocks, position)
        if group:
            merge_groups.append(group)
            position = group["start_index"] + 1
        else:
            position += 1
    return merge_groups

def try_find_merge_group_at(blocks, start_pos):
    if start_pos >= len(blocks):
        return None
    if blocks[start_pos].get("label") != "p":
        return None
    paragraph_indices = [start_pos]
    exclude_indices = []
    current_pos = start_pos + 1
    while current_pos < len(blocks):
        current_block = blocks[current_pos]
        if current_block.get("label") == "exclude":
            exclude_indices.append(current_pos)
            current_pos += 1
            continue
        if current_block.get("label") == "p":
            text_content = current_block.get("text", "")
            if text_content and len(text_content) > 0:
                first_char = text_content[0]
                if first_char.islower():
                    paragraph_indices.append(current_pos)
                    break
                if first_char == '“' and len(text_content) > 1 and text_content[1].islower():
                    paragraph_indices.append(current_pos)
                    break
        break
    if len(paragraph_indices) < 2:
        return None
    if len(exclude_indices) == 0:
        return None
    return {
        "paragraph_indices": paragraph_indices,
        "exclude_indices": exclude_indices,
        "start_index": start_pos,
        "end_index": paragraph_indices[-1]
    }

def save_all(root):
    if not root.original_blocks or not root.merge_groups:
        return
    blocks_with_metadata = []
    for original_index, block_data in enumerate(root.original_blocks):
        blocks_with_metadata.append({
            "original_index": original_index,
            "data": dict(block_data),
            "action": "keep"
        })
    for group_index, use_space in enumerate(root.merge_decisions):
        group = root.merge_groups[group_index]
        paragraph_positions = group["paragraph_indices"]
        exclude_positions = group["exclude_indices"]
        primary_position = paragraph_positions[0]
        blocks_with_metadata[primary_position]["action"] = "merge_target"
        blocks_with_metadata[primary_position]["merge_sources"] = paragraph_positions[1:]
        blocks_with_metadata[primary_position]["use_space"] = use_space
        for para_pos in paragraph_positions[1:]:
            blocks_with_metadata[para_pos]["action"] = "delete"
        for excl_pos in exclude_positions:
            blocks_with_metadata[excl_pos]["action"] = "delete"
    final_blocks = []
    for block_meta in blocks_with_metadata:
        if block_meta["action"] == "delete":
            continue
        if block_meta["action"] == "merge_target":
            merged_text = block_meta["data"]["text"]
            use_space = block_meta.get("use_space", True)
            for source_pos in block_meta["merge_sources"]:
                source_text = root.original_blocks[source_pos].get("text", "")
                if not use_space and merged_text.endswith("-"):
                    merged_text = merged_text[:-1] + source_text
                else:
                    merged_text = merged_text + (" " if use_space else "") + source_text
            result_block = dict(block_meta["data"])
            result_block["text"] = merged_text
            final_blocks.append(result_block)
        else:
            final_blocks.append(block_meta["data"])
    save_path = filedialog.asksaveasfilename(title="Save merged file", initialfile="merged.json", defaultextension=".json", filetypes=[("JSON Lines", "*.json"), ("All files", "*.*")])
    if not save_path:
        return
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            for block in final_blocks:
                json.dump(block, f, ensure_ascii=False, separators=(", ", ": "))
                f.write("\n")
        messagebox.showinfo("Done", f"Saved successfully:\n{save_path}")
    except Exception as e:
        messagebox.showerror("Save failed", f"Could not write file:\n{str(e)}")

if __name__ == "__main__":
    main()
