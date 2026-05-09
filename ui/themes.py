"""
Theme engine for PixArchive.

Each theme is a flat dict of colour tokens. build_stylesheet(theme) converts
those tokens into a complete QSS string. Switching themes at runtime just
calls QApplication.setStyleSheet(build_stylesheet(theme)).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Theme:
    id: str
    name: str
    dark: bool                      # True = dark bg, False = light bg
    description: str

    # ── Backgrounds ──────────────────────────────────────────────────────────
    bg_base: str        # window / outermost bg
    bg_mantle: str      # sidebar, header bars
    bg_surface0: str    # cards, input fields
    bg_surface1: str    # hover states, secondary surfaces
    bg_surface2: str    # pressed / active surface

    # ── Borders ──────────────────────────────────────────────────────────────
    border_dim: str     # subtle dividers
    border_mid: str     # normal borders
    border_hi: str      # hover/focus borders

    # ── Text ─────────────────────────────────────────────────────────────────
    text_primary: str   # main text
    text_secondary: str # muted / labels
    text_tertiary: str  # very muted / placeholders
    text_on_accent: str # text ON the accent-coloured button

    # ── Accent ───────────────────────────────────────────────────────────────
    accent: str         # primary interactive colour (buttons, tabs, focus)
    accent_hover: str   # accent + lighter
    accent_pressed: str # accent + darker

    # ── Semantic ─────────────────────────────────────────────────────────────
    danger: str         # stop button / error text
    danger_hover: str
    success: str        # done badge
    warning: str        # warning log line

    # ── Special surfaces ─────────────────────────────────────────────────────
    log_bg: str         # log pane background (usually darkest)
    code_bg: str        # inline code in help

    # ── Extra expressiveness ─────────────────────────────────────────────────
    accent2: str        # secondary accent for gradients (can equal accent)
    focus_glow: str     # border color on focused inputs (often = accent)


# ── Theme definitions ─────────────────────────────────────────────────────────

THEMES: dict[str, Theme] = {}


def _reg(t: Theme):
    THEMES[t.id] = t
    return t


_reg(Theme(
    id="jade-abyss",
    name="Jade Abyss",
    dark=True,
    description="Deep ocean black with luminous jade green and gold — mysterious, rich, jewel-toned",
    # BG: lifted teal-black — dark and moody but the green cast now visibly reads
    bg_base    = "#081614",
    bg_mantle  = "#040e0c",
    bg_surface0= "#102220",
    bg_surface1= "#1a3230",
    bg_surface2= "#24403e",
    border_dim = "#102220",
    border_mid = "#24403e",
    border_hi  = "#00c896",
    # Text: pale aquamarine — cool green-white, totally unlike any warm cream or blue-white
    text_primary   = "#c8f0e8",
    text_secondary = "#70b8a0",
    text_tertiary  = "#306850",
    text_on_accent = "#040e0c",
    # Accent: luminous jade — vivid saturated green, distinct from aurora's cold neon or monokai's lime
    accent        = "#00c896",
    accent_hover  = "#20e0ac",
    accent_pressed= "#00a078",
    danger        = "#ff5566",
    danger_hover  = "#ff7788",
    success       = "#88ff44",
    warning       = "#ffcc44",
    log_bg   = "#020706",
    code_bg  = "#0e1e1a",
    accent2     = "#e8b84a",       # antique gold — warm treasure against cool jade depths
    focus_glow  = "#e8b84a",       # gold focus ring — glows like sunken treasure
))

_reg(Theme(
    id="dracula",
    name="Dracula",
    dark=True,
    description="Vibrant purple & pink — the classic dark theme",
    # BG: cool desaturated blue-gray — clearly not warm, not teal, not indigo
    bg_base    = "#282a36",
    bg_mantle  = "#20212c",
    bg_surface0= "#343746",
    bg_surface1= "#424558",
    bg_surface2= "#555869",
    border_dim = "#343746",
    border_mid = "#555869",
    border_hi  = "#bd93f9",
    # Text: near-white with blue cast — not cream (gruvbox), not periwinkle (tokyo)
    text_primary   = "#f8f8f2",
    text_secondary = "#d4d4cc",
    text_tertiary  = "#6272a4",
    text_on_accent = "#1e1f2b",
    # Accent: lavender purple — owned by dracula, lighter/brighter than rose-pine's dusty pink
    accent        = "#bd93f9",
    accent_hover  = "#cba8fa",
    accent_pressed= "#a87df6",
    danger        = "#ff5555",
    danger_hover  = "#ff7070",
    success       = "#50fa7b",
    warning       = "#ffb86c",
    log_bg   = "#16171f",
    code_bg  = "#343746",
    accent2     = "#8be9fd",       # cyan — cold complement to warm lavender
    focus_glow  = "#ff79c6",       # hot pink — unmistakable focus ring
))

_reg(Theme(
    id="synthwave-84",
    name="Synthwave '84",
    dark=True,
    description="Neon magenta & cyan on deep purple-black — retro-futuristic vibes",
    # BG: deep indigo — darker and more saturated than dracula's desaturated gray
    bg_base    = "#1e1b2e",
    bg_mantle  = "#15122a",
    bg_surface0= "#2a2650",
    bg_surface1= "#34316a",
    bg_surface2= "#3e3b78",
    border_dim = "#2a2650",
    border_mid = "#4a4790",
    border_hi  = "#f92aad",
    # Text: pure white with lavender undertone — brighter than dracula's slightly warm white
    text_primary   = "#ffffff",
    text_secondary = "#b2aed4",
    text_tertiary  = "#6e5fa0",
    text_on_accent = "#15122a",
    # Accent: electric magenta — the defining synthwave colour, pinker than dracula's lavender
    accent        = "#f92aad",
    accent_hover  = "#ff48bc",
    accent_pressed= "#d91890",
    danger        = "#fe4450",
    danger_hover  = "#ff6070",
    success       = "#72f1b8",
    warning       = "#fede5d",
    log_bg   = "#0d0b1e",
    code_bg  = "#2a2650",
    accent2     = "#03edf9",       # electric cyan — the classic synthwave pairing
    focus_glow  = "#03edf9",       # cyan ring — contrasts hard with magenta accent
))


_reg(Theme(
    id="glassmorphism",
    name="Glassmorphism",
    dark=False,
    description="Frosted glass panels over deep teal — luminous, layered, Apple-inspired",
    # BG: saturated medium teal — the vivid wall seen through frosted glass; surfaces wash out toward white
    bg_base    = "#a8d4cc",
    bg_mantle  = "#90c4ba",
    bg_surface0= "#c8e8e4",
    bg_surface1= "#dff2f0",
    bg_surface2= "#f0fafa",
    border_dim = "#c8e8e4",
    border_mid = "#a0c8c0",
    border_hi  = "#0d7a6b",
    # Text: very dark teal-black — crisp and legible on both the vivid BG and frosted surfaces
    text_primary   = "#0a2820",
    text_secondary = "#1e5048",
    text_tertiary  = "#508878",
    text_on_accent = "#ffffff",
    # Accent: deep teal-green — a solid button color, clearly distinct from any blue/purple/lavender theme
    accent        = "#0d7a6b",
    accent_hover  = "#0f9280",
    accent_pressed= "#0a6055",
    danger        = "#c0392b",
    danger_hover  = "#d44234",
    success       = "#1a7a3a",
    warning       = "#c87010",
    log_bg   = "#90c4ba",
    code_bg  = "#c8e8e4",
    accent2     = "#60a5fa",       # sky blue — the reflection highlight on glass, Apple's signature
    focus_glow  = "#60a5fa",       # ice-blue focus ring — glows like backlit frosted glass
))

_reg(Theme(
    id="obsidian-ember",
    name="Obsidian Ember",
    dark=True,
    description="Volcanic black with smouldering amber and molten orange — dramatic and intense",
    # BG: near-black with a faint warm undertone — darker than gruvbox, less brown than copper
    bg_base    = "#111008",
    bg_mantle  = "#0a0904",
    bg_surface0= "#1e1c10",
    bg_surface1= "#2b2818",
    bg_surface2= "#3a3620",
    border_dim = "#1e1c10",
    border_mid = "#3a3620",
    border_hi  = "#ff6d00",
    # Text: hot ash white — very slightly warm, not cream, not blue-white
    text_primary   = "#f5f0e8",
    text_secondary = "#c8b89a",
    text_tertiary  = "#6e5e3e",
    text_on_accent = "#0a0904",
    # Accent: molten orange — brighter and hotter than gruvbox, less brown than copper
    accent        = "#ff6d00",
    accent_hover  = "#ff8c2a",
    accent_pressed= "#d45500",
    danger        = "#ff2244",
    danger_hover  = "#ff4060",
    success       = "#aadd00",
    warning       = "#ffcc00",
    log_bg   = "#070600",
    code_bg  = "#1e1c10",
    accent2     = "#ff3c00",       # deeper ember red-orange — volcanic gradient pair
    focus_glow  = "#00e5cc",       # electric teal — cold shock against volcanic warmth
))




_reg(Theme(
    id="ayu-dark",
    name="Ayu Dark",
    dark=True,
    description="Clean dark theme with warm golden accents — Ayu palette",
    # BG: very dark desaturated navy — nearly black but with a blue-steel cast
    bg_base    = "#0d1017",
    bg_mantle  = "#06090f",
    bg_surface0= "#131721",
    bg_surface1= "#1e2535",
    bg_surface2= "#283044",
    border_dim = "#131721",
    border_mid = "#283044",
    border_hi  = "#e6b450",
    # Text: warm stone — desaturated beige, not cream/parchment (gruvbox/kanagawa)
    text_primary   = "#bfbdb6",
    text_secondary = "#a8a197",
    text_tertiary  = "#5c6773",
    text_on_accent = "#0d1017",
    # Accent: golden yellow — Ayu's signature, warmer than cornflower blue themes
    accent        = "#e6b450",
    accent_hover  = "#f0c463",
    accent_pressed= "#c99d38",
    danger        = "#f07178",
    danger_hover  = "#f48890",
    success       = "#aad94c",
    warning       = "#f4a245",
    log_bg   = "#06090f",
    code_bg  = "#131721",
    accent2     = "#39bae6",       # sky blue — cold contrast to warm gold
    focus_glow  = "#39bae6",       # blue focus — clearly different from gold accent
))

_reg(Theme(
    id="monokai",
    name="Monokai",
    dark=True,
    description="The legendary Monokai — bold and punchy since 2006",
    # BG: olive-tinged near-black — warmer/greener cast than any neutral dark
    bg_base    = "#272822",
    bg_mantle  = "#1c1d18",
    bg_surface0= "#3b3c34",
    bg_surface1= "#4e4f45",
    bg_surface2= "#626358",
    border_dim = "#3b3c34",
    border_mid = "#626358",
    border_hi  = "#a6e22e",
    # Text: bright near-white — very slightly warm, vivid against the dark olive
    text_primary   = "#f8f8f2",
    text_secondary = "#c8c8bc",
    text_tertiary  = "#75715e",
    text_on_accent = "#1c1d18",
    # Accent: vivid lime — saturated neon green, totally different from everforest's sage
    accent        = "#a6e22e",
    accent_hover  = "#baef42",
    accent_pressed= "#8ecc1a",
    danger        = "#f92672",
    danger_hover  = "#fa4585",
    success       = "#fd971f",
    warning       = "#e6db74",
    log_bg   = "#1c1d18",
    code_bg  = "#3b3c34",
    accent2     = "#66d9e8",       # cyan — monokai aqua, cool contrast to hot lime
    focus_glow  = "#66d9e8",       # cyan focus ring — distinct from lime/orange
))



_reg(Theme(
    id="solarized-light",
    name="Solarized Light",
    dark=False,
    description="The classic Solarized Light — warm ivory with precision accents",
    # BG: warm ivory — yellowish tint, clearly not neutral white or mint or cool gray
    bg_base    = "#fdf6e3",
    bg_mantle  = "#eee8d5",
    bg_surface0= "#e4deca",
    bg_surface1= "#d8d2bc",
    bg_surface2= "#c8c2aa",
    border_dim = "#e4deca",
    border_mid = "#c8c2aa",
    border_hi  = "#cb4b16",
    # Text: darker slate — pushed down for contrast ratio (was 2.0, now ~3.8)
    text_primary   = "#3a5560",
    text_secondary = "#4a6570",
    text_tertiary  = "#7a9898",
    text_on_accent = "#ffffff",
    accent        = "#cb4b16",
    accent_hover  = "#de5e28",
    accent_pressed= "#a83a0c",
    danger        = "#dc322f",
    danger_hover  = "#e84a47",
    success       = "#859900",
    warning       = "#b58900",
    log_bg   = "#eee8d5",
    code_bg  = "#e4deca",
    accent2     = "#2aa198",       # solarized cyan — cool companion to warm orange
    focus_glow  = "#6c71c4",       # solarized violet — distinctive, jewel-like on warm ivory
))


_reg(Theme(
    id="candy-pastel",
    name="Candy Pastel",
    dark=False,
    description="Soft creamy pink-white with candy pink, mint and lavender — sweet, warm, effortlessly pretty",
    # BG: very light pink-white — warm and delicate, clearly distinct from peach-blossom's deeper blush
    bg_base    = "#fff7fb",
    bg_mantle  = "#fdeef6",
    bg_surface0= "#fce0ee",
    bg_surface1= "#f8cee2",
    bg_surface2= "#f2b8d4",
    border_dim = "#fce0ee",
    border_mid = "#f2b8d4",
    border_hi  = "#ff8fab",
    # Text: muted dark purple-gray — warm and soft, not harsh black
    text_primary   = "#4b4453",
    text_secondary = "#7a6880",
    text_tertiary  = "#b09ab8",
    text_on_accent = "#3a1830",   # deep plum on pink button — readable without white harshness
    # Accent: candy pink — button fill with dark text, decorative borders, highlights
    accent        = "#ff8fab",
    accent_hover  = "#ff9fba",
    accent_pressed= "#f07090",
    danger        = "#e05050",
    danger_hover  = "#f06060",
    success       = "#50b880",
    warning       = "#e09040",
    log_bg   = "#fce0ee",
    code_bg  = "#fdeef6",
    accent2     = "#a0e7e5",       # soft mint — cool, refreshing complement to candy pink
    focus_glow  = "#b4a7ff",       # light lavender — dreamy focus ring; all three pastels present
))

_reg(Theme(
    id="catppuccin-latte",
    name="Catppuccin Latte",
    dark=False,
    description="Warm cream with lavender and green — Catppuccin's light variant",
    # BG: lavender-tinted cool gray — clearly purple-influenced, unlike arctic's crisp white
    bg_base    = "#eff1f5",
    bg_mantle  = "#e2e5ee",
    bg_surface0= "#d4d8e4",
    bg_surface1= "#c4c8d8",
    bg_surface2= "#b0b5ca",
    border_dim = "#d4d8e4",
    border_mid = "#b0b5ca",
    border_hi  = "#7287fd",
    # Text: deep indigo-slate — darkened for contrast (was 2.7 ratio, now ~4.5)
    text_primary   = "#383b58",
    text_secondary = "#565870",
    text_tertiary  = "#8c90a8",
    text_on_accent = "#12103a",
    accent        = "#7287fd",
    accent_hover  = "#8898ff",
    accent_pressed= "#5f74fa",
    danger        = "#d20f39",
    danger_hover  = "#e41848",
    success       = "#40a02b",
    warning       = "#df8e1d",
    log_bg   = "#d4d8e4",
    code_bg  = "#e2e5ee",
    accent2     = "#8839ef",       # mauve — vivid purple complement to lavender
    focus_glow  = "#04a5e5",       # sky blue focus — lighter, cooler than accent
))

_reg(Theme(
    id="tokyo-night",
    name="Tokyo Night",
    dark=True,
    description="Cool midnight blues with neon violet — inspired by Tokyo after dark",
    # BG: deep true navy — shifted blue vs synthwave's purple-indigo (#1e1b2e Δ=4 was too close)
    bg_base    = "#16213e",
    bg_mantle  = "#0f1629",
    bg_surface0= "#1f2d4a",
    bg_surface1= "#2b3d60",
    bg_surface2= "#374e76",
    border_dim = "#1f2d4a",
    border_mid = "#374e76",
    border_hi  = "#7aa2f7",
    # Text: periwinkle-tinted — distinctly blue-purple, unlike kanagawa's warm parchment
    text_primary   = "#c0caf5",
    text_secondary = "#9aa5ce",
    text_tertiary  = "#565f89",
    text_on_accent = "#16213e",
    # Accent: cornflower blue — bright and cool, not as muted as kanagawa's wave blue
    accent        = "#7aa2f7",
    accent_hover  = "#8fb2f8",
    accent_pressed= "#638ee6",
    danger        = "#f7768e",
    danger_hover  = "#f98fa3",
    success       = "#9ece6a",
    warning       = "#e0af68",
    log_bg   = "#0b0c19",
    code_bg  = "#222338",
    accent2     = "#bb9af7",       # violet — neon night glow
    focus_glow  = "#7dcfff",       # light cyan — dawn on the horizon
))

_reg(Theme(
    id="midnight-aurora",
    name="Midnight Aurora",
    dark=True,
    description="Deep arctic black with aurora borealis greens and violet ribbons",
    # BG: deep teal-black — lifted so the cold teal cast visibly reads (was too dark to perceive hue)
    bg_base    = "#0a1a1e",
    bg_mantle  = "#061014",
    bg_surface0= "#112428",
    bg_surface1= "#1a3038",
    bg_surface2= "#243e48",
    border_dim = "#112428",
    border_mid = "#243e48",
    border_hi  = "#00ffaa",
    # Text: glacial white — cool blue-white, crisper than dracula's near-white
    text_primary   = "#d8f0f0",
    text_secondary = "#7aaebb",
    text_tertiary  = "#3a6070",
    text_on_accent = "#040a0c",
    # Accent: aurora green — vivid, cold, unlike monokai's warm lime or everforest's sage
    accent        = "#00ffaa",
    accent_hover  = "#33ffbe",
    accent_pressed= "#00cc88",
    danger        = "#ff4466",
    danger_hover  = "#ff6680",
    success       = "#00ddff",
    warning       = "#ffe066",
    log_bg   = "#020608",
    code_bg  = "#0e1a1e",
    accent2     = "#aa44ff",       # deep violet aurora ribbon — cold complement to green
    focus_glow  = "#aa44ff",       # violet — strikes against the green accent beautifully
))

_reg(Theme(
    id="cyberpunk",
    name="Cyberpunk",
    dark=True,
    description="Acid yellow on near-black — high voltage neon dystopia",
    # BG: pure achromatic near-black — zero hue, maximally stark contrast to all other BGs
    bg_base    = "#0c0c0c",
    bg_mantle  = "#050505",
    bg_surface0= "#181818",
    bg_surface1= "#242424",
    bg_surface2= "#303030",
    border_dim = "#181818",
    border_mid = "#303030",
    border_hi  = "#f9e800",
    # Text: almost pure white — hard industrial, no warmth or tint
    text_primary   = "#f0f0f0",
    text_secondary = "#aaaaaa",
    text_tertiary  = "#505050",
    text_on_accent = "#080808",
    # Accent: acid yellow — aggressive, unlike any other theme
    accent        = "#f9e800",
    accent_hover  = "#fff030",
    accent_pressed= "#d8c800",
    danger        = "#ff003c",
    danger_hover  = "#ff2855",
    success       = "#00ff9f",
    warning       = "#ff8c00",
    log_bg   = "#020202",
    code_bg  = "#181818",
    accent2     = "#00d4ff",       # ice blue — cold complement to hot yellow
    focus_glow  = "#00d4ff",       # ice blue focus — distinct from danger red
))

_reg(Theme(
    id="neon-noir",
    name="Neon Noir",
    dark=True,
    description="Rain-slicked black streets lit by hot pink and electric blue neons — cinematic cyberpunk noir",
    # BG: deep violet-tinged black — faint purple cast separates it from cyberpunk's pure gray & aurora's teal
    bg_base    = "#0a0614",
    bg_mantle  = "#060410",
    bg_surface0= "#130d22",
    bg_surface1= "#1c1530",
    bg_surface2= "#271e40",
    border_dim = "#130d22",
    border_mid = "#271e40",
    border_hi  = "#ff2d78",
    # Text: neon-lit white — pure bright, no warmth, no purple tint
    text_primary   = "#f0f0ff",
    text_secondary = "#9090c0",
    text_tertiary  = "#505070",
    text_on_accent = "#06060c",
    # Accent: hot neon pink — more saturated/redder than dracula's lavender, hotter than rose-pine's dusty rose
    accent        = "#ff2d78",
    accent_hover  = "#ff5595",
    accent_pressed= "#d41a60",
    danger        = "#ff1100",
    danger_hover  = "#ff3322",
    success       = "#00ff88",
    warning       = "#ffcc00",
    log_bg   = "#020206",
    code_bg  = "#121220",
    accent2     = "#00c8ff",       # electric blue — classic neon pairing with hot pink
    focus_glow  = "#00c8ff",       # blue focus ring — cold contrast to hot pink
))

_reg(Theme(
    id="honeydew",
    name="Honeydew",
    dark=False,
    description="Soft mint greens and warm cream — fresh, gentle, easy on the eyes",
    # BG: pale mint-white — very light, clearly green-tinted, unlike paper's warm tan
    bg_base    = "#f4faf4",
    bg_mantle  = "#e8f4e8",
    bg_surface0= "#d8ecd8",
    bg_surface1= "#c4e0c4",
    bg_surface2= "#acd0ac",
    border_dim = "#d8ecd8",
    border_mid = "#acd0ac",
    border_hi  = "#257040",
    # Text: deep forest green — green-tinted dark, unlike paper's sepia or arctic's navy
    text_primary   = "#1a3824",
    text_secondary = "#336640",
    text_tertiary  = "#6a9870",
    text_on_accent = "#ffffff",
    # Accent: darkened to #257040 so white text clears 4.5:1 on buttons
    accent        = "#257040",
    accent_hover  = "#339058",
    accent_pressed = "#1c5a34",
    danger        = "#c0392b",
    danger_hover  = "#d44438",
    success       = "#1e7a45",
    warning       = "#c87a10",
    log_bg   = "#d8ecd8",
    code_bg  = "#e8f4e8",
    accent2     = "#1a6e90",       # teal-blue — cool complement to green
    focus_glow  = "#8e34a8",       # violet focus — unexpected pop on mint
))


_reg(Theme(
    id="galactic-grape",
    name="Galactic Grape",
    dark=True,
    description="Deep space purple-black with electric violet and gold stardust accents — cosmic and opulent",
    # BG: lifted deep violet — dark enough to feel cosmic, light enough that the purple hue is visible
    bg_base    = "#130a22",
    bg_mantle  = "#0c0618",
    bg_surface0= "#1e1035",
    bg_surface1= "#2a1a48",
    bg_surface2= "#38245c",
    border_dim = "#1e1035",
    border_mid = "#38245c",
    border_hi  = "#c060ff",
    # Text: pale lavender-white — distinctly purple-tinted, cooler than rose-pine's warm lavender
    text_primary   = "#e8d8ff",
    text_secondary = "#a880d0",
    text_tertiary  = "#604880",
    text_on_accent = "#0c0618",
    # Accent: electric violet — more saturated than dracula's soft purple, brighter than rose-pine's iris
    accent        = "#c060ff",
    accent_hover  = "#d080ff",
    accent_pressed= "#a040e0",
    danger        = "#ff4488",
    danger_hover  = "#ff66a0",
    success       = "#60ffb0",
    warning       = "#ffd060",
    log_bg   = "#050210",
    code_bg  = "#180e2c",
    accent2     = "#ffd060",       # gold stardust — warm luxury against the cold violet
    focus_glow  = "#ff60b0",       # hot pink — distinct from gold accent2 and violet accent
))

_reg(Theme(
    id="vanta-crimson",
    name="Vanta Crimson",
    dark=True,
    description="Vantablack depths with blood-red accents and steel-silver highlights — bold, gothic, unforgettable",
    # BG: lifted red-black — dark enough to feel gothic, enough red to be perceptibly distinct from cyberpunk's gray
    bg_base    = "#1a0808",
    bg_mantle  = "#110404",
    bg_surface0= "#280e0e",
    bg_surface1= "#361616",
    bg_surface2= "#461e1e",
    border_dim = "#280e0e",
    border_mid = "#461e1e",
    border_hi  = "#e01030",
    # Text: cold silver — blue-gray tint, metallic, sharply contrasts warm red bg
    text_primary   = "#e8e0e0",
    text_secondary = "#a09090",
    text_tertiary  = "#604040",
    text_on_accent = "#ffffff",
    # Accent: blood crimson — deeper and redder than danger colors, owns the warmth
    accent        = "#e01030",
    accent_hover  = "#f02848",
    accent_pressed= "#b00820",
    danger        = "#ff6600",
    danger_hover  = "#ff8833",
    success       = "#40cc60",
    warning       = "#ffaa00",
    log_bg   = "#050202",
    code_bg  = "#1e0c0c",
    accent2     = "#c0c8d8",       # cold steel — metallic silver-blue complement to hot crimson
    focus_glow  = "#e050a0",       # hot rose — vivid, cold-warm contrast against the red darkness
))

_reg(Theme(
    id="arctic",
    name="Arctic",
    dark=False,
    description="Crisp white and icy blue — clean, high-contrast, Scandinavian minimalism",
    # BG: pure white — maximally crisp, unlike any other light theme's tinted base
    bg_base    = "#ffffff",
    bg_mantle  = "#f0f5fa",
    bg_surface0= "#dfe8f0",
    bg_surface1= "#ccd9e5",
    bg_surface2= "#b5c8db",
    border_dim = "#dfe8f0",
    border_mid = "#b5c8db",
    border_hi  = "#0c6ec9",
    # Text: deep navy — high contrast, colder than paper's sepia, darker than catppuccin's slate
    text_primary   = "#0a1c2e",
    text_secondary = "#234060",
    text_tertiary  = "#6a90b0",
    text_on_accent = "#ffffff",
    # Accent: deep ice blue — bolder/darker than catppuccin's lavender-blue, arctic serious
    accent        = "#0c6ec9",
    accent_hover  = "#1a82e0",
    accent_pressed= "#0858a8",
    danger        = "#c62828",
    danger_hover  = "#d83535",
    success       = "#2e7d32",
    warning       = "#e65100",
    log_bg   = "#dfe8f0",
    code_bg  = "#f0f5fa",
    accent2     = "#007a8a",       # teal — cool second accent distinct from blue
    focus_glow  = "#6a1fa0",       # deep violet — unexpected, dramatic on white
))

_reg(Theme(
    id="peach-blossom",
    name="Peach Blossom",
    dark=False,
    description="Soft blush pink and warm ivory with deep rose accents — delicate, vibrant, and distinctly feminine",
    # BG: blush white — lightest possible pink tint, clearly rose-influenced, unlike any other light theme
    bg_base    = "#fff5f5",
    bg_mantle  = "#fce8e8",
    bg_surface0= "#f5d6d6",
    bg_surface1= "#ecc4c4",
    bg_surface2= "#e0aeae",
    border_dim = "#f5d6d6",
    border_mid = "#e0aeae",
    border_hi  = "#c0305a",
    # Text: deep plum — warm dark, not sepia, not navy, rose-tinted darkness
    text_primary   = "#2e0a18",
    text_secondary = "#6e2840",
    text_tertiary  = "#b07088",
    text_on_accent = "#fff5f5",
    # Accent: deep rose — saturated, bold, unlike catppuccin's lavender or arctic's cold blue
    accent        = "#c0305a",
    accent_hover  = "#d84470",
    accent_pressed= "#a02048",
    danger        = "#aa1500",
    danger_hover  = "#c02010",
    success       = "#2a7840",
    warning       = "#b05800",
    log_bg   = "#f5d6d6",
    code_bg  = "#fce8e8",
    accent2     = "#8040a8",       # deep violet — cool complement to warm rose
    focus_glow  = "#8040a8",       # purple focus ring — jewel-like against blush
))

DEFAULT_THEME_ID = "tokyo-night"


# ── QSS generator ─────────────────────────────────────────────────────────────

def build_stylesheet(t: Theme, font_size: int = 10) -> str:
    """Generate a complete QSS string from a Theme."""
    return f"""
