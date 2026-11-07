from tkinter import ttk

# --- Color Palette Constants ---
COLOR_BG = "#F5F3EC"              # Warm Linen Alabaster / Ivory
COLOR_SIDEBAR = "#263C35"         # Deep Pine Forest
COLOR_SIDEBAR_HOVER = "#324C43"   # Slightly lighter pine for hover
COLOR_SIDEBAR_ACTIVE = "#1A2B25"  # Dark forest for active nav tab
COLOR_ACCENT = "#82916C"          # Sage Herb
COLOR_ACCENT_HOVER = "#6E7C5A"    # Darker sage for button hover
COLOR_CARD_BG = "#FFFFFF"         # Crisp White Card Background
COLOR_CARD_BORDER = "#E5E1D5"     # Subtle card border
COLOR_TEXT_PRIMARY = "#283B32"    # Deep Forest Charcoal
COLOR_TEXT_SECONDARY = "#73786C"  # Muted Olive Gray
COLOR_BORDER = "#DCD7CA"          # General border color

# Status Badge Colors
COLOR_STATUS_AVAILABLE = "#4E7C5F"    # Deep Sage Green
COLOR_STATUS_OCCUPIED = "#C67D34"     # Warm Amber Orange
COLOR_STATUS_MAINTENANCE = "#B94A48"  # Muted Terracotta Red
COLOR_STATUS_BOOKED = "#436E82"       # Slate Blue

# Currency Symbol
CURRENCY_SYMBOL = "₹"

# --- Typography Font Specifications ---
FONT_FAMILY = "Segoe UI"
FONT_TITLE_LARGE = (FONT_FAMILY, 18, "bold")
FONT_TITLE_MEDIUM = (FONT_FAMILY, 14, "bold")
FONT_SECTION = (FONT_FAMILY, 12, "bold")
FONT_CARD_VALUE = (FONT_FAMILY, 22, "bold")
FONT_CARD_LABEL = (FONT_FAMILY, 10, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_BUTTON = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_BRAND = ("Georgia", 16, "bold")
FONT_BRAND_SUB = (FONT_FAMILY, 8, "bold")


def setup_ttk_styles(root):
    """
    Configures ttk styles for tables (Treeview), dropdowns (Combobox),
    and entry widgets to match the Staywise boutique hotel aesthetic.
    """
    style = ttk.Style(root)
    # Use 'clam' or 'alt' for predictable custom styling across Windows
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # --- Treeview (Tables) Styling ---
    style.configure(
        "Treeview",
        background="#FFFFFF",
        foreground=COLOR_TEXT_PRIMARY,
        fieldbackground="#FFFFFF",
        rowheight=32,
        font=FONT_BODY,
        borderwidth=0
    )
    style.map(
        "Treeview",
        background=[("selected", "#E4EAE1")],
        foreground=[("selected", COLOR_TEXT_PRIMARY)]
    )

    style.configure(
        "Treeview.Heading",
        background="#EBE7DD",
        foreground=COLOR_TEXT_PRIMARY,
        font=(FONT_FAMILY, 10, "bold"),
        padding=(8, 6),
        relief="flat"
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#DFD9CD")]
    )

    # --- Combobox (Dropdowns) Styling ---
    style.configure(
        "TCombobox",
        fieldbackground="#FFFFFF",
        background="#FFFFFF",
        foreground=COLOR_TEXT_PRIMARY,
        selectbackground="#E4EAE1",
        selectforeground=COLOR_TEXT_PRIMARY,
        arrowcolor=COLOR_TEXT_PRIMARY,
        padding=5
    )

    # --- TButton Styling ---
    style.configure(
        "Accent.TButton",
        background=COLOR_ACCENT,
        foreground="#FFFFFF",
        font=FONT_BUTTON,
        padding=(14, 8),
        borderwidth=0
    )
    style.map(
        "Accent.TButton",
        background=[("active", COLOR_ACCENT_HOVER)]
    )

    style.configure(
        "Secondary.TButton",
        background="#EBE7DD",
        foreground=COLOR_TEXT_PRIMARY,
        font=FONT_BUTTON,
        padding=(12, 6),
        borderwidth=0
    )
    style.map(
        "Secondary.TButton",
        background=[("active", "#DFD9CD")]
    )

    return style
