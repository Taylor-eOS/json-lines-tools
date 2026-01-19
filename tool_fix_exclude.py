import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

ROWS = 8

def main():
    root=tk.Tk()
    root.title("JSON Paragraph Merge Tool")
    root.geometry("1100x620")
    root.blocks=None
    root.candidates=None
    root.selections=[]
    root.offset=0
    menubar=tk.Menu(root)
    filemenu=tk.Menu(menubar,tearoff=0)
    filemenu.add_command(label="Save",command=lambda:save_all(root))
    filemenu.add_separator()
    filemenu.add_command(label="Exit",command=root.quit)
    menubar.add_cascade(label="File",menu=filemenu)
    root.config(menu=menubar)
    main_frame=ttk.Frame(root,padding=20)
    main_frame.pack(fill="both",expand=True)
    info_label=ttk.Label(main_frame,text="",wraplength=900,justify="left",font=("Sans",10))
    info_label.pack(pady=8)
    list_frame=ttk.Frame(main_frame)
    list_frame.pack(fill="both",expand=True,pady=10)
    row_widgets=[]
    def set_row_selected(row,selected):
        bg="#d0e6ff" if selected else root.cget("bg")
        row.configure(bg=bg)
        for w in row.winfo_children():w.configure(bg=bg)
    for _ in range(ROWS):
        row=tk.Frame(list_frame,bd=1,relief="solid",padx=8,pady=6)
        row.pack(fill="x",pady=4)
        var=tk.BooleanVar(value=False)
        left=tk.Label(row,text="",font=("Monospace",11),anchor="e",width=40)
        left.pack(side="left")
        mid=tk.Label(row,text="•",font=("Monospace",14,"bold"),fg="red",width=3)
        mid.pack(side="left")
        right=tk.Label(row,text="",font=("Monospace",11),anchor="w",width=40)
        right.pack(side="left")
        def make_toggle(v,r):
            def toggle(e=None):
                v.set(not v.get())
                set_row_selected(r,v.get())
            return toggle
        toggle_fn=make_toggle(var,row)
        row.bind("<Button-1>",toggle_fn)
        left.bind("<Button-1>",toggle_fn)
        mid.bind("<Button-1>",toggle_fn)
        right.bind("<Button-1>",toggle_fn)
        row_widgets.append((row,left,right,var))
    root.row_widgets=row_widgets
    nav_frame=ttk.Frame(main_frame)
    nav_frame.pack(pady=12)
    btn_prev=ttk.Button(nav_frame,text="Previous",width=16)
    btn_prev.pack(side="left",padx=15)
    btn_next=ttk.Button(nav_frame,text="Next",width=16)
    btn_next.pack(side="left",padx=15)
    def load_file():
        try:
            with open("input.json","r",encoding="utf-8") as f:lines=f.readlines()
        except FileNotFoundError:
            info_label.config(text="input.json not found in current folder")
            return
        blocks=[]
        for i,line in enumerate(lines,1):
            line=line.strip()
            if not line:continue
            try:blocks.append(json.loads(line))
            except json.JSONDecodeError:
                messagebox.showerror("Parse Error",f"Invalid JSON at line {i}")
                return
        candidates=[]
        i=0
        while i<len(blocks)-2:
            p1=blocks[i];ex=blocks[i+1];p2=blocks[i+2]
            if p1.get("label")=="p" and ex.get("label")=="exclude" and p2.get("label")=="p":
                txt2=p2.get("text","")
                if txt2 and txt2[0].islower():
                    candidates.append({"prev_idx":i,"cont_idx":i+2,"prev_text":p1.get("text",""),"cont_text":txt2,"excl_text":ex.get("text",""),"prev_page":p1.get("page","?"),"cont_page":p2.get("page","?")})
                    i+=3
                    continue
            i+=1
        if not candidates:
            info_label.config(text="No potential broken paragraphs found")
            return
        root.blocks=blocks
        root.candidates=candidates
        root.selections=[False]*len(candidates)
        root.offset=0
        refresh_page()
    def refresh_page():
        total=len(root.candidates)
        start=root.offset
        end=min(start+ROWS,total)
        info_label.config(text=f"Showing {start+1}–{end} of {total}")
        for i in range(ROWS):
            row,left,right,var=root.row_widgets[i]
            idx=start+i
            if idx<total:
                cand=root.candidates[idx]
                prev=cand["prev_text"];cont=cand["cont_text"]
                left_part=prev[-38:] if len(prev)>=38 else prev
                right_part=cont[:38] if len(cont)>=38 else cont
                left.config(text=left_part)
                right.config(text=right_part)
                var.set(root.selections[idx])
                set_row_selected(row,var.get())
                row.pack(fill="x",pady=4)
            else:row.pack_forget()
    def save_state_from_ui():
        start=root.offset
        for i in range(ROWS):
            idx=start+i
            if idx<len(root.selections):root.selections[idx]=root.row_widgets[i][3].get()
    def go_next():
        save_state_from_ui()
        if root.offset+ROWS<len(root.candidates):
            root.offset+=ROWS
            refresh_page()
    def go_prev():
        save_state_from_ui()
        if root.offset-ROWS>=0:
            root.offset-=ROWS
            refresh_page()
    btn_next.config(command=go_next)
    btn_prev.config(command=go_prev)
    load_file()
    root.mainloop()

def save_all(root):
    if not root.blocks or not root.candidates:return
    start=root.offset
    for i in range(ROWS):
        idx=start+i
        if idx<len(root.selections):
            root.selections[idx]=root.row_widgets[i][3].get()
    blocks=root.blocks[:]
    merges=[]
    for i,selected in enumerate(root.selections):
        if selected:
            cand=root.candidates[i]
            merges.append((cand["prev_idx"],cand["cont_idx"],cand["prev_idx"]+1))
    merges.sort(key=lambda x:x[0],reverse=True)
    for prev_idx,cont_idx,excl_idx in merges:
        blocks[prev_idx]["text"]+=" "+blocks[cont_idx]["text"]
        del blocks[excl_idx:cont_idx+1]
    save_path=filedialog.asksaveasfilename(title="Save merged file",initialfile="merged.json",defaultextension=".json",filetypes=[("JSON Lines","*.json"),("All files","*.*")])
    if not save_path:return
    try:
        with open(save_path,"w",encoding="utf-8") as f:
            for block in blocks:
                json.dump(block,f,ensure_ascii=False,separators=(", ",": "))
                f.write("\n")
        messagebox.showinfo("Done",f"Saved successfully:\n{save_path}")
    except Exception as e:
        messagebox.showerror("Save failed",f"Could not write file:\n{str(e)}")

if __name__=="__main__":
    main()

