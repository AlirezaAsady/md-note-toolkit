#!/usr/bin/env python3
"""Tkinter frontend for md_batch.run_batch."""

import queue
import threading
import tkinter as tk
from tkinter import filedialog, ttk

import md_batch

DEFAULT_MODE = md_batch.DEFAULT_MODE
NEW_FILE = md_batch.NEW_FILE
WINDOW_SIZE = "1000x720"


class App:
    def __init__(self, root):
        self.root = root
        self.busy = False
        self.last_report = []
        self.events = queue.Queue()
        self.controls = []
        root.title("Markdown batch processor")
        root.geometry(WINDOW_SIZE)
        root.minsize(720, 580)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=3)
        root.rowconfigure(2, weight=2)
        root.protocol("WM_DELETE_WINDOW", self.close)

        files = ttk.LabelFrame(root, text="File paths — one per line")
        files.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        files.columnconfigure(0, weight=1)
        files.rowconfigure(0, weight=1)
        self.paths_box = tk.Text(files, wrap="none", undo=True, font=("Consolas", 11))
        self.paths_box.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(files, command=self.paths_box.yview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(files, orient="horizontal", command=self.paths_box.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.paths_box.config(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.controls.append(self.paths_box)

        buttons = ttk.Frame(files)
        buttons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=6)
        for label, command in (
            ("Add files", self.browse),
            ("Paste paths", self.paste),
            ("Clear list", self.clear_paths),
        ):
            button = ttk.Button(buttons, text=label, command=command)
            button.pack(side="left", padx=4)
            self.controls.append(button)

        options = ttk.LabelFrame(root, text="Operation — applied to each listed file")
        options.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.mode_var = tk.StringVar(value=DEFAULT_MODE)
        self.new_var = tk.BooleanVar(value=NEW_FILE)
        modes = ttk.Frame(options)
        modes.pack(fill="x", padx=8, pady=8)
        for label, mode in (
            ("Reverse", "reverse"), ("Color", "color"),
            ("RTL", "rtl"), ("Color + RTL", "forward"),
        ):
            button = ttk.Radiobutton(
                modes, text=label, value=mode, variable=self.mode_var,
            )
            button.pack(side="left", padx=(0, 20))
            self.controls.append(button)
        self.new_check = ttk.Checkbutton(
            options, text="Write to new file (single-step modes only)",
            variable=self.new_var,
        )
        self.new_check.pack(anchor="w", padx=8, pady=(0, 4))
        self.output_var = tk.StringVar()
        ttk.Label(options, textvariable=self.output_var).pack(anchor="w", padx=8, pady=(0, 8))
        self.mode_var.trace_add("write", self.update_output)
        self.new_var.trace_add("write", self.update_output)

        logs = ttk.LabelFrame(root, text="Log — warnings and errors are shown per file")
        logs.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        logs.columnconfigure(0, weight=1)
        logs.rowconfigure(0, weight=1)
        self.log_box = tk.Text(logs, state="disabled", wrap="word", font=("Consolas", 10))
        self.log_box.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(logs, command=self.log_box.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_box.config(yscrollcommand=scrollbar.set)

        actions = ttk.Frame(root)
        actions.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(actions, textvariable=self.status_var).pack(side="left")
        self.run_button = ttk.Button(actions, text="Run batch", command=self.run)
        self.run_button.pack(side="right")
        self.controls.append(self.run_button)
        self.update_output()

    def update_output(self, *_):
        combined = self.mode_var.get() == "forward"
        if combined and self.new_var.get():
            self.new_var.set(False)
        self.new_check.config(state="disabled" if combined or self.busy else "normal")
        if self.new_var.get():
            suffix = {
                "reverse": ".raw.md", "color": md_batch.md_color_gui.OUT_SUFFIX,
                "rtl": md_batch.md_rtl_advance_gui.OUT_SUFFIX,
            }[self.mode_var.get()]
            self.output_var.set(f"New output: {suffix}; originals kept; existing outputs refused.")
        else:
            self.output_var.set("Replace original (default): same name; previous file goes to Recycle Bin.")

    def log(self, message):
        self.log_box.config(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def paths(self):
        return [
            line.strip().strip('"')
            for line in self.paths_box.get("1.0", "end-1c").splitlines()
            if line.strip().strip('"')
        ]

    def add_paths(self, paths):
        entries = list(dict.fromkeys(self.paths() + [str(path).strip().strip('"') for path in paths]))
        entries = [path for path in entries if path]
        self.paths_box.delete("1.0", "end")
        self.paths_box.insert("1.0", "\n".join(entries))
        self.status_var.set(f"Listed: {len(entries)}")

    def browse(self):
        paths = filedialog.askopenfilenames(
            parent=self.root, filetypes=[("Markdown", "*.md"), ("All files", "*.*")],
        )
        if paths:
            self.add_paths(paths)

    def paste(self):
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            self.log("Clipboard is empty or not text")
            return
        self.add_paths(text.splitlines())

    def clear_paths(self):
        self.paths_box.delete("1.0", "end")
        self.status_var.set("Ready")

    def run(self):
        if self.busy:
            return
        paths = self.paths()
        if not paths:
            self.log("No input paths")
            return
        mode, new_file = self.mode_var.get(), self.new_var.get()
        self.busy = True
        self.last_report = []
        for control in self.controls:
            control.config(state="disabled")
        self.update_output()
        self.status_var.set("Running…")
        self.log(f"Starting: {mode}; files={len(paths)}; new_file={new_file}")
        threading.Thread(target=self.worker, args=(paths, mode, new_file), daemon=False).start()
        self.root.after(50, self.drain_events)

    def worker(self, paths, mode, new_file):
        try:
            report = md_batch.run_batch(
                paths, mode, new_file, log=lambda message: self.events.put(("log", message)),
            )
            self.events.put(("done", report))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def drain_events(self):
        while True:
            try:
                kind, payload = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "log":
                self.log(payload)
            else:
                if kind == "done":
                    self.last_report = payload
                    failed = sum(item.status == "error" for item in payload)
                    warned = sum(bool(item.warnings) for item in payload)
                    self.status_var.set(f"Finished: {len(payload)} files; failed={failed}; warned={warned}")
                else:
                    self.log("Error: " + payload)
                    self.status_var.set("Failed")
                self.busy = False
                for control in self.controls:
                    control.config(state="normal")
                self.update_output()
        if self.busy:
            self.root.after(50, self.drain_events)

    def close(self):
        if self.busy:
            self.log("Processing is still running; wait before closing.")
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
