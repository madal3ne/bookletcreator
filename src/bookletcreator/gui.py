from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .cli import FOUR_UP_PARTIAL_STRATEGIES, PAPER_SIZES, SHEET_LAYOUTS, convert_booklet
from .text_layout import SIZE_UNITS


SIGNATURE_CHOICES = ["None", "4", "8", "12", "16", "20", "24", "32"]


class BookletCreatorGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("BookletCreator")
        self.root.geometry("820x470")
        self.root.resizable(False, False)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.add_numbers = tk.BooleanVar(value=False)
        self.start_number = tk.StringVar(value="1")
        self.skip_numbering_pages = tk.StringVar(value="0")
        self.number_font_size = tk.StringVar(value="11")
        self.bottom_margin = tk.StringVar(value="18")
        self.paper_size = tk.StringVar(value="AUTO")
        self.paper_width = tk.StringVar()
        self.paper_height = tk.StringVar()
        self.paper_unit = tk.StringVar(value="MM")
        self.text_page_size = tk.StringVar(value="A5")
        self.text_page_width = tk.StringVar()
        self.text_page_height = tk.StringVar()
        self.text_page_unit = tk.StringVar(value="MM")
        self.body_font_size = tk.StringVar(value="12")
        self.text_margin = tk.StringVar(value="54")
        self.line_spacing = tk.StringVar(value="16")
        self.inner_margin = tk.StringVar(value="0")
        self.sheet_layout = tk.StringVar(value="BOOKLET")
        self.four_up_partial_strategy = tk.StringVar(value="BLANK_BACK")
        self.signature_size = tk.StringVar(value="None")
        self.combine_signatures = tk.BooleanVar(value=False)
        self.only_combined = tk.BooleanVar(value=False)
        self.show_map = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill="both", expand=True)

        files = ttk.LabelFrame(frame, text="Files", padding=10)
        files.grid(row=0, column=0, sticky="we")
        ttk.Label(files, text="Input PDF or Text").grid(row=0, column=0, sticky="w")
        ttk.Entry(files, textvariable=self.input_path, width=72).grid(row=1, column=0, sticky="we", padx=(0, 8))
        ttk.Button(files, text="Browse", command=self.pick_input).grid(row=1, column=1)
        ttk.Label(files, text="Output PDF / Folder").grid(row=2, column=0, sticky="w", pady=(10, 0))
        ttk.Entry(files, textvariable=self.output_path, width=72).grid(row=3, column=0, sticky="we", padx=(0, 8))
        ttk.Button(files, text="Browse", command=self.pick_output).grid(row=3, column=1)
        files.columnconfigure(0, weight=1)

        notebook = ttk.Notebook(frame)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(14, 0))

        booklet_layout = ttk.Frame(notebook, padding=12)
        notebook.add(booklet_layout, text="Layout")
        paper_values = ["AUTO", "CUSTOM", *PAPER_SIZES.keys()]
        ttk.Label(booklet_layout, text="Booklet Paper").grid(row=0, column=0, sticky="w")
        ttk.Combobox(booklet_layout, textvariable=self.paper_size, values=paper_values, width=12, state="readonly").grid(row=1, column=0, padx=(0, 12))
        ttk.Label(booklet_layout, text="Inner Margin").grid(row=0, column=1, sticky="w")
        ttk.Entry(booklet_layout, textvariable=self.inner_margin, width=12).grid(row=1, column=1, padx=(0, 12))
        ttk.Label(booklet_layout, text="Sheet Layout").grid(row=0, column=2, sticky="w")
        ttk.Combobox(booklet_layout, textvariable=self.sheet_layout, values=list(SHEET_LAYOUTS), width=14, state="readonly").grid(row=1, column=2, padx=(0, 12))
        ttk.Label(booklet_layout, text="Signature Size").grid(row=0, column=3, sticky="w")
        ttk.Combobox(booklet_layout, textvariable=self.signature_size, values=SIGNATURE_CHOICES, width=12, state="readonly").grid(row=1, column=3)
        ttk.Label(booklet_layout, text="4-up Partial").grid(row=2, column=0, sticky="w", pady=(10, 0))
        ttk.Combobox(
            booklet_layout,
            textvariable=self.four_up_partial_strategy,
            values=list(FOUR_UP_PARTIAL_STRATEGIES),
            width=20,
            state="readonly",
        ).grid(row=3, column=0, padx=(0, 12))
        ttk.Label(booklet_layout, text="Custom Width").grid(row=2, column=1, sticky="w", pady=(10, 0))
        ttk.Entry(booklet_layout, textvariable=self.paper_width, width=12).grid(row=3, column=1, padx=(0, 12))
        ttk.Label(booklet_layout, text="Custom Height").grid(row=2, column=2, sticky="w", pady=(10, 0))
        ttk.Entry(booklet_layout, textvariable=self.paper_height, width=12).grid(row=3, column=2, padx=(0, 12))
        ttk.Label(booklet_layout, text="Unit").grid(row=2, column=3, sticky="w", pady=(10, 0))
        ttk.Combobox(booklet_layout, textvariable=self.paper_unit, values=list(SIZE_UNITS.keys()), width=10, state="readonly").grid(row=3, column=3, padx=(0, 12))

        text_layout = ttk.Frame(notebook, padding=12)
        notebook.add(text_layout, text="Text Input")
        ttk.Label(text_layout, text="Text Page Size").grid(row=0, column=0, sticky="w")
        ttk.Combobox(text_layout, textvariable=self.text_page_size, values=["CUSTOM", *list(PAPER_SIZES.keys())], width=14, state="readonly").grid(row=1, column=0, padx=(0, 12))
        ttk.Label(text_layout, text="Body Font Size").grid(row=0, column=1, sticky="w")
        ttk.Entry(text_layout, textvariable=self.body_font_size, width=12).grid(row=1, column=1, padx=(0, 12))
        ttk.Label(text_layout, text="Margin").grid(row=0, column=2, sticky="w")
        ttk.Entry(text_layout, textvariable=self.text_margin, width=12).grid(row=1, column=2, padx=(0, 12))
        ttk.Label(text_layout, text="Line Spacing").grid(row=0, column=3, sticky="w")
        ttk.Entry(text_layout, textvariable=self.line_spacing, width=12).grid(row=1, column=3)
        ttk.Label(text_layout, text="Custom Width").grid(row=2, column=0, sticky="w", pady=(10, 0))
        ttk.Entry(text_layout, textvariable=self.text_page_width, width=12).grid(row=3, column=0, padx=(0, 12))
        ttk.Label(text_layout, text="Custom Height").grid(row=2, column=1, sticky="w", pady=(10, 0))
        ttk.Entry(text_layout, textvariable=self.text_page_height, width=12).grid(row=3, column=1, padx=(0, 12))
        ttk.Label(text_layout, text="Unit").grid(row=2, column=2, sticky="w", pady=(10, 0))
        ttk.Combobox(text_layout, textvariable=self.text_page_unit, values=list(SIZE_UNITS.keys()), width=10, state="readonly").grid(row=3, column=2, padx=(0, 12))

        numbering = ttk.Frame(notebook, padding=12)
        notebook.add(numbering, text="Page Numbers")
        ttk.Checkbutton(numbering, text="Add page numbers", variable=self.add_numbers).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(numbering, text="Start").grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Entry(numbering, textvariable=self.start_number, width=8).grid(row=2, column=0, padx=(0, 12))
        ttk.Label(numbering, text="Skip First Pages").grid(row=1, column=1, sticky="w", pady=(10, 0))
        ttk.Entry(numbering, textvariable=self.skip_numbering_pages, width=12).grid(row=2, column=1, padx=(0, 12))
        ttk.Label(numbering, text="Number Font").grid(row=1, column=2, sticky="w", pady=(10, 0))
        ttk.Entry(numbering, textvariable=self.number_font_size, width=12).grid(row=2, column=2, padx=(0, 12))
        ttk.Label(numbering, text="Bottom Margin").grid(row=1, column=3, sticky="w", pady=(10, 0))
        ttk.Entry(numbering, textvariable=self.bottom_margin, width=12).grid(row=2, column=3)

        output = ttk.Frame(notebook, padding=12)
        notebook.add(output, text="Output")
        ttk.Checkbutton(output, text="Combine signatures into one PDF", variable=self.combine_signatures).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(output, text="Only combined output (no per-signature files)", variable=self.only_combined).grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Checkbutton(output, text="Show spread mapping in console", variable=self.show_map).grid(row=2, column=0, sticky="w", pady=(8, 0))

        action_bar = ttk.Frame(frame)
        action_bar.grid(row=2, column=0, sticky="we", pady=(14, 0))
        ttk.Button(action_bar, text="Create Booklet", command=self.create_booklet).pack(side="left")

        self.status = tk.StringVar(value="Ready")
        ttk.Label(action_bar, textvariable=self.status).pack(side="left", padx=(16, 0))

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

    def pick_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose input PDF or text file",
            filetypes=[("Supported files", "*.pdf *.txt"), ("PDF files", "*.pdf"), ("Text files", "*.txt"), ("All files", "*.*")],
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

    def _optional_float(self, value: str) -> float | None:
        raw = value.strip()
        if not raw:
            return None
        return float(raw)

    def create_booklet(self) -> None:
        in_path = self.input_path.get().strip()
        out_path = self.output_path.get().strip()

        if not in_path:
            messagebox.showerror("Missing input", "Please select an input PDF or text file.")
            return

        try:
            results, combined = convert_booklet(
                input_pdf=Path(in_path),
                output_pdf=Path(out_path) if out_path else None,
                add_page_numbers=self.add_numbers.get(),
                start_number=int(self.start_number.get()),
                skip_numbering_pages=int(self.skip_numbering_pages.get()),
                font_size=float(self.number_font_size.get()),
                bottom_margin=float(self.bottom_margin.get()),
                paper_size=self.paper_size.get(),
                paper_width=self._optional_float(self.paper_width.get()),
                paper_height=self._optional_float(self.paper_height.get()),
                paper_unit=self.paper_unit.get(),
                text_page_size=self.text_page_size.get(),
                text_page_width=self._optional_float(self.text_page_width.get()),
                text_page_height=self._optional_float(self.text_page_height.get()),
                text_page_unit=self.text_page_unit.get(),
                body_font_size=float(self.body_font_size.get()),
                text_margin=float(self.text_margin.get()),
                line_spacing=float(self.line_spacing.get()),
                inner_margin=float(self.inner_margin.get()),
                sheet_layout=self.sheet_layout.get(),
                four_up_partial_strategy=self.four_up_partial_strategy.get(),
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