/* ════════════════════════════════════════════════════
   PixArchive  —  theme: {t.name}
   ════════════════════════════════════════════════════ */

QWidget {{
    background-color: {t.bg_base};
    color: {t.text_primary};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: {font_size}pt;
}}

/* ── Sidebar ── */
QListWidget {{
    background-color: {t.bg_mantle};
    border: none;
    padding: 6px 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 8px 12px;
    border-radius: 6px;
    color: {t.text_secondary};
}}
QListWidget::item:selected {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.bg_surface2}, stop:1 {t.bg_surface0}
    );
    color: {t.accent2};
    border-left: 3px solid {t.accent2};
    font-weight: bold;
}}
QListWidget::item:hover:!selected {{
    background-color: {t.bg_surface0};
    color: {t.text_primary};
    border-left: 3px solid {t.accent};
}}

/* ── Inputs ── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {t.bg_surface0};
    border: 1px solid {t.border_mid};
    border-radius: 6px;
    padding: 5px 9px;
    color: {t.text_primary};
    selection-background-color: {t.accent};
    selection-color: {t.text_on_accent};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {t.accent};
}}
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
    color: {t.text_tertiary};
    background-color: {t.bg_mantle};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {t.bg_surface0};
    border: 1px solid {t.accent2};
    border-radius: 6px;
    selection-background-color: {t.bg_surface1};
    selection-color: {t.accent2};
    color: {t.text_primary};
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background: {t.bg_surface1};
    border: none;
    border-left: 1px solid {t.accent2};
    width: 16px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {t.accent2};
}}

/* ── Buttons ── */
QPushButton {{
    background-color: {t.bg_surface0};
    color: {t.text_secondary};
    border: 1px solid {t.border_mid};
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    background-color: {t.bg_surface1};
    color: {t.accent};
    border: 1px solid {t.accent};
    border-bottom: 3px solid {t.accent};
}}
QPushButton:pressed {{
    background-color: {t.bg_surface2};
    border: 1px solid {t.accent2};
    border-bottom: 3px solid {t.accent2};
    color: {t.accent2};
}}
QPushButton:checked {{
    background-color: {t.bg_surface1};
    color: {t.accent};
    border: 1px solid {t.accent};
    border-bottom: 3px solid {t.accent2};
    font-weight: bold;
}}
QPushButton:disabled {{
    color: {t.text_tertiary};
    border: 1px solid {t.border_dim};
}}
QPushButton#btn_download {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.accent}, stop:1 {t.accent2}
    );
    color: {t.text_on_accent};
    border: none;
    font-weight: bold;
    padding: 6px 18px;
    border-radius: 6px;
}}
QPushButton#btn_download:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.accent_hover}, stop:1 {t.accent2}
    );
}}
QPushButton#btn_download:pressed {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.accent_pressed}, stop:1 {t.accent}
    );
}}
QPushButton#btn_download:disabled {{
    background: {t.bg_surface1};
    color: {t.text_tertiary};
}}
QPushButton#btn_stop {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.danger}, stop:1 {t.danger_hover}
    );
    color: #ffffff;
    border: none;
    border-bottom: 3px solid {t.accent2};
    font-weight: bold;
    border-radius: 6px;
}}
QPushButton#btn_stop:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.danger_hover}, stop:1 {t.danger}
    );
    border-bottom: 3px solid {t.accent};
}}

