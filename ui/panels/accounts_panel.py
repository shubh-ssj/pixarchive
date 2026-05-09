import json
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QComboBox, QMessageBox,
    QFormLayout, QDialog, QDialogButtonBox, QCheckBox
)
from PyQt6.QtCore import Qt


# Sites that support username/password auth
AUTH_SITES = [
    ("DeviantArt",      "oauth",    "Run OAuth flow via gallery-dl --oauth deviantart"),
    ("pixiv",           "oauth",    "Run OAuth flow via gallery-dl --oauth pixiv"),
    ("Flickr",          "oauth",    "Run OAuth flow via gallery-dl --oauth flickr"),
    ("Reddit",          "oauth",    "Run OAuth flow via gallery-dl --oauth reddit"),
    ("SmugMug",         "oauth",    "Run OAuth flow via gallery-dl --oauth smugmug"),
    ("Tumblr",          "oauth",    "Run OAuth flow via gallery-dl --oauth tumblr"),
    ("Instagram",       "cookies",  "Export cookies from your browser"),
    ("Pinterest",       "cookies",  "Export cookies from your browser"),
    ("Facebook",        "cookies",  "Export cookies from your browser"),
    ("Patreon",         "cookies",  "Export cookies from your browser"),
    ("Fantia",          "cookies",  "Export cookies from your browser"),
    ("pixivFANBOX",    "cookies",  "Export cookies from your browser"),
    ("Boosty",          "cookies",  "Export cookies from your browser"),
    ("Twitter/X",       "cookies",  "Export cookies from your browser"),
    ("Danbooru",        "credentials", "Username + API key"),
    ("Newgrounds",      "credentials", "Username + password"),
    ("Bluesky",         "credentials", "Username + password/app password"),
    ("Zerochan",        "credentials", "Username + password"),
    ("MangaDex",        "credentials", "Username + password"),
]

CREDS_PATH = os.path.join(os.path.expanduser("~"), ".pixarchive", "accounts.json")
# NOTE: credentials are stored in plain text. A future version could use the
# system keyring (via the `keyring` package) for credential storage. The
# warning banner in AccountsPanel informs users of the current behaviour.


