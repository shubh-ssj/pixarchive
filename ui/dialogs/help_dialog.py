from __future__ import annotations
import re

from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QWidget, QLabel, QLineEdit, QScrollArea,
    QFrame, QPushButton, QSizePolicy, QTextBrowser
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont

# ── Help content ──────────────────────────────────────────────────────────────
# Each page is (title, icon, html_body)

PAGES: list[tuple[str, str, str]] = [

("Getting started", "🚀", """
<h2>Getting started</h2>
<p>PixArchive is an image downloader utility for archiving galleries and collections
from 200+ websites. It uses <b>gallery-dl</b> as its download engine — a powerful tool that
downloads image galleries and collections from 200+ websites.</p>

<h3>Prerequisites</h3>
<ol>
  <li>Install Python 3.11 or newer.</li>
  <li>Install gallery-dl:<br>
      <code>pip install gallery-dl</code></li>
  <li>Install PyQt6:<br>
      <code>pip install PyQt6</code></li>
  <li>Run the GUI:<br>
      <code>python main.py</code></li>
</ol>

<h3>Your first download</h3>
<ol>
  <li>Paste a URL into the bar at the top of the <b>Download</b> panel.</li>
  <li>The site banner will appear immediately, confirming gallery-dl supports the URL
      and showing what authentication (if any) is needed.</li>
  <li>Choose an output directory in the <b>Output</b> tab, or leave it blank to use
      the path defined in your gallery-dl config.</li>
  <li>Click <b>Download Now</b>. The log pane will show live output.</li>
</ol>

<h3>Quick tips</h3>
<ul>
  <li>Copy a gallery URL to your clipboard, then bring the window to the front —
      the URL will be pasted automatically if the field is empty.</li>
  <li>You can drag and drop URLs or text files onto the Download panel.</li>
  <li>Use <b>+ Queue</b> to batch up several URLs before starting them all.</li>
  <li>Use a <b>Preset</b> to save your favourite option combinations.</li>
  <li>The <b>✕ close button</b> quits the app. The <b>minimise button</b> hides it to the
      system tray (if <i>Minimize to tray</i> is on in Settings). Click the tray icon to restore.</li>
  <li>To open links in a specific browser (e.g. Edge instead of Chrome), set
      <b>Settings → Advanced → Open links in</b>.</li>
</ul>
"""),

("URL detection", "◈", """
<h2>URL detection</h2>
<p>When you paste or type a URL, the app matches it against 70+ compiled patterns
covering every supported site. A banner appears below the URL bar showing:</p>
<ul>
  <li><b>Site name</b> — e.g. "pixiv", "Reddit"</li>
  <li><b>Capabilities</b> — what gallery-dl can download from that site</li>
  <li><b>Auth badge</b> — one of:</li>
</ul>
<table border="0" cellspacing="6">
  <tr><td><span style="background:#1e3a5f;color:#89b4fa;border-radius:4px;padding:2px 8px;">OAuth</span></td>
      <td>Requires OAuth token flow (DeviantArt, Flickr, Reddit, pixiv…)</td></tr>
  <tr><td><span style="background:#2a2010;color:#f9e2af;border-radius:4px;padding:2px 8px;">Cookies</span></td>
      <td>Needs browser cookies (Instagram, Patreon, Pinterest…)</td></tr>
  <tr><td><span style="background:#1e3a2f;color:#a6e3a1;border-radius:4px;padding:2px 8px;">Optional</span></td>
      <td>Works without auth, but auth unlocks more content</td></tr>
  <tr><td><span style="background:#252530;color:#6c7086;border-radius:4px;padding:2px 8px;">Public</span></td>
      <td>No authentication required</td></tr>
</table>
<p>Detection is purely local regex matching — no network requests are made until you click Download.</p>
"""),

("Download options", "⚙", """
<h2>Download options</h2>
<p>Options are grouped across four tabs in the Download panel.</p>

<h3>Output tab</h3>
<dl>
  <dt><b>Save directory</b></dt>
  <dd>Where files are saved. Leave blank to use the <code>base-directory</code> from your gallery-dl config.</dd>
  <dt><b>Filename pattern</b></dt>
  <dd>A gallery-dl format string controlling how files are named. See the <b>Filename patterns</b> help page.</dd>
  <dt><b>Pack into .zip</b></dt>
  <dd>Bundles the downloaded files into a single archive.</dd>
  <dt><b>Set modification time</b></dt>
  <dd>Sets the file's mtime to the original upload date from the site's metadata.</dd>
</dl>

<h3>Filters tab</h3>
<dl>
  <dt><b>Item filter</b></dt>
  <dd>Python expression evaluated against each item's metadata. Items that don't match are skipped.
      See the <b>Filter expressions</b> help page.</dd>
  <dt><b>Image filter</b></dt>
  <dd>Like item filter but applied per-image within a post (useful for multi-image posts).</dd>
  <dt><b>Index range</b></dt>
  <dd>Download only items at these 1-based positions, e.g. <code>1-20</code> or <code>1,5,10-15</code>.</dd>
  <dt><b>Chapter range</b></dt>
  <dd>For manga/chapter extractors: which chapters to download.</dd>
</dl>

<h3>Behaviour tab</h3>
<dl>
  <dt><b>Skip existing files</b></dt>
  <dd>Skips files that are already present in the output directory. Recommended on.</dd>
  <dt><b>Write metadata</b></dt>
  <dd>Saves a <code>.json</code> file alongside each download with all metadata gallery-dl collected.</dd>
  <dt><b>Write tags</b></dt>
  <dd>Writes tags to XMP/EXIF sidecar files.</dd>
  <dt><b>Dry run</b></dt>
  <dd>Simulates the download without writing any files — useful for testing filters and ranges.</dd>
  <dt><b>Verbose</b></dt>
  <dd>Passes <code>--verbose</code> to gallery-dl, which logs every HTTP request. Useful for debugging.</dd>
</dl>

<h3>Network tab</h3>
<dl>
  <dt><b>Retries</b></dt>
  <dd>How many times to retry a failed request. Default 4.</dd>
  <dt><b>Timeout</b></dt>
  <dd>HTTP request timeout in seconds. Default 30.</dd>
  <dt><b>Rate limit</b></dt>
  <dd>Throttle download speed, e.g. <code>500k</code> or <code>2M</code>.</dd>
  <dt><b>Cookies from browser</b></dt>
  <dd>Extracts cookies from your local browser profile. Needed for sites like Instagram and Patreon.</dd>
  <dt><b>Cookies file</b></dt>
  <dd>Path to a Netscape-format <code>cookies.txt</code> exported from a browser extension.</dd>
  <dt><b>Proxy</b></dt>
  <dd>HTTP/HTTPS proxy URL, e.g. <code>http://user:pass@host:port</code>.</dd>
</dl>
"""),

("Filename patterns", "{}", """
<h2>Filename patterns</h2>
<p>gallery-dl uses Python-style format strings to construct filenames and directories.
You can use any metadata key that the extractor exposes.</p>

<h3>Common tokens</h3>
<table border="0" cellspacing="0" cellpadding="6" width="100%">
  <tr style="background:#252535;"><td><code>{filename}</code></td><td>Original filename (no extension)</td></tr>
  <tr><td><code>{extension}</code></td><td>File extension</td></tr>
  <tr style="background:#252535;"><td><code>{category}</code></td><td>Site name, e.g. <code>pixiv</code>, <code>reddit</code></td></tr>
  <tr><td><code>{subcategory}</code></td><td>Extractor subtype, e.g. <code>user</code>, <code>tag</code></td></tr>
  <tr style="background:#252535;"><td><code>{id}</code></td><td>Item or post ID</td></tr>
  <tr><td><code>{title}</code></td><td>Gallery or post title</td></tr>
  <tr style="background:#252535;"><td><code>{num}</code></td><td>Sequence number within a gallery</td></tr>
  <tr><td><code>{date}</code></td><td>Upload date (datetime object)</td></tr>
  <tr style="background:#252535;"><td><code>{date:%Y-%m-%d}</code></td><td>Formatted date</td></tr>
  <tr><td><code>{user[name]}</code></td><td>Nested key access</td></tr>
  <tr style="background:#252535;"><td><code>{num:>04}</code></td><td>Zero-padded number: <code>0001</code></td></tr>
</table>

<h3>Examples</h3>
<pre style="background:#11111b; padding:10px; border-radius:6px; color:#a6adc8;">
# Default (flat)
{filename}.{extension}

# Per-artist folders
{category}/{user[name]}/{id}.{extension}

# Dated folders
{category}/{date:%Y-%m-%d}/{filename}.{extension}

# Manga pages
{manga}/{chapter:>03}/{page:>03}.{extension}

# Pixiv with artwork ID + page number
{user[id]}/{id}_p{num}.{extension}
</pre>

<p>Run with <b>Verbose</b> enabled and <b>Dry run</b> on to inspect the metadata keys
a specific extractor provides before writing your pattern.</p>
"""),

("Filter expressions", "⧖", """
<h2>Filter expressions</h2>
<p>Item and image filters are Python expressions evaluated against the metadata dictionary
gallery-dl produces for each item. Items where the expression evaluates to <code>False</code>
(or raises an exception) are skipped.</p>

<h3>Syntax</h3>
<p>Any valid Python expression. Access metadata keys as bare names:</p>
<pre style="background:#11111b; padding:10px; border-radius:6px; color:#a6adc8;">
width >= 1920
extension in ("jpg", "jpeg", "png")
score > 100
"landscape" in tags
date > datetime(2023, 1, 1)
</pre>

<h3>Combining conditions</h3>
<pre style="background:#11111b; padding:10px; border-radius:6px; color:#a6adc8;">
width >= 1920 and height >= 1080
"scenery" in tags and score > 50
extension == "gif" or extension == "mp4"
not "nsfw" in tags
</pre>

<h3>Site-specific examples</h3>
<pre style="background:#11111b; padding:10px; border-radius:6px; color:#a6adc8;">
# Pixiv — only bookmarked with 500+ views
bookmark_count > 0 and view_count > 500

# Danbooru — only 'safe' rated images
rating == "s"

# Reddit — only images (not videos)
extension in ("jpg", "jpeg", "png", "gif", "webp")

# Fur Affinity — only files larger than 100 KB
filesize > 100000
</pre>

<h3>Finding available keys</h3>
<p>Enable <b>Verbose</b> output and <b>Dry run</b>, then download a single item.
The log will show the full metadata dictionary for each item.</p>
"""),

("Presets", "★", """
<h2>Presets</h2>
<p>Presets save all your current option settings under a name so you can recall them later
with one click. They are stored in <code>~/.pixarchive/presets.json</code>.</p>

<h3>Built-in presets — site-specific</h3>
<table border="0" cellspacing="6" width="100%">
  <tr style="background:#252535;"><td><b>Pixiv – high-res originals</b></td>
      <td>Organised by user ID, enables metadata, increases retries and timeout.</td></tr>
  <tr><td><b>Reddit – images only</b></td>
      <td>Filters to common image extensions so videos and links are skipped.</td></tr>
  <tr style="background:#252535;"><td><b>Twitter/X – media archive</b></td>
      <td>Organises by author and tweet ID, saves metadata and timestamps.</td></tr>
  <tr><td><b>Instagram – posts &amp; reels</b></td>
      <td>Shortcode-based filenames, metadata, timestamps.</td></tr>
  <tr style="background:#252535;"><td><b>DeviantArt – full gallery</b></td>
      <td>Includes tags, metadata and modification time.</td></tr>
  <tr><td><b>ArtStation – portfolio</b></td>
      <td>Organised by username and title, longer timeout for large files.</td></tr>
  <tr style="background:#252535;"><td><b>Tumblr – blog archive</b></td>
      <td>Writes info JSON (preserves captions), metadata and timestamps.</td></tr>
  <tr><td><b>Flickr – photostream</b></td>
      <td>Human-readable folder names using path alias, metadata and timestamps.</td></tr>
  <tr style="background:#252535;"><td><b>Naver Webtoon</b></td>
      <td>Episode folders with zero-padded pages, info JSON and timestamps.</td></tr>
  <tr><td><b>Naver Webtoon – zipped episodes</b></td>
      <td>Same as above but each episode packed into a .zip for comic readers.</td></tr>
  <tr style="background:#252535;"><td><b>Manga chapter pack</b></td>
      <td>Packs chapters into .zip archives and writes info.json.</td></tr>
</table>

<h3>Built-in presets — workflow</h3>
<table border="0" cellspacing="6" width="100%">
  <tr><td><b>Dry run / preview</b></td>
      <td>Simulate mode with verbose output — see what would download without writing files.</td></tr>
  <tr style="background:#252535;"><td><b>Archive + metadata</b></td>
      <td>Metadata + modification time + info.json. Good general archiving preset.</td></tr>
  <tr><td><b>Full offline archive</b></td>
      <td>Everything on: metadata, tags, info.json, timestamps, max retries.</td></tr>
  <tr style="background:#252535;"><td><b>Images only – no videos</b></td>
      <td>Filters to jpg, png, gif, webp and similar. Skips video files.</td></tr>
  <tr><td><b>Videos only</b></td>
      <td>Filters to mp4, webm, mov and similar. Skips image files.</td></tr>
  <tr style="background:#252535;"><td><b>Latest 50 items</b></td>
      <td>Downloads only the first 50 items — useful for checking what's new.</td></tr>
  <tr><td><b>Slow connection / metered</b></td>
      <td>Caps speed at 200 kB/s, high retries and timeout. Good for mobile hotspots.</td></tr>
  <tr style="background:#252535;"><td><b>Resume interrupted</b></td>
      <td>Skip existing files, maximum retries and timeout. Picks up where a failed download left off.</td></tr>
  <tr><td><b>Quick grab – no extras</b></td>
      <td>No metadata, low retries, short timeout. When you just want the file fast.</td></tr>
</table>

<h3>Saving your own</h3>
<ol>
  <li>Configure the options tabs the way you want.</li>
  <li>Click <b>Save current…</b> in the preset bar.</li>
  <li>Give the preset a name and press OK.</li>
</ol>
<p>Built-in preset names are reserved — choosing one shows a warning asking you to pick a different name.
User presets can be deleted with the <b>Delete</b> button.</p>
"""),

("Queue & history", "◷", """
<h2>Queue &amp; history</h2>

<h3>Queue panel</h3>
<p>The queue shows all current and pending downloads as cards. Each card shows:</p>
<ul>
  <li>Site badge (coloured by site category)</li>
  <li>URL</li>
  <li>Progress bar and file count</li>
  <li>Status badge (queued / running / done / error / cancelled)</li>
  <li>Cancel button</li>
</ul>
<p>Use <b>Start all</b> to kick off all queued jobs, or <b>Clear finished</b> to tidy up.</p>

<h3>History panel</h3>
<p>Completed downloads are recorded automatically to a local SQLite database at
<code>~/.pixarchive/history.db</code>. Each record includes:</p>
<ul>
  <li>URL and site</li>
  <li>Status (done / error / cancelled)</li>
  <li>File count and start time</li>
  <li>Output directory</li>
</ul>
<p>You can filter history by URL/site name or by status, and open the output folder
directly from a history row.</p>
"""),

("Authentication", "🔐", """
<h2>Authentication</h2>
<p>Many sites require some form of authentication to access protected content.</p>

<h3>Browser cookies  <span style="background:#2a2010;color:#f9e2af;border-radius:4px;padding:1px 7px;font-size:9pt;">Cookies</span></h3>
<p>For sites like Instagram, Patreon, Pinterest, Twitter, Facebook, and Fantia:</p>
<ul>
  <li>Select your browser from the <b>Cookies from browser</b> dropdown in the Network tab.
      gallery-dl will extract cookies automatically.</li>
  <li>Alternatively, export a <code>cookies.txt</code> file using a browser extension
      (e.g. "Get cookies.txt LOCALLY") and point the <b>Cookies file</b> field to it.</li>
</ul>

<h3>OAuth  <span style="background:#1e3a5f;color:#89b4fa;border-radius:4px;padding:1px 7px;font-size:9pt;">OAuth</span></h3>
<p>For DeviantArt, Flickr, pixiv, Reddit, SmugMug, and Tumblr:</p>
<ol>
  <li>Open a terminal and run:<br>
      <code>gallery-dl oauth:deviantart</code>  (substitute the site name)</li>
  <li>A browser window opens — authorise gallery-dl.</li>
  <li>Copy the token shown and add it to your gallery-dl config
      (the <b>Config</b> panel can help).</li>
</ol>

<h3>Username &amp; password  <span style="background:#1e3a2f;color:#a6e3a1;border-radius:4px;padding:1px 7px;font-size:9pt;">Optional</span></h3>
<p>For sites like Danbooru, Sankaku, and Bluesky, go to the <b>Accounts</b> panel,
find the site, click <b>Configure…</b> and enter your credentials.
They're stored in <code>~/.pixarchive/accounts.json</code>.</p>

<p><b>Note:</b> Credentials are stored in plain text. For sensitive sites, prefer
cookie files or OAuth tokens.</p>
"""),

("Sites panel", "◈", """
<h2>Sites panel</h2>
<p>The Sites panel lists all 200+ sites that gallery-dl supports, sourced directly
from the official gallery-dl documentation.</p>

<h3>Browsing</h3>
<ul>
  <li><b>Search box</b> — filters by site name, URL, or capabilities as you type.</li>
  <li><b>Category filter</b> — narrows to a site category (Social Media, Art Platforms, Manga, etc.)</li>
  <li><b>Auth badge</b> — each card shows the authentication method required.</li>
</ul>

<h3>Launching a download</h3>
<p>Click any site card to pre-fill the Download panel's URL bar with the site's base URL
and switch to the Download panel. Replace the URL with the specific gallery or profile
you want to download.</p>

<h3>Categories</h3>
<ul>
  <li>Social Media</li>
  <li>Art Platforms</li>
  <li>Pixiv Ecosystem</li>
  <li>Creator / Patreon-style</li>
  <li>Imageboards / Booru</li>
  <li>Manga / Comics</li>
  <li>Image Hosts / File Sharing</li>
  <li>Photography</li>
  <li>Forums / Boards</li>
  <li>Japanese Sites</li>
  <li>Other / Misc</li>
</ul>
"""),

("Configuration", "⚙", """
<h2>Configuration</h2>
<p>gallery-dl uses a JSON config file for persistent settings. The GUI's Config panel
can read and write this file directly.</p>

<h3>Config file locations</h3>
<table border="0" cellspacing="4">
  <tr style="background:#252535;"><td><b>Windows</b></td>
      <td><code>%APPDATA%\\gallery-dl\\config.json</code></td></tr>
  <tr><td><b>Linux / macOS</b></td>
      <td><code>~/.config/gallery-dl/config.json</code></td></tr>
</table>

<h3>Config panel tabs</h3>
<dl>
  <dt><b>Common Settings</b></dt>
  <dd>Form-based editor for the most frequently used options: base directory,
      filename pattern, sleep, rate limit, retries, ugoira format, archive DB.</dd>
  <dt><b>Raw JSON</b></dt>
  <dd>Direct JSON editor. Useful for per-site overrides and advanced options.
      Changes here take precedence when you click Save.</dd>
</dl>

<h3>Per-site overrides</h3>
<p>gallery-dl supports nested configuration that applies only to a specific site.
In the raw JSON editor, this looks like:</p>
<pre style="background:#11111b; padding:10px; border-radius:6px; color:#a6adc8;">
{
  "extractor": {
    "pixiv": {
      "filename": "{user[id]}/{id}_p{num}.{extension}",
      "ugoira": { "ffmpeg-args": ["-vf", "fps=12"] }
    },
    "reddit": {
      "subreddit-metadata": true
    }
  }
}
</pre>
<p>Refer to the official gallery-dl documentation for a full list of per-site options.</p>
"""),

("Keyboard shortcuts", "⌨", """
<h2>Keyboard shortcuts</h2>
<table border="0" cellspacing="0" cellpadding="8" width="100%">
  <tr style="background:#252535;">
    <td><code>Ctrl+1</code></td><td>Switch to Download panel</td>
  </tr>
  <tr><td><code>Ctrl+2</code></td><td>Switch to Queue panel</td></tr>
  <tr style="background:#252535;">
    <td><code>Ctrl+3</code></td><td>Switch to History panel</td>
  </tr>
  <tr><td><code>Ctrl+4</code></td><td>Switch to Sites panel</td></tr>
  <tr style="background:#252535;">
    <td><code>Ctrl+5</code></td><td>Switch to Config panel</td>
  </tr>
  <tr><td><code>Ctrl+6</code></td><td>Switch to Accounts panel</td></tr>
  <tr style="background:#252535;">
    <td><code>Ctrl+N</code></td><td>New download (switch to Download panel)</td>
  </tr>
  <tr><td><code>Ctrl+Shift+V</code></td><td>Paste clipboard URL into download bar from anywhere</td></tr>
  <tr style="background:#252535;">
    <td><code>Ctrl+,</code></td><td>Open Settings</td>
  </tr>
  <tr><td><code>Ctrl+Q</code></td><td>Quit</td></tr>
  <tr style="background:#252535;">
    <td><code>F1</code></td><td>Open this Help window</td>
  </tr>
</table>
"""),

("Troubleshooting", "🛠", """
<h2>Troubleshooting</h2>

<h3>gallery-dl not found</h3>
<p>Make sure gallery-dl is installed and on your PATH:</p>
<pre style="background:#11111b; padding:8px; border-radius:6px; color:#a6adc8;">pip install gallery-dl
gallery-dl --version</pre>
<p>Or set the full path in <b>Settings → Advanced → gallery-dl executable</b>.</p>

<h3>Download fails immediately</h3>
<ul>
  <li>Enable <b>Verbose</b> and try again — the log will show the exact error from gallery-dl.</li>
  <li>Try the same URL in a terminal: <code>gallery-dl --verbose "URL"</code></li>
  <li>Check if the site requires authentication (see the site banner auth badge).</li>
</ul>

<h3>Login-required sites return empty results</h3>
<ul>
  <li>Use the <b>Cookies from browser</b> option in the Network tab.</li>
  <li>Make sure you're logged into the site in that browser.</li>
  <li>For OAuth sites, complete the OAuth flow from the Accounts panel instructions.</li>
</ul>

<h3>Files are downloading but ending up in the wrong folder</h3>
<p>Check the <b>Save directory</b> in the Output tab. If it's blank, gallery-dl uses
the <code>base-directory</code> from your config file (default: <code>./gallery-dl/</code>
relative to where you run the command).</p>

<h3>Rate limit / 429 errors</h3>
<ul>
  <li>Lower the rate limit in the Network tab, e.g. <code>200k</code>.</li>
  <li>Increase the sleep time in your gallery-dl config.</li>
  <li>Reduce concurrent downloads to 1 in Settings → Downloads.</li>
</ul>

<h3>Progress bar stays at 0%</h3>
<p>Progress is parsed from gallery-dl's log output using a regex pattern.
Some extractors don't print a <code>(N/M)</code> count, so progress may not
be trackable. The download is still running — watch the log pane.</p>

<h3>Still stuck?</h3>
<p>Check the <a href="https://github.com/mikf/gallery-dl/issues">gallery-dl issue tracker</a>
or the <a href="https://github.com/mikf/gallery-dl/discussions">discussions</a>.</p>
"""),

]