/* ── Labels ── */
QLabel#section_label {{
    color: {t.text_tertiary};
    font-size: 8pt;
    font-weight: bold;
    letter-spacing: 1px;
}}

/* ── Progress bar ── */
QProgressBar {{
    background-color: {t.bg_surface0};
    border: none;
    border-radius: 3px;
    height: 5px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.accent}, stop:1 {t.accent2}
    );
    border-radius: 3px;
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.border_hi}, stop:1 {t.border_mid}
    );
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.accent}, stop:1 {t.accent2}
    );
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ height: 0; }}

/* ── Log output ── */
QPlainTextEdit#log_output {{
    background-color: {t.log_bg};
    border: none;
    border-top: 1px solid {t.border_dim};
    border-radius: 0;
    color: {t.text_secondary};
    font-family: 'Cascadia Code', 'Consolas', 'JetBrains Mono', monospace;
    font-size: 9pt;
    padding: 6px 10px;
}}

/* ── Splitter ── */
QSplitter::handle {{
    background-color: {t.border_dim};
    width: 1px;
    height: 1px;
}}

/* ── Group box ── */
QGroupBox {{
    border: 1px solid {t.border_mid};
    border-top: 2px solid {t.accent2};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    color: {t.accent2};
    font-size: 8pt;
    font-weight: bold;
    letter-spacing: 1px;
}}

