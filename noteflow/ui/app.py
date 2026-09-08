"""
Интерфейс NoteFlow Workspace на CustomTkinter в ультрачистом светлом стиле (Notion / Linear / Minimalist Light).
"""

from datetime import datetime
import os
import webbrowser
from tkinter import messagebox, ttk
import customtkinter as ctk
from noteflow.config import EXPORTS_DIR
from noteflow.core.graph_engine import KnowledgeGraphEngine
from noteflow.core.markdown_parser import MarkdownParser
from noteflow.storage.db import NoteFlowDB

# Принудительный чистый светлый режим
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


class NoteFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("NoteFlow — Минималистичное рабочее пространство & Граф знаний")
        self.geometry("1120x740")
        self.minsize(980, 640)

        # Конфигурация светлых цветов в стиле Linear
        self.configure(fg_color="#F8FAFC")

        self.db = NoteFlowDB()
        self.current_doc_id = None

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self, corner_radius=8, fg_color="#FFFFFF", border_width=1, border_color="#E2E8F0")
        self.tabview.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")

        self.tab_editor = self.tabview.add("📝 1. Документы & Редактор")
        self.tab_kanban = self.tabview.add("📋 2. Задачи (Linear Kanban)")
        self.tab_graph = self.tabview.add("🕸️ 3. Граф знаний & Backlinks")
        self.tab_export = self.tabview.add("📤 4. Экспорт & Публикация")

        self._build_tab_editor()
        self._build_tab_kanban()
        self._build_tab_graph()
        self._build_tab_export()

    # ================= 1. TAB EDITOR =================
    def _build_tab_editor(self):
        tab = self.tab_editor
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Боковая панель списка заметок (Sidebar)
        side = ctk.CTkFrame(tab, width=280, fg_color="#F1F5F9", corner_radius=6, border_width=1, border_color="#E2E8F0")
        side.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=0)
        side.grid_rowconfigure(2, weight=1)

        # Поиск и кнопка создания
        top_side = ctk.CTkFrame(side, fg_color="transparent")
        top_side.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.search_entry = ctk.CTkEntry(top_side, placeholder_text="Поиск заметок...", height=32, fg_color="#FFFFFF", border_color="#CBD5E1")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_doc_list())

        btn_new = ctk.CTkButton(top_side, text="+", width=32, height=32, fg_color="#0F172A", hover_color="#334155", command=self.create_new_doc)
        btn_new.pack(side="right")

        # Дерево документов
        self.doc_listbox = ttk.Treeview(side, columns=("title", "words"), show="headings", height=15)
        self.doc_listbox.heading("title", text="Заголовок")
        self.doc_listbox.heading("words", text="Слов")
        self.doc_listbox.column("title", width=180)
        self.doc_listbox.column("words", width=60, anchor="e")
        self.doc_listbox.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.doc_listbox.bind("<<TreeviewSelect>>", self._on_doc_select)

        # Правая часть: Редактор
        editor_pane = ctk.CTkFrame(tab, fg_color="#FFFFFF", corner_radius=6, border_width=1, border_color="#E2E8F0")
        editor_pane.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        editor_pane.grid_columnconfigure(0, weight=1)
        editor_pane.grid_rowconfigure(2, weight=1)

        # Заголовок заметки и Папка
        head_pane = ctk.CTkFrame(editor_pane, fg_color="transparent")
        head_pane.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 6))

        self.title_entry = ctk.CTkEntry(head_pane, font=ctk.CTkFont(size=20, weight="bold"), height=40, fg_color="#FFFFFF", border_color="#E2E8F0")
        self.title_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_save = ctk.CTkButton(head_pane, text="Сохранить", width=100, fg_color="#059669", hover_color="#047857", command=self.save_current_doc)
        btn_save.pack(side="right")

        # Метрики документа
        self.lbl_stats = ctk.CTkLabel(editor_pane, text="Слов: 0 | Символов: 0 | Время чтения: ~1 мин", text_color="#64748B", font=ctk.CTkFont(size=12))
        self.lbl_stats.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 8))

        # Текстовое поле Markdown
        self.content_text = ctk.CTkTextbox(editor_pane, font=ctk.CTkFont(family="Consolas", size=13), fg_color="#FFFFFF", border_width=1, border_color="#E2E8F0")
        self.content_text.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.content_text.bind("<KeyRelease>", self._update_stats_live)

        self.load_doc_list()

    def load_doc_list(self):
        q = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
        docs = self.db.get_documents(search=q)

        for row in self.doc_listbox.get_children():
            self.doc_listbox.delete(row)

        for d in docs:
            self.doc_listbox.insert("", "end", iid=str(d["id"]), values=(d["title"], d["word_count"]))

        if docs and self.current_doc_id is None:
            self._select_doc_by_id(docs[0]["id"])

    def _select_doc_by_id(self, doc_id):
        docs = self.db.get_documents()
        doc = next((x for x in docs if x["id"] == doc_id), None)
        if doc:
            self.current_doc_id = doc["id"]
            self.title_entry.delete(0, "end")
            self.title_entry.insert(0, doc["title"])
            self.content_text.delete("1.0", "end")
            self.content_text.insert("1.0", doc["content"])
            self._update_stats_live(None)

    def _on_doc_select(self, event):
        sel = self.doc_listbox.selection()
        if sel:
            doc_id = int(sel[0])
            self._select_doc_by_id(doc_id)

    def _update_stats_live(self, event):
        text = self.content_text.get("1.0", "end")
        words, chars, read_time = MarkdownParser.calculate_stats(text)
        self.lbl_stats.configure(text=f"Слов: {words} | Символов: {chars} | Время чтения: ~{read_time} мин")

    def create_new_doc(self):
        self.current_doc_id = None
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, "Новый документ")
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", "# Новый документ\n\nНачните писать здесь...")
        self._update_stats_live(None)

    def save_current_doc(self):
        title = self.title_entry.get().strip() or "Без названия"
        content = self.content_text.get("1.0", "end").strip()
        self.current_doc_id = self.db.save_document(self.current_doc_id, title, content)
        self.load_doc_list()
        messagebox.showinfo("Сохранено", f"Документ '{title}' успешно сохранен!")

    # ================= 2. TAB KANBAN =================
    def _build_tab_kanban(self):
        tab = self.tab_kanban
        tab.grid_columnconfigure((0, 1, 2, 3), weight=1)
        tab.grid_rowconfigure(1, weight=1)

        columns = [
            ("To Do (К выполнению)", "TODO", "#64748B"),
            ("In Progress (В работе)", "IN_PROGRESS", "#0284C7"),
            ("Review (На проверке)", "REVIEW", "#D97706"),
            ("Done (Завершено)", "DONE", "#059669"),
        ]

        self.kanban_frames = {}

        for col_idx, (title, status, color) in enumerate(columns):
            col_frame = ctk.CTkFrame(tab, fg_color="#F8FAFC", corner_radius=8, border_width=1, border_color="#E2E8F0")
            col_frame.grid(row=1, column=col_idx, sticky="nsew", padx=6, pady=10)
            col_frame.grid_columnconfigure(0, weight=1)

            # Шапка колонки
            head = ctk.CTkFrame(col_frame, fg_color="transparent")
            head.pack(fill="x", padx=12, pady=10)
            ctk.CTkLabel(head, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=color).pack(side="left")

            card_container = ctk.CTkScrollableFrame(col_frame, fg_color="transparent")
            card_container.pack(fill="both", expand=True, padx=6, pady=(0, 6))
            self.kanban_frames[status] = card_container

        self.load_kanban_cards()

    def load_kanban_cards(self):
        tasks = self.db.get_tasks()
        for f in self.kanban_frames.values():
            for w in f.winfo_children():
                w.destroy()

        for t in tasks:
            status = t["status"]
            container = self.kanban_frames.get(status)
            if not container:
                continue

            card = ctk.CTkFrame(container, fg_color="#FFFFFF", corner_radius=6, border_width=1, border_color="#E2E8F0")
            card.pack(fill="x", pady=4, padx=2)

            ctk.CTkLabel(card, text=t["title"], font=ctk.CTkFont(size=12, weight="bold"), text_color="#0F172A", wraplength=200, justify="left").pack(anchor="w", padx=10, pady=(8, 4))
            
            prio_color = "#DC2626" if t["priority"] == "URGENT" else ("#EF4444" if t["priority"] == "HIGH" else "#059669")
            ctk.CTkLabel(card, text=f"Приоритет: {t['priority']}", text_color=prio_color, font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=10, pady=(0, 8))

    # ================= 3. TAB GRAPH =================
    def _build_tab_graph(self):
        tab = self.tab_graph
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Граф перекрестных связей и обратных ссылок (Backlinks)", font=ctk.CTkFont(size=16, weight="bold"), text_color="#0F172A").pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(tab, text="Анализирует двунаправленные ссылки вида [[Заголовок Заметки]] между всеми документами базы.", text_color="#64748B", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=16, pady=(0, 16))

        docs = self.db.get_documents()
        graph = KnowledgeGraphEngine.build_graph(docs)

        stats_bar = ctk.CTkFrame(tab, fg_color="#F8FAFC", border_width=1, border_color="#E2E8F0")
        stats_bar.pack(fill="x", padx=16, pady=8)

        ctk.CTkLabel(stats_bar, text=f"Узлов графа: {graph['total_nodes']} | Связей (Edges): {graph['total_edges']}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#0F172A").pack(padx=16, pady=12)

        self.txt_links = ctk.CTkTextbox(tab, font=ctk.CTkFont(family="Consolas", size=12), fg_color="#FFFFFF", border_width=1, border_color="#E2E8F0")
        self.txt_links.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        lines = ["=== Обнаруженные перекрестные связи заметок ===\n"]
        for e in graph["edges"]:
            lines.append(f"• [{e['source']}] ➔ [[{e['target']}]]\n")
        self.txt_links.insert("1.0", "".join(lines))

    # ================= 4. TAB EXPORT =================
    def _build_tab_export(self):
        tab = self.tab_export
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Экспорт и верстка документации", font=ctk.CTkFont(size=16, weight="bold"), text_color="#0F172A").pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(tab, text="Экспорт текущей базы заметок в автономный HTML/PDF документ с чистой версткой Linear/Notion.", text_color="#64748B", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=16, pady=(0, 16))

        btn_html = ctk.CTkButton(tab, text="🌐 Сгенерировать чистую HTML-статью", height=40, fg_color="#0F172A", hover_color="#334155", command=self.export_html)
        btn_html.pack(anchor="w", padx=16, pady=8)

        self.lbl_export_res = ctk.CTkLabel(tab, text="Файлы сохраняются в data/exports/", text_color="#64748B")
        self.lbl_export_res.pack(anchor="w", padx=16, pady=8)

    def export_html(self):
        docs = self.db.get_documents()
        doc = docs[0] if docs else None
        if not doc:
            return

        body_html = MarkdownParser.to_html(doc["content"])
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>{doc['title']}</title>
<style>
  body {{ background: #fafaf9; color: #1c1917; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 780px; margin: 40px auto; padding: 20px; line-height: 1.7; }}
  h1 {{ font-size: 32px; font-weight: 800; border-bottom: 1px solid #e7e5e4; padding-bottom: 12px; margin-bottom: 24px; }}
  h2 {{ font-size: 22px; font-weight: 700; margin-top: 32px; margin-bottom: 12px; }}
  p {{ margin-bottom: 16px; color: #44403c; }}
  .wiki-link {{ background: #e0e7ff; color: #4338ca; padding: 2px 6px; border-radius: 4px; font-weight: 600; text-decoration: none; }}
  .task {{ padding: 4px 0; display: flex; align-items: center; gap: 8px; }}
  .task.done {{ color: #a8a29e; text-decoration: line-through; }}
  pre {{ background: #f5f5f4; border: 1px solid #e7e5e4; padding: 16px; border-radius: 8px; font-family: monospace; font-size: 13px; }}
</style>
</head>
<body>
  {body_html}
</body>
</html>"""
        out_file = EXPORTS_DIR / f"doc_{doc['id']}.html"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html)

        self.lbl_export_res.configure(text=f"Экспорт сохранен: {out_file.name}", text_color="#059669")
        webbrowser.open(out_file.as_uri())


if __name__ == "__main__":
    app = NoteFlowApp()
    app.mainloop()

