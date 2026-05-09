from __future__ import annotations
import sqlite3
import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QSizePolicy, QFileDialog,
    QComboBox, QDateEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSlot, QDate

from core.download_manager import DownloadManager
from core.job import DownloadJob, JobStatus


DB_PATH = os.path.join(os.path.expanduser("~"), ".pixarchive", "history.db")


def _ensure_db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            url         TEXT NOT NULL,
            site        TEXT,
            status      TEXT,
            files_done  INTEGER DEFAULT 0,
            videos_done INTEGER DEFAULT 0,
            started_at  TEXT,
            finished_at TEXT,
            output_dir  TEXT
        )
    """)
    # Migration: add videos_done if upgrading from older schema
    try:
        con.execute("ALTER TABLE history ADD COLUMN videos_done INTEGER DEFAULT 0")
        con.commit()
    except Exception:
        pass  # column already exists
    return con


def _record_job(job: DownloadJob) -> int | None:
    """Insert a new history row and return its row id."""
    try:
        con = _ensure_db()
        cur = con.execute(
            "INSERT INTO history (url, site, status, files_done, started_at, output_dir) VALUES (?,?,?,?,?,?)",
            (job.url, job.site, job.status.value, 0, datetime.now().isoformat(),
             job.opts.output_dir or ""),
        )
        row_id = cur.lastrowid
        con.commit()
        con.close()
        return row_id
    except Exception:
        return None


def _finish_record(row_id: int, status: str, files_done: int, videos_done: int = 0):
    """Update history with real file/video counts on completion."""
    try:
        con = _ensure_db()
        con.execute(
            "UPDATE history SET status=?, files_done=?, videos_done=?, finished_at=? WHERE id=?",
            (status, files_done, videos_done, datetime.now().isoformat(), row_id),
        )
        con.commit()
        con.close()
    except Exception:
        pass


class HistoryRow(QFrame):
    def __init__(self, row: tuple, parent=None):
        super().__init__(parent)
        # Support both old (8-col) and new (9-col) schema rows
        if len(row) == 9:
            rid, url, site, status, files_done, videos_done, started_at, finished_at, output_dir = row
        else:
            rid, url, site, status, files_done, started_at, finished_at, output_dir = row
            videos_done = 0
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedHeight(64)
        self.setStyleSheet(
            "HistoryRow { background-color: palette(base); border: 1px solid palette(midlight); border-radius: 6px; }"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # Site badge
        site_lbl = QLabel(site or "url")
        site_lbl.setStyleSheet(
            "background: palette(highlight); color: palette(highlighted-text); border-radius:4px; padding:1px 7px; font-size:8pt; font-weight:bold;"
        )
        site_lbl.setFixedWidth(70)
        site_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(site_lbl)

        # URL + meta
        info = QVBoxLayout()
        info.setSpacing(2)
        url_lbl = QLabel(url)
        url_lbl.setStyleSheet("font-size:9pt;")
        url_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info.addWidget(url_lbl)
        started_str = started_at[:16].replace("T", "  ") if started_at else "—"
        images_done = files_done - videos_done
        if videos_done > 0 and images_done > 0:
            files_str = f"{images_done} image{'s' if images_done != 1 else ''}, {videos_done} video{'s' if videos_done != 1 else ''}"
        elif videos_done > 0:
            files_str = f"{videos_done} video{'s' if videos_done != 1 else ''}"
        else:
            files_str = f"{files_done} file{'s' if files_done != 1 else ''}" 
        meta_lbl = QLabel(f"{files_str}  ·  started {started_str}")
        meta_lbl.setStyleSheet("color: palette(mid); font-size:8pt;")
        info.addWidget(meta_lbl)
        layout.addLayout(info, stretch=1)

        # Status badge
        STATUS_STYLE = {
            "done":      "background: palette(shadow); color: palette(highlighted-text);",
            "error":     "background: palette(bright-text); color: palette(base);",
            "cancelled": "background: palette(midlight); color: palette(mid);",
        }
        st_style = STATUS_STYLE.get(status or "", "background: palette(mid); color: palette(window-text);")
        status_lbl = QLabel(status or "—")
        status_lbl.setStyleSheet(f"{st_style} border-radius:4px; padding:1px 7px; font-size:8pt; font-weight:bold;")
        layout.addWidget(status_lbl)

        # Open folder
        if output_dir and os.path.isdir(output_dir):
            btn = QPushButton("Open folder")
            btn.setFixedHeight(26)
            btn.setStyleSheet("font-size:8pt; padding:0 8px;")
            btn.clicked.connect(lambda: (
                os.startfile(output_dir) if os.name == "nt"
                else os.system(f'xdg-open "{output_dir}"')
            ))
            layout.addWidget(btn)


class HistoryPanel(QWidget):
    def __init__(self, manager: DownloadManager = None):
        super().__init__()
        self.manager = manager
        self._page = 0
        self._page_size = 100
        self._total_count = 0
        self._use_date_from = False
        self._build_ui()
        self._load()
        if manager:
            manager.job_added.connect(self._on_job_added)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setObjectName("dialog_header")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(12, 10, 12, 10)
        tb.setSpacing(8)

        title = QLabel("Download History")
        title.setStyleSheet("font-weight:bold; font-size:11pt; color: palette(link);")
        tb.addWidget(title)

        self.result_count = QLabel("")
        self.result_count.setStyleSheet("color: palette(mid); font-size:9pt;")
        tb.addWidget(self.result_count)

        tb.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter by URL or site…")
        self.search.setFixedWidth(180)
        self.search.setFixedHeight(28)
        self.search.textChanged.connect(self._on_filter_changed)
        tb.addWidget(self.search)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All statuses", "done", "error", "cancelled"])
        self.status_filter.setFixedHeight(28)
        self.status_filter.currentTextChanged.connect(self._on_filter_changed)
        tb.addWidget(self.status_filter)

        # Date range
        date_lbl = QLabel("From:")
        date_lbl.setStyleSheet("color: palette(mid); font-size:8pt;")
        tb.addWidget(date_lbl)
        self.date_from = QDateEdit()
        self.date_from.setFixedHeight(28)
        self.date_from.setCalendarPopup(True)
        self.date_from.setEnabled(False)   # enabled only when toggle is on
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setSpecialValueText("Any")
        self.date_from.setMinimumDate(QDate(2020, 1, 1))
        self.date_from.dateChanged.connect(self._on_filter_changed)
        tb.addWidget(self.date_from)

        self.date_from_check = QPushButton("×")
        self.date_from_check.setCheckable(True)
        self.date_from_check.setFixedSize(22, 28)
        self.date_from_check.setToolTip("Enable/disable date-from filter")
        self.date_from_check.toggled.connect(self._on_date_toggle)
        tb.addWidget(self.date_from_check)

        btn_export = QPushButton("Export…")
        btn_export.setFixedHeight(28)
        btn_export.clicked.connect(self._export)
        tb.addWidget(btn_export)

        btn_clear = QPushButton("Clear all")
        btn_clear.setFixedHeight(28)
        btn_clear.clicked.connect(self._clear_all)
        tb.addWidget(btn_clear)

        layout.addWidget(toolbar)

        # Pagination bar (hidden when not needed)
        page_bar = QWidget()
        page_bar.setObjectName("dialog_header")
        pb = QHBoxLayout(page_bar)
        pb.setContentsMargins(12, 4, 12, 4)
        pb.setSpacing(8)
        self.btn_prev = QPushButton("← Prev")
        self.btn_prev.setFixedHeight(24)
        self.btn_prev.clicked.connect(self._prev_page)
        pb.addWidget(self.btn_prev)
        self.page_lbl = QLabel("")
        self.page_lbl.setStyleSheet("color: palette(mid); font-size:8pt;")
        pb.addWidget(self.page_lbl)
        self.btn_next = QPushButton("Next →")
        self.btn_next.setFixedHeight(24)
        self.btn_next.clicked.connect(self._next_page)
        pb.addWidget(self.btn_next)
        pb.addStretch()
        self._page_bar = page_bar
        layout.addWidget(page_bar)
        page_bar.setVisible(False)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.rows_widget = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_widget)
        self.rows_layout.setContentsMargins(12, 12, 12, 12)
        self.rows_layout.setSpacing(6)
        self.rows_layout.addStretch()

        scroll.setWidget(self.rows_widget)
        layout.addWidget(scroll, stretch=1)

        self.empty_lbl = QLabel("No download history yet.")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet("color: palette(mid); font-size:10pt;")
        layout.addWidget(self.empty_lbl)

    def _build_query(self) -> tuple[str, list]:
        """Return (WHERE clause fragment, params) for current filters."""
        query    = self.search.text().strip().lower()
        status_f = self.status_filter.currentText()
        sql = "WHERE 1=1"
        params: list = []
        if query:
            sql += " AND (lower(url) LIKE ? OR lower(site) LIKE ?)"
            params += [f"%{query}%", f"%{query}%"]
        if status_f != "All statuses":
            sql += " AND status = ?"
            params.append(status_f)
        if self._use_date_from:
            date_str = self.date_from.date().toString("yyyy-MM-dd")
            sql += " AND started_at >= ?"
            params.append(date_str)
        return sql, params

    def _on_filter_changed(self):
        self._page = 0
        self._load()

    def _on_date_toggle(self, checked: bool):
        self._use_date_from = checked
        self.date_from.setEnabled(checked)
        self.date_from_check.setText("✓" if checked else "×")
        self._page = 0
        self._load()

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._load()

    def _next_page(self):
        max_page = max(0, (self._total_count - 1) // self._page_size)
        if self._page < max_page:
            self._page += 1
            self._load()

    def _load(self):
        where, params = self._build_query()

        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            con = _ensure_db()
            # Total matching count
            self._total_count = con.execute(
                f"SELECT COUNT(*) FROM history {where}", params
            ).fetchone()[0]

            # Paginated rows
            offset = self._page * self._page_size
            rows = con.execute(
                f"SELECT * FROM history {where} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [self._page_size, offset]
            ).fetchall()
            con.close()
        except Exception:
            rows = []
            self._total_count = 0

        # Result count label
        if self._total_count:
            total_pages = max(1, (self._total_count + self._page_size - 1) // self._page_size)
            self.result_count.setText(
                f"{self._total_count} result{'s' if self._total_count != 1 else ''}")
        else:
            self.result_count.setText("")

        # Pagination bar
        total_pages = max(1, (self._total_count + self._page_size - 1) // self._page_size)
        show_pages  = total_pages > 1
        self._page_bar.setVisible(show_pages)
        if show_pages:
            self.page_lbl.setText(f"Page {self._page + 1} of {total_pages}")
            self.btn_prev.setEnabled(self._page > 0)
            self.btn_next.setEnabled(self._page < total_pages - 1)

        if not rows:
            self.empty_lbl.setVisible(True)
            self.rows_layout.addStretch()
            return

        self.empty_lbl.setVisible(False)
        for row in rows:
            self.rows_layout.addWidget(HistoryRow(row))
        self.rows_layout.addStretch()

    def _export(self):
        import json, csv
        from PyQt6.QtWidgets import QFileDialog
        path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export history",
            "gallery-dl-history",
            "CSV files (*.csv);;JSON files (*.json)"
        )
        if not path:
            return
        try:
            con = _ensure_db()
            rows = con.execute("SELECT * FROM history ORDER BY id DESC").fetchall()
            con.close()
            cols = ["id", "url", "site", "status", "files_done", "videos_done",
                    "started_at", "finished_at", "output_dir"]
            if path.endswith(".json") or "JSON" in selected_filter:
                data = [dict(zip(cols, row)) for row in rows]
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
            else:
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(cols)
                    writer.writerows(rows)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Exported", f"History exported to:\n{path}")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Export failed", str(e))

    def _clear_all(self):
        resp = QMessageBox.question(
            self, "Clear history",
            "Delete all download history? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return
        try:
            con = _ensure_db()
            con.execute("DELETE FROM history")
            con.commit()
            con.close()
        except Exception:
            pass
        self._page = 0
        self._load()

    @pyqtSlot(object)
    def _on_job_added(self, job: DownloadJob):
        row_id = _record_job(job)
        if row_id is not None:
            # FIX #4: pass real file count when job finishes
            job.finished.connect(
                lambda: (_finish_record(row_id, job.status.value, job.files_done, job.videos_done), self._load())
            )