/* ── Checkboxes ── */
QCheckBox {{
    spacing: 8px;
    color: {t.text_primary};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {t.border_mid};
    background: {t.bg_surface0};
}}
QCheckBox::indicator:checked {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 {t.accent}, stop:1 {t.accent2}
    );
    border-color: {t.accent2};
    border-width: 2px;
}}
QCheckBox::indicator:hover {{
    border-color: {t.focus_glow};
    border-width: 2px;
    background: {t.bg_surface1};
}}
QCheckBox:disabled {{
    color: {t.text_tertiary};
}}

/* ── Tab bar ── */
QTabWidget::pane {{
    border: none;
}}
QTabBar::tab {{
    background: transparent;
    color: {t.text_tertiary};
    padding: 7px 16px;
    border: none;
    border-bottom: 3px solid transparent;
}}
QTabBar::tab:selected {{
    color: {t.accent};
    border-bottom: 3px solid {t.accent};
    border-top: 2px solid {t.accent2};
    font-weight: bold;
    background: {t.bg_surface0};
}}
QTabBar::tab:hover:!selected {{
    color: {t.accent2};
    border-bottom: 3px solid {t.accent2};
    background: {t.bg_surface0};
}}

/* ── Menu bar ── */
QMenuBar {{
    background: {t.bg_mantle};
    color: {t.text_secondary};
    border-bottom: 1px solid {t.border_dim};
    padding: 2px 4px;
    font-size: 9pt;
}}
QMenuBar::item:selected {{
    background: {t.bg_surface0};
    color: {t.text_primary};
    border-radius: 4px;
}}
QMenu {{
    background: {t.bg_base};
    border: 1px solid {t.border_mid};
    border-radius: 6px;
    padding: 4px;
    color: {t.text_primary};
    font-size: 9pt;
}}
QMenu::item {{
    padding: 6px 28px 6px 14px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.bg_surface2}, stop:1 {t.bg_surface0}
    );
    color: {t.accent2};
    border-left: 3px solid {t.accent};
}}
QMenu::separator {{
    height: 1px;
    background: {t.border_dim};
    margin: 4px 8px;
}}