class HelpDialog(QDialog):
    """Searchable help reference with a sidebar and rich-text content panes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help — PixArchive")
        self.setMinimumSize(820, 580)
        self.resize(900, 640)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(48)
        header.setObjectName("dialog_header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(18, 0, 18, 0)
        hl.setSpacing(12)

        title = QLabel("Help")
        title.setStyleSheet("font-size:13pt; font-weight:bold;")
        hl.addWidget(title)
        hl.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search help…")
        self.search.setFixedWidth(220)
        self.search.setFixedHeight(30)
        self.search.textChanged.connect(self._on_search)
        hl.addWidget(self.search)

        outer.addWidget(header)

        # Body
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar — no hardcoded colors, inherits from QListWidget theme rules
        self.toc = QListWidget()
        self.toc.setFixedWidth(200)
        self._toc_items: list[QListWidgetItem] = []
        for title_text, icon, _ in PAGES:
            item = QListWidgetItem(f"  {icon}  {title_text}")
            item.setSizeHint(QSize(0, 34))
            self.toc.addItem(item)
            self._toc_items.append(item)
        self.toc.setCurrentRow(0)
        body_layout.addWidget(self.toc)

        # Content pane — no hardcoded colors, inherits from QTextBrowser theme rules
        self.stack = QStackedWidget()
        for _, _, html_body in PAGES:
            browser = QTextBrowser()
            browser.setOpenExternalLinks(True)
            browser.setHtml(self._wrap_html(html_body))
            self.stack.addWidget(browser)

        body_layout.addWidget(self.stack, stretch=1)
        self.toc.currentRowChanged.connect(self.stack.setCurrentIndex)
        outer.addWidget(body, stretch=1)

        # Footer
        footer = QWidget()
        footer.setFixedHeight(36)
        footer.setObjectName("dialog_footer")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(16, 0, 16, 0)
        fl.setSpacing(10)

        gdl_link = QLabel('<a href="https://github.com/mikf/gallery-dl">gallery-dl on GitHub</a>')
        gdl_link.setOpenExternalLinks(True)
        fl.addWidget(gdl_link)

        docs_link = QLabel('<a href="https://gdl-org.github.io/docs/">Official docs</a>')
        docs_link.setOpenExternalLinks(True)
        fl.addWidget(docs_link)

        fl.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(26)
        btn_close.clicked.connect(self.accept)
        fl.addWidget(btn_close)
        outer.addWidget(footer)

    def _wrap_html(self, body: str) -> str:
        # No hardcoded colors in HTML — QTextBrowser widget rules from the theme handle it
        return f"""
        <html><head><style>
          body {{ font-family: 'Segoe UI', sans-serif; font-size:10pt; margin:0; padding:20px 28px; }}
          h2 {{ font-size:14pt; padding-bottom:6px; }}
          h3 {{ font-size:11pt; margin-top:18px; }}
          code {{ border-radius:3px; padding:1px 5px; font-family:monospace; }}
          pre {{ border-radius:6px; padding:12px; font-family:monospace; white-space:pre-wrap; }}
          dt {{ font-weight:bold; margin-top:10px; }}
          dd {{ margin-left:18px; }}
          table {{ border-collapse:collapse; width:100%; }}
          td {{ padding:6px 10px; }}
          li {{ margin-bottom:3px; }}
        </style></head><body>{body}</body></html>
        """

    def _on_search(self, query: str):
        query = query.strip().lower()
        for i, (title_text, icon, html_body) in enumerate(PAGES):
            plain = re.sub(r"<[^>]+>", "", html_body).lower()
            visible = not query or query in title_text.lower() or query in plain
            self._toc_items[i].setHidden(not visible)

    def open_page(self, title: str):
        """Jump to a specific help page by title."""
        for i, (t, _, _) in enumerate(PAGES):
            if t.lower() == title.lower():
                self.toc.setCurrentRow(i)
                break
