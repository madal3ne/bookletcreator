from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .cli import PAPER_SIZES, convert_booklet


SIGNATURE_CHOICES = ["None", "4", "8", "12", "16", "20", "24", "32"]


class BookletCreatorGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("BookletCreator")
        self.root.geometry("660x470")
        self.root.resizable(False, False)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.add_numbers = tk.BooleanVar(value=False)
        self.start_number = tk.StringVar(value="1")
        self.font_size = tk.StringVar(value="11")
        self.bottom_margin = tk.StringVar(value="18")
        self.paper_size = tk.StringVar(value="AUTO")
        self.inner_margin = tk.StringVar(value="0")
        self.signature_size = tk.StringVar(value="None")
        self.combine_signatures = tk.BooleanVar(value=False)
        self.only_combined = tk.BooleanVar(value=False)
        self.show_map = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Input PDF").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.input_path, width=60).grid(row=1, column=0, sticky="we", padx=(0, 8))
        ttk.Button(frame, text="Browse", command=self.pick_input).grid(row=1, column=1)

        ttk.Label(frame, text="Output PDF / Folder").grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=self.output_path, width=60).grid(row=3, column=0, sticky="we", padx=(0, 8))
        ttk.Button(frame, text="Browse", command=self.pick_output).grid(row=3, column=1)

        ttk.Checkbutton(frame, text="Add page numbers", variable=self.add_numbers).grid(row=4, column=0, sticky="w", pady=(12, 0))

        numbers = ttk.Frame(frame)
        numbers.grid(row=5, column=0, columnspan=2, sticky="we", pady=(6, 0))
        ttk.Label(numbers, text="Start").grid(row=0, column=0, sticky="w")
        ttk.Entry(numbers, textvariable=self.start_number, width=8).grid(row=1, column=0, padx=(0, 12))
        ttk.Label(numbers, text="Font").grid(row=0, column=1, sticky="w")
        ttk.Entry(numbers, textvariable=self.font_size, width=8).grid(row=1, column=1, padx=(0, 12))
        ttk.Label(numbers, text="Bottom Margin").grid(row=0, column=2, sticky="w")
        ttk.Entry(numbers, textvariable=self.bottom_margin, width=12).grid(row=1, column=2)

        layout = ttk.Frame(frame)
        layout.grid(row=6, column=0, columnspan=2, sticky="we", pady=(14, 0))
        ttk.Label(layout, text="Paper").grid(row=0, column=0, sticky="w")
        paper_values = ["AUTO", *PAPER_SIZES.keys()]
        ttk.Combobox(layout, textvariable=self.paper_size, values=paper_values, width=12, state="readonly").grid(row=1, column=0, padx=(0, 12))
        ttk.Label(layout, text="Inner Margin").grid(row=0, column=1, sticky="w")
        ttk.Entry(layout, textvariable=self.inner_margin, width=12).grid(row=1, column=1, padx=(0, 12))
        ttk.Label(layout, text="Signature Size").grid(row=0, column=2, sticky="w")
        ttk.Combobox(layout, textvariable=self.signature_size, values=SIGNATURE_CHOICES, width=12, state="readonly").grid(row=1, column=2)

        ttk.Checkbutton(frame, text="Combine signatures into one PDF", variable=self.combine_signatures).grid(row=7, column=0, sticky="w", pady=(12, 0))
        ttk.Checkbutton(frame, text="Only combined output (no per-signature files)", variable=self.only_combined).grid(row=8, column=0, sticky="w", pady=(6, 0))

        ttk.Checkbutton(frame, text="Show spread mapping in console", variable=self.show_map).grid(row=9, column=0, sticky="w", pady=(6, 0))

        ttk.Button(frame, text="Create Booklet", command=self.create_booklet).grid(row=10, column=0, sticky="w", pady=(18, 0))

        self.status = tk.StringVar(value="Ready")
        ttk.Label(frame, textvariable=self.status).grid(row=11, column=0, columnspan=2, sticky="w", pady=(14, 0))

        frame.columnconfigure(0, weight=1)

    def pick_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose input PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if path:
            self.input_path.set(path)
            suggested = Path(path).with_name(f"{Path(path).stem}_booklet.pdf")
            if not self.output_path.get().strip():
                self.output_path.set(str(suggested))

    def pick_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Choose output PDF or base name",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if path:
            self.output_path.set(path)

    def _signature_value(self) -> int:
        raw = self.signature_size.get().strip()
        if not raw or raw.lower() == "none":
            return 0
        return int(raw)

    def create_booklet(self) -> None:
        in_path = self.input_path.get().strip()
        out_path = self.output_path.get().strip()

        if not in_path:
            messagebox.showerror("Missing input", "Please select an input PDF.")
            return

        try:
            results, combined = convert_booklet(
                input_pdf=Path(in_path),
                output_pdf=Path(out_path) if out_path else None,
                add_page_numbers=self.add_numbers.get(),
                start_number=int(self.start_number.get()),
                font_size=float(self.font_size.get()),
                bottom_margin=float(self.bottom_margin.get()),
                paper_size=self.paper_size.get(),
                inner_margin=float(self.inner_margin.get()),
                signature_size=self._signature_value(),
                combine_signatures=self.combine_signatures.get(),
                only_combined=self.only_combined.get(),
                show_map=self.show_map.get(),
                dry_run=False,
            )
        except Exception as exc:
            self.status.set("Failed")
            messagebox.showerror("Error", str(exc))
            return

        total_files = len(results) + (1 if combined is not None else 0)
        self.status.set(f"Created {total_files} file(s)")
        first = results[0]
        summary_lines = [
            f"Created {total_files} file(s).",
            "",
            f"Input pages: {sum(r.input_pages for r in results)}",
            f"Added blanks: {sum(r.added_blanks for r in results)}",
            f"Output folder: {first.output_path.parent}",
        ]
        if combined is not None:
            summary_lines.append(f"Combined output: {combined.output_path.name}")
        summary = "\n".join(summary_lines)
        messagebox.showinfo("Success", summary)


def main() -> None:
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    BookletCreatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