/* ── Tooltip ── */
QToolTip {{
    background-color: {t.bg_surface1};
    color: {t.text_primary};
    border: 1px solid {t.focus_glow};
    border-left: 3px solid {t.accent2};
    border-radius: 4px;
    padding: 5px 10px;
    font-size: 9pt;
}}

/* ── Menu bar ── */
QMenuBar {{
    background-color: {t.bg_mantle};
    color: {t.text_secondary};
    border-bottom: 2px solid {t.accent2};
    padding: 2px 4px;
}}
QMenuBar::item:selected {{
    background: {t.bg_surface0};
    color: {t.accent2};
    border-radius: 4px;
    border-bottom: 2px solid {t.accent};
}}

/* ── Dialogs / scroll areas ── */
QDialog {{
    background-color: {t.bg_base};
}}
QScrollArea {{
    background: transparent;
    border: none;
}}

/* ── Text browser (help / about) ── */
QTextBrowser {{
    background-color: {t.bg_base};
    border: none;
    color: {t.text_primary};
    selection-background-color: {t.accent};
    selection-color: {t.text_on_accent};
}}

/* ── Frames ── */
QFrame[frameShape="4"],   /* HLine */
QFrame[frameShape="5"] {{ /* VLine */
    color: {t.border_mid};
    background: {t.border_mid};
}}

