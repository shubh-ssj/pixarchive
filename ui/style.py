"""
Backwards-compatibility shim.
Old code that imports APP_STYLE will get the default theme's stylesheet.
New code should import from ui.themes instead.
"""
from ui.themes import build_stylesheet, get_theme, DEFAULT_THEME_ID

APP_STYLE = build_stylesheet(get_theme(DEFAULT_THEME_ID))
