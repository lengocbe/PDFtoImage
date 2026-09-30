"""Windows desktop interface for the standalone PDF-to-image converter."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from pdf_to_image.converter import PdfConversionError, convert_pages, get_page_count
from pdf_to_image.page_selection import PageSelectionError, parse_page_selection


class PdfToImageApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PDF sang ảnh")
        self.minsize(650, 440)
        self.resizable(False, False)
        self.pdf_path = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.format_value = tk.StringVar(value="PNG")
        self.mode = tk.StringVar(value="all")
        self.pages_value = tk.StringVar()
        self.page_count = 0
        self.status = tk.StringVar(value="Chọn một file PDF để bắt đầu.")
        self.progress = tk.DoubleVar(value=0)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=20)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="PDF sang ảnh", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Mỗi trang PDF sẽ thành một ảnh riêng, giữ nguyên tỉ lệ trang.").pack(anchor="w", pady=(3, 18))

        file_box = ttk.LabelFrame(outer, text="PDF nguồn", padding=10)
        file_box.pack(fill="x")
        ttk.Entry(file_box, textvariable=self.pdf_path, state="readonly").pack(side="left", fill="x", expand=True)
        ttk.Button(file_box, text="Chọn PDF", command=self.choose_pdf).pack(side="left", padx=(10, 0))
        self.page_label = ttk.Label(file_box, text="Chưa chọn file")
        self.page_label.pack(side="left", padx=(12, 0))

        mode_box = ttk.LabelFrame(outer, text="Trang cần xuất", padding=10)
        mode_box.pack(fill="x", pady=(12, 0))
        ttk.Radiobutton(mode_box, text="Xuất toàn bộ trang", variable=self.mode, value="all", command=self.update_page_state).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(mode_box, text="Chỉ xuất các trang này:", variable=self.mode, value="selected", command=self.update_page_state).grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.pages_entry = ttk.Entry(mode_box, textvariable=self.pages_value, width=37, state="disabled")
        self.pages_entry.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(8, 0))
        ttk.Label(mode_box, text="Ví dụ: 1, 3, 5-8").grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(3, 0))

        options = ttk.Frame(outer)
        options.pack(fill="x", pady=(14, 0))
        ttk.Label(options, text="Định dạng ảnh:").pack(side="left")
        ttk.Combobox(options, textvariable=self.format_value, values=("PNG", "JPG"), state="readonly", width=8).pack(side="left", padx=(8, 28))
        ttk.Label(options, text="Chất lượng: 200 DPI").pack(side="left")

        output_box = ttk.LabelFrame(outer, text="Thư mục xuất", padding=10)
        output_box.pack(fill="x", pady=(12, 0))
        ttk.Entry(output_box, textvariable=self.output_folder, state="readonly").pack(side="left", fill="x", expand=True)
        ttk.Button(output_box, text="Chọn thư mục", command=self.choose_output_folder).pack(side="left", padx=(10, 0))

        ttk.Progressbar(outer, variable=self.progress, maximum=100).pack(fill="x", pady=(18, 5))
        ttk.Label(outer, textvariable=self.status).pack(anchor="w")
        self.convert_button = ttk.Button(outer, text="Xuất ảnh", command=self.start_conversion)
        self.convert_button.pack(anchor="e", pady=(12, 0))

    def choose_pdf(self) -> None:
        path = filedialog.askopenfilename(title="Chọn file PDF", filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        try:
            self.page_count = get_page_count(path)
        except PdfConversionError as error:
            messagebox.showerror("PDF không hợp lệ", str(error))
            return
        self.pdf_path.set(path)
        self.page_label.configure(text=f"{self.page_count} trang")
        if not self.output_folder.get():
            self.output_folder.set(str(Path(path).parent))
        self.status.set("PDF hợp lệ. Chọn trang và thư mục xuất.")

    def choose_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Chọn thư mục xuất ảnh")
        if folder:
            self.output_folder.set(folder)

    def update_page_state(self) -> None:
        self.pages_entry.configure(state="normal" if self.mode.get() == "selected" else "disabled")

    def start_conversion(self) -> None:
        try:
            pages = self._selected_pages()
            if not self.output_folder.get():
                raise PdfConversionError("Hãy chọn thư mục xuất ảnh.")
            self.convert_button.configure(state="disabled")
            self.progress.set(0)
            self.status.set("Đang xuất ảnh...")
            threading.Thread(target=self._convert_worker, args=(pages,), daemon=True).start()
        except (PdfConversionError, PageSelectionError) as error:
            messagebox.showerror("Không thể xuất ảnh", str(error))

    def _selected_pages(self) -> list[int]:
        if not self.pdf_path.get() or self.page_count < 1:
            raise PdfConversionError("Hãy chọn file PDF hợp lệ trước.")
        if self.mode.get() == "all":
            return list(range(1, self.page_count + 1))
        return parse_page_selection(self.pages_value.get(), self.page_count)

    def _convert_worker(self, pages: list[int]) -> None:
        try:
            outputs = convert_pages(
                self.pdf_path.get(), self.output_folder.get(), pages,
                self.format_value.get().lower(), self._progress_callback,
            )
            self.after(0, lambda: self._conversion_finished(outputs))
        except Exception as error:  # Send library errors safely to the UI thread.
            self.after(0, lambda: self._conversion_failed(str(error)))

    def _progress_callback(self, current: int, total: int, _: Path) -> None:
        self.after(0, lambda: self._set_progress(current, total))

    def _set_progress(self, current: int, total: int) -> None:
        self.progress.set(current * 100 / total)
        self.status.set(f"Đã xuất {current}/{total} ảnh...")

    def _conversion_finished(self, outputs: list[Path]) -> None:
        self.convert_button.configure(state="normal")
        self.status.set(f"Hoàn tất: đã xuất {len(outputs)} ảnh.")
        messagebox.showinfo("Hoàn tất", f"Đã xuất {len(outputs)} ảnh vào:\n{self.output_folder.get()}")

    def _conversion_failed(self, message: str) -> None:
        self.convert_button.configure(state="normal")
        self.status.set("Xuất ảnh không thành công.")
        messagebox.showerror("Không thể xuất ảnh", message)


if __name__ == "__main__":
    PdfToImageApp().mainloop()