/* ── Header bars inside dialogs ── */
QWidget#dialog_header {{
    background-color: {t.bg_mantle};
    border-bottom: 2px solid {t.accent};
}}
QWidget#dialog_header QLabel {{
    color: {t.text_secondary};
    background: transparent;
}}
QWidget#dialog_footer {{
    background-color: {t.bg_mantle};
    border-top: 2px solid {t.accent2};
}}

/* ── Sidebar ── */
QWidget#sidebar {{
    background-color: {t.bg_mantle};
    border-right: 1px solid {t.border_dim};
}}
QWidget#sidebar QLabel {{
    background-color: transparent;
    color: {t.text_secondary};
}}
QWidget#sidebar QLabel#sidebar_title {{
    color: {t.accent};
    font-weight: bold;
    font-size: 14pt;
    padding: 4px 10px 16px 10px;
    letter-spacing: 1px;
}}
QWidget#sidebar QPushButton {{
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    color: {t.text_tertiary};
    font-size: 8pt;
    padding: 5px 10px;
    text-align: left;
    border-radius: 0px;
}}
QWidget#sidebar QPushButton:hover {{
    background-color: {t.bg_surface0};
    color: {t.accent2};
    border: none;
    border-left: 3px solid {t.accent2};
    border-radius: 0px;
}}
QWidget#sidebar QLabel#sidebar_version {{
    color: {t.accent2};
    font-size: 8pt;
    padding: 4px 10px 0 10px;
    font-weight: bold;
}}
QListWidget#nav_list {{
    background-color: {t.bg_mantle};
    border: none;
}}
QListWidget#nav_list::item {{
    color: {t.text_tertiary};
    padding: 8px 8px 8px 14px;
    border-left: 3px solid transparent;
    border-radius: 0px;
}}
QListWidget#nav_list::item:selected {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.bg_surface1}, stop:1 {t.bg_mantle}
    );
    color: {t.accent};
    border-left: 4px solid {t.accent};
    font-weight: bold;
}}
QListWidget#nav_list::item:hover:!selected {{
    background-color: {t.bg_surface0};
    color: {t.accent2};
    border-left: 4px solid {t.accent2};
}}