def _load_accounts() -> dict:
    if os.path.exists(CREDS_PATH):
        try:
            with open(CREDS_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_accounts(data: dict):
    os.makedirs(os.path.dirname(CREDS_PATH), exist_ok=True)
    with open(CREDS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class CredentialDialog(QDialog):
    def __init__(self, site: str, auth_type: str, existing: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Configure — {site}")
        self.setMinimumWidth(400)
        self.setStyleSheet(parent.styleSheet() if parent else "")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        if auth_type == "credentials":
            form = QFormLayout()
            self.username = QLineEdit(existing.get("username", "") if existing else "")
            self.password = QLineEdit(existing.get("password", "") if existing else "")
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            form.addRow("Username", self.username)
            form.addRow("Password / API key", self.password)
            layout.addLayout(form)

        elif auth_type == "cookies":
            info = QLabel(
                "For cookie-based sites, use your browser's cookie export extension "
                "(e.g. 'Get cookies.txt LOCALLY') and point gallery-dl to the file, "
                "or use --cookies-from-browser in the Network options tab."
            )
            info.setWordWrap(True)
            info.setStyleSheet("color: palette(text); font-size:9pt;")
            layout.addWidget(info)

            form = QFormLayout()
            self.cookie_file = QLineEdit(existing.get("cookie_file", "") if existing else "")
            self.cookie_file.setPlaceholderText("Path to cookies.txt")
            btn = QPushButton("Browse…")
            from PyQt6.QtWidgets import QFileDialog
            btn.clicked.connect(lambda: self.cookie_file.setText(
                QFileDialog.getOpenFileName(self, "cookies.txt")[0]
            ))
            row = QHBoxLayout()
            row.addWidget(self.cookie_file)
            row.addWidget(btn)
            form.addRow("Cookies file", row)
            layout.addLayout(form)
            self.username = None
            self.password = None

        elif auth_type == "oauth":
            info = QLabel(
                "OAuth sites require running the gallery-dl OAuth flow in a terminal.\n\n"
                f"Run:  gallery-dl oauth:{site.lower().replace('/', '').replace(' ', '')}\n\n"
                "A browser window will open. Authorize gallery-dl, then copy the token "
                "into your config file. The Config panel can help you edit it."
            )
            info.setWordWrap(True)
            info.setStyleSheet("color: palette(text); font-size:9pt; font-family:monospace;")
            layout.addWidget(info)
            self.username = None
            self.password = None

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> dict:
        data = {}
        if hasattr(self, "username") and self.username:
            data["username"] = self.username.text()
        if hasattr(self, "password") and self.password:
            data["password"] = self.password.text()
        if hasattr(self, "cookie_file") and self.cookie_file:
            data["cookie_file"] = self.cookie_file.text()
        return data


class AccountRow(QFrame):
    def __init__(self, site: str, auth_type: str, note: str, account_data: dict | None, parent_panel, parent=None):
        super().__init__(parent)
        self.site = site
        self.auth_type = auth_type
        self.note = note
        self.account_data = account_data
        self.parent_panel = parent_panel

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedHeight(56)
        self.setStyleSheet("AccountRow { background-color: palette(alternateBase); border: 1px solid palette(mid); border-radius: 6px; }")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        AUTH_COLORS = {
            "oauth":       ("palette(dark)", "palette(highlight)", "OAuth"),
            "cookies":     ("palette(shadow)", "palette(text)", "Cookies"),
            "credentials": ("palette(dark)", "palette(link)", "Login"),
        }
        bg, fg, label = AUTH_COLORS.get(auth_type, ("#45475a", "#cdd6f4", auth_type))
        badge = QLabel(label)
        badge.setStyleSheet(f"background:{bg}; color:{fg}; border-radius:4px; padding:1px 6px; font-size:8pt; font-weight:bold;")
        badge.setFixedWidth(55)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(badge)

        info = QVBoxLayout()
        info.setSpacing(2)
        name_lbl = QLabel(site)
        name_lbl.setStyleSheet("font-weight:bold; font-size:10pt;")
        info.addWidget(name_lbl)
        note_lbl = QLabel(note)
        note_lbl.setStyleSheet("color: palette(mid); font-size:8pt;")
        info.addWidget(note_lbl)
        layout.addLayout(info, stretch=1)

        # Status
        if account_data:
            status = QLabel("Configured")
            status.setStyleSheet("color: palette(highlight); font-size:8pt;")  # green = configured, intentional semantic
        else:
            status = QLabel("Not configured")
            status.setStyleSheet("color: palette(mid); font-size:8pt;")
        layout.addWidget(status)

        btn = QPushButton("Configure…" if not account_data else "Edit…")
        btn.setFixedHeight(26)
        btn.setStyleSheet("font-size:8pt; padding:0 10px;")
        btn.clicked.connect(self._configure)
        layout.addWidget(btn)

    def _configure(self):
        dlg = CredentialDialog(self.site, self.auth_type, self.account_data, self)
        if dlg.exec():
            data = dlg.get_data()
            accounts = _load_accounts()
            accounts[self.site] = data
            _save_accounts(accounts)
            self.parent_panel._reload()


class AccountsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._reload()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QWidget()
        toolbar.setObjectName("dialog_header")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(12, 10, 12, 10)

        title = QLabel("Accounts & Authentication")
        title.setStyleSheet("font-weight:bold; font-size:11pt; color: palette(link);")
        tb.addWidget(title)
        tb.addStretch()

        info = QLabel("Credentials are stored in ~/.pixarchive/accounts.json")
        info.setStyleSheet("color: palette(mid); font-size:8pt;")
        tb.addWidget(info)

        layout.addWidget(toolbar)

        # Warning banner
        warn = QLabel(
            "⚠  Credentials are stored in plain text. For sensitive sites, prefer cookie files or OAuth tokens."
        )
        warn.setStyleSheet(
            "background: palette(alternateBase); color: palette(text); font-size:8pt; padding:6px 14px;"
            "border-bottom:1px solid palette(mid);"
        )
        layout.addWidget(warn)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.rows_widget = QWidget()
        self.rows_widget.setStyleSheet("background-color: palette(base);")
        self.rows_layout = QVBoxLayout(self.rows_widget)
        self.rows_layout.setContentsMargins(12, 12, 12, 12)
        self.rows_layout.setSpacing(6)
        self.rows_layout.addStretch()

        scroll.setWidget(self.rows_widget)
        layout.addWidget(scroll, stretch=1)

    def _reload(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        accounts = _load_accounts()
        for site, auth_type, note in AUTH_SITES:
            row = AccountRow(site, auth_type, note, accounts.get(site), self)
            self.rows_layout.addWidget(row)

        self.rows_layout.addStretch()
