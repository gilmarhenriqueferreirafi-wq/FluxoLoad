from __future__ import annotations

import os
import threading
import webbrowser
from pathlib import Path
from tkinter import END, StringVar, Tk, messagebox
from tkinter import filedialog, ttk

from .downloader import DownloadError, DownloadManager


class FluxoLoadApp:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("FluxoLoad")
        self.root.geometry("760x500")
        self.root.minsize(620, 420)

        self.url = StringVar()
        self.status = StringVar(value="Pronto para baixar")
        self.destination = StringVar(
            value=str(Path.home() / "Downloads" / "FluxoLoad")
        )
        self.manager = DownloadManager()
        self._build_style()
        self._build_ui()

    def _build_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("vista")
        except Exception:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", foreground="#5f6368")
        style.configure("Action.TButton", padding=(12, 7))

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=24)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="FluxoLoad", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Downloads locais, simples e leves — sem navegador embutido.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 20))

        search = ttk.LabelFrame(outer, text="Pesquisar ou colar um link", padding=14)
        search.pack(fill="x")
        url_entry = ttk.Entry(search, textvariable=self.url)
        url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        url_entry.bind("<Return>", lambda _event: self.download())
        ttk.Button(
            search, text="Pesquisar", style="Action.TButton", command=self.search
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            search, text="Baixar", style="Action.TButton", command=self.download
        ).pack(side="left")

        destination = ttk.LabelFrame(outer, text="Pasta de destino", padding=14)
        destination.pack(fill="x", pady=16)
        ttk.Entry(destination, textvariable=self.destination).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        ttk.Button(destination, text="Escolher", command=self.choose_destination).pack(
            side="left"
        )

        downloads = ttk.LabelFrame(outer, text="Download atual", padding=14)
        downloads.pack(fill="both", expand=True)
        self.progress = ttk.Progressbar(downloads, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(0, 10))
        self.details = ttk.Label(downloads, text="Nenhum download em andamento")
        self.details.pack(anchor="w")

        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(16, 0))
        ttk.Label(footer, textvariable=self.status).pack(side="left")
        ttk.Button(footer, text="Abrir downloads", command=self.open_destination).pack(
            side="right"
        )

    def search(self) -> None:
        query = self.url.get().strip()
        if not query:
            query = "YouTube"
        if query.startswith(("http://", "https://")):
            webbrowser.open(query)
        else:
            webbrowser.open(
                "https://www.google.com/search?q="
                + query.replace(" ", "+")
                + "+video"
            )
        self.status.set("Pesquisa aberta no navegador padrão")

    def choose_destination(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.destination.get())
        if selected:
            self.destination.set(selected)

    def download(self) -> None:
        url = self.url.get().strip()
        if not url.startswith(("http://", "https://")):
            messagebox.showwarning("Link necessário", "Cole uma URL válida para baixar.")
            return

        self.progress.configure(value=0)
        self.status.set("Preparando download...")
        self.details.configure(text=url)
        self._set_download_controls(False)
        threading.Thread(
            target=self._download_worker,
            args=(url, self.destination.get()),
            daemon=True,
        ).start()

    def _download_worker(self, url: str, destination: str) -> None:
        try:
            result = self.manager.download(
                url,
                Path(destination),
                progress=lambda data: self.root.after(0, self._update_progress, data),
            )
        except DownloadError as error:
            self.root.after(0, self._download_failed, str(error))
            return
        self.root.after(0, self._download_finished, result)

    def _update_progress(self, data: dict) -> None:
        percent = data.get("percent", 0)
        self.progress.configure(value=percent)
        self.details.configure(text=data.get("text", "Baixando..."))
        self.status.set("Baixando...")

    def _download_finished(self, path: Path) -> None:
        self.progress.configure(value=100)
        self.details.configure(text=path.name)
        self.status.set("Download concluído")
        self._set_download_controls(True)

    def _download_failed(self, error: str) -> None:
        self.status.set("Não foi possível concluir o download")
        self._set_download_controls(True)
        messagebox.showerror("Erro no download", error)

    def _set_download_controls(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for child in self.root.winfo_children():
            self._set_children_state(child, state)

    def _set_children_state(self, widget, state: str) -> None:
        try:
            if isinstance(widget, ttk.Button):
                widget.configure(state=state)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._set_children_state(child, state)

    def open_destination(self) -> None:
        path = Path(self.destination.get())
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)

    def run(self) -> None:
        self.root.mainloop()