/* ── Stop button — dim when disabled ── */
QPushButton#btn_stop:disabled {{
    background-color: {t.bg_surface1};
    color: {t.text_tertiary};
    border: 1px solid {t.border_dim};
}}

/* ── Status bar stat labels ── */
QWidget#dialog_footer QLabel {{
    color: {t.text_tertiary};
    font-size: 8pt;
}}
QWidget#dialog_footer {{
    background-color: {t.bg_mantle};
    border-top: 2px solid {t.accent2};
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t.bg_mantle}, stop:0.5 {t.bg_surface0}, stop:1 {t.bg_mantle}
    );
}}

/* ── Log level filter toggle buttons ── */
QPushButton#log_filter_btn {{
    background-color: {t.bg_surface0};
    color: {t.text_tertiary};
    border: 1px solid {t.border_dim};
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 7pt;
    font-weight: normal;
}}
QPushButton#log_filter_btn:checked {{
    background-color: {t.bg_surface1};
    color: {t.accent};
    border: 1px solid {t.accent};
    border-bottom: 2px solid {t.accent2};
    font-weight: bold;
}}
QPushButton#log_filter_btn:hover {{
    border-color: {t.accent};
    color: {t.accent};
}}

/* ── Log output area ── */
QPlainTextEdit#log_output {{
    background-color: {t.bg_mantle};
    color: {t.text_secondary};
    border: none;
    font-family: 'Consolas', 'Cascadia Code', 'Fira Mono', monospace;
    font-size: 9pt;
    padding: 6px;
}}

/* Log level colors embedded via HTML span classes in appendHtml() */
/* Defined here for reference — actual coloring is inline HTML */

/* ── QTextBrowser (Help / About) ── */
QTextBrowser {{
    background-color: {t.bg_surface0};
    color: {t.text_primary};
    border: none;
    border-left: 3px solid {t.accent2};
    font-size: 9pt;
    padding: 16px 20px;
}}

/* ── Stop button — dim when disabled ── */
QPushButton#btn_stop {{
    background-color: {t.danger};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-weight: bold;
}}
QPushButton#btn_stop:hover {{
    background-color: {t.danger_hover};
}}
QPushButton#btn_stop:disabled {{
    background-color: {t.bg_surface1};
    color: {t.text_tertiary};
    border: 1px solid {t.border_dim};
    font-weight: normal;
}}
""" + (_synthwave_overrides(t) if t.id == "synthwave-84" else "")


def _synthwave_overrides(t: Theme) -> str:
    """
    Extra QSS rules that are unique to the Synthwave '84 theme.
    Appended after the base stylesheet so they take precedence.
    """
    return """
/* ══════════════════════════════════════════════
   Synthwave '84 — neon overrides
   ══════════════════════════════════════════════ */

/* Neon magenta glow on focused inputs — 2px accent border + inner shadow */
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 2px solid #ff7edb;
    padding: 4px 8px;           /* compensate for thicker border */
}

/* Accent (Download Now) button — gradient + thicker border glow */
QPushButton#btn_download {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff7edb, stop:1 #b893f5
    );
    color: #1a1a2e;
    border: 2px solid #ff7edb;
    font-weight: bold;
    border-radius: 6px;
    padding: 5px 17px;
}
QPushButton#btn_download:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff9ae3, stop:1 #c9a4fa
    );
    border-color: #ff9ae3;
}
QPushButton#btn_download:pressed {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #e060c0, stop:1 #9d6de0
    );
    border-color: #e060c0;
}

/* Stop button — neon red */
QPushButton#btn_stop {
    background: #fe4450;
    border: 2px solid #fe4450;
    color: #1a1a2e;
}
QPushButton#btn_stop:hover {
    background: #ff6070;
    border-color: #ff6070;
}

/* Tab bar — cyan underline instead of magenta for contrast */
QTabBar::tab:selected {
    color: #72f1b8;
    border-bottom: 2px solid #72f1b8;
}

/* Progress bar — cyan fill on dark purple track */
QProgressBar {
    background-color: #2d2b55;
    border-radius: 3px;
}
QProgressBar::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff7edb, stop:1 #72f1b8
    );
    border-radius: 3px;
}

/* Scrollbar handle — accent pink */
QScrollBar::handle:vertical {
    background: #495495;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #ff7edb;
}

/* Selected nav item — subtle magenta left-border accent */
QListWidget::item:selected {
    background-color: #2d2b55;
    color: #ff7edb;
    border-left: 3px solid #ff7edb;
    padding-left: 9px;          /* keep text aligned */
}

/* Sidebar title — neon gradient text isn't possible in QSS,
   so we use a bright white + purple-tinted bg instead */
QWidget#sidebar {
    background-color: #1a1a2e;
    border-right: 1px solid #495495;
}

/* Tooltip — dark purple with neon border */
QToolTip {
    background-color: #2d2b55;
    color: #ff7edb;
    border: 1px solid #ff7edb;
    border-radius: 4px;
    padding: 4px 8px;
}

/* CheckBox indicator — magenta when checked */
QCheckBox::indicator:checked {
    background-color: #ff7edb;
    border-color: #ff7edb;
}
QCheckBox::indicator:hover {
    border-color: #ff7edb;
}

/* Menu hover — purple surface */
QMenu::item:selected {
    background: #34315f;
    color: #ff7edb;
}
QMenuBar::item:selected {
    background: #2d2b55;
    color: #ff7edb;
    border-radius: 4px;
}

/* Group box title — cyan */
QGroupBox::title {
    color: #72f1b8;
}

/* Log pane — deep black-purple with cyan text */
QPlainTextEdit#log_output {
    background-color: #110e1f;
    color: #b8b4d0;
    border-top: 1px solid #495495;
}
"""


def get_theme(theme_id: str) -> Theme:
    return THEMES.get(theme_id, THEMES[DEFAULT_THEME_ID])


def list_themes() -> list[Theme]:
    return list(THEMES.values())


def apply_theme(app, theme_id: str, font_size: int = 10):
    """Apply a theme: sets QPalette AND QSS so palette() refs resolve correctly."""
    from PyQt6.QtGui import QPalette, QColor

    theme = get_theme(theme_id)

    def c(h): return QColor(h)

    pal = QPalette()
    # For light themes, Base should be lighter than Window (bg_base)
    # For dark themes, Base is a slightly elevated surface
    if theme.dark:
        base_color = theme.bg_surface0
        alt_base   = theme.bg_surface1
        button_col = theme.bg_surface0
    else:
        base_color = theme.bg_base       # lightest surface for inputs
        alt_base   = theme.bg_surface0   # slightly darker for alternating rows
        button_col = theme.bg_surface0

    pal.setColor(QPalette.ColorRole.Window,          c(theme.bg_base))
    pal.setColor(QPalette.ColorRole.Base,            c(base_color))
    pal.setColor(QPalette.ColorRole.AlternateBase,   c(alt_base))
    pal.setColor(QPalette.ColorRole.Button,          c(button_col))
    pal.setColor(QPalette.ColorRole.Dark,            c(theme.bg_mantle))
    pal.setColor(QPalette.ColorRole.Mid,             c(theme.text_tertiary))
    pal.setColor(QPalette.ColorRole.Midlight,        c(theme.border_mid))
    pal.setColor(QPalette.ColorRole.Shadow,          c(theme.bg_surface2))
    pal.setColor(QPalette.ColorRole.Light,           c(theme.bg_surface1))
    pal.setColor(QPalette.ColorRole.WindowText,      c(theme.text_primary))
    pal.setColor(QPalette.ColorRole.Text,            c(theme.text_primary))
    pal.setColor(QPalette.ColorRole.ButtonText,      c(theme.text_primary))
    pal.setColor(QPalette.ColorRole.BrightText,      c(theme.danger))
    pal.setColor(QPalette.ColorRole.PlaceholderText, c(theme.text_tertiary))
    pal.setColor(QPalette.ColorRole.Highlight,       c(theme.accent))
    pal.setColor(QPalette.ColorRole.HighlightedText, c(theme.text_on_accent))
    pal.setColor(QPalette.ColorRole.Link,            c(theme.accent))
    pal.setColor(QPalette.ColorRole.LinkVisited,     c(theme.accent_pressed))
    pal.setColor(QPalette.ColorRole.ToolTipBase,     c(theme.bg_surface0))
    pal.setColor(QPalette.ColorRole.ToolTipText,     c(theme.text_primary))

    # Mirror the Active group into Inactive so that text selection colours
    # remain consistent when a widget or window loses focus. Without this Qt
    # falls back to the system palette for the Inactive group, which produces
    # the "blacked-out / censored" selection appearance on custom themes.
    for role, color in [
        (QPalette.ColorRole.Highlight,        c(theme.accent)),
        (QPalette.ColorRole.HighlightedText,  c(theme.text_on_accent)),
        (QPalette.ColorRole.Text,             c(theme.text_primary)),
        (QPalette.ColorRole.WindowText,       c(theme.text_primary)),
        (QPalette.ColorRole.Base,             c(base_color)),
        (QPalette.ColorRole.Window,           c(theme.bg_base)),
    ]:
        pal.setColor(QPalette.ColorGroup.Inactive, role, color)

    # Disabled group — keep text readable but visually dimmed.
    for role, color in [
        (QPalette.ColorRole.Text,        c(theme.text_tertiary)),
        (QPalette.ColorRole.WindowText,  c(theme.text_tertiary)),
        (QPalette.ColorRole.ButtonText,  c(theme.text_tertiary)),
        (QPalette.ColorRole.Base,        c(base_color)),
        (QPalette.ColorRole.Window,      c(theme.bg_base)),
        (QPalette.ColorRole.Highlight,   c(theme.bg_surface2)),
        (QPalette.ColorRole.HighlightedText, c(theme.text_tertiary)),
    ]:
        pal.setColor(QPalette.ColorGroup.Disabled, role, color)

    app.setPalette(pal)
    app.setStyleSheet(build_stylesheet(theme, font_size))
    return theme
