import tkinter as tk
from tkinter import ttk
from ui.theme import (
    COLOR_BG, COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_SIDEBAR, COLOR_SIDEBAR_ACTIVE,
    COLOR_SIDEBAR_HOVER, FONT_CARD_LABEL, FONT_CARD_VALUE, FONT_SMALL, FONT_BODY_BOLD,
    FONT_BUTTON, FONT_BODY
)


class StatCard(tk.Frame):
    """
    A boutique-styled statistics card displaying a KPI metric.
    Includes a subtle accent bar, label, large value, and descriptive caption.
    """
    def __init__(self, parent, title, value, caption="", accent_color=COLOR_ACCENT, **kwargs):
        super().__init__(
            parent,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=16,
            pady=14,
            **kwargs
        )
        self.accent_color = accent_color

        # Top decorative accent strip
        accent_strip = tk.Frame(self, bg=accent_color, height=3)
        accent_strip.pack(fill="x", side="top", pady=(0, 10))

        # Card Title / Label
        self.lbl_title = tk.Label(
            self,
            text=title.upper(),
            font=FONT_CARD_LABEL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG,
            anchor="w"
        )
        self.lbl_title.pack(fill="x", anchor="w")

        # Metric Value
        self.lbl_value = tk.Label(
            self,
            text=str(value),
            font=FONT_CARD_VALUE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
            anchor="w"
        )
        self.lbl_value.pack(fill="x", anchor="w", pady=(2, 4))

        # Bottom Caption / Context
        self.lbl_caption = tk.Label(
            self,
            text=caption,
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG,
            anchor="w"
        )
        self.lbl_caption.pack(fill="x", anchor="w")

    def update_value(self, new_value, new_caption=None):
        """Update the displayed metric value dynamically."""
        self.lbl_value.config(text=str(new_value))
        if new_caption is not None:
            self.lbl_caption.config(text=new_caption)


class SidebarButton(tk.Frame):
    """
    Interactive sidebar navigation button with active indicator pill,
    clean icon/text display, and responsive hover transitions.
    """
    def __init__(self, parent, text, icon="•", command=None, **kwargs):
        super().__init__(parent, bg=COLOR_SIDEBAR, cursor="hand2", **kwargs)
        self.command = command
        self.is_active = False

        # Left active pill indicator
        self.indicator = tk.Frame(self, bg=COLOR_SIDEBAR, width=4)
        self.indicator.pack(side="left", fill="y")

        # Icon Label
        self.lbl_icon = tk.Label(
            self,
            text=icon,
            font=("Segoe UI Symbol", 12),
            fg="#C2CCBA",
            bg=COLOR_SIDEBAR,
            width=2
        )
        self.lbl_icon.pack(side="left", padx=(10, 4), pady=10)

        # Button Text
        self.lbl_text = tk.Label(
            self,
            text=text,
            font=FONT_BUTTON,
            fg="#E6ECE2",
            bg=COLOR_SIDEBAR,
            anchor="w"
        )
        self.lbl_text.pack(side="left", fill="x", expand=True, pady=10)

        # Bind click and hover events to all child widgets
        for widget in (self, self.indicator, self.lbl_icon, self.lbl_text):
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def _on_click(self, event=None):
        if self.command:
            self.command()

    def _on_enter(self, event=None):
        if not self.is_active:
            self._set_bg(COLOR_SIDEBAR_HOVER)

    def _on_leave(self, event=None):
        if not self.is_active:
            self._set_bg(COLOR_SIDEBAR)

    def set_active(self, active=True):
        self.is_active = active
        if active:
            self._set_bg(COLOR_SIDEBAR_ACTIVE)
            self.indicator.config(bg=COLOR_ACCENT)
            self.lbl_text.config(fg="#FFFFFF")
            self.lbl_icon.config(fg=COLOR_ACCENT)
        else:
            self._set_bg(COLOR_SIDEBAR)
            self.indicator.config(bg=COLOR_SIDEBAR)
            self.lbl_text.config(fg="#E6ECE2")
            self.lbl_icon.config(fg="#C2CCBA")

    def _set_bg(self, color):
        self.config(bg=color)
        self.lbl_icon.config(bg=color)
        self.lbl_text.config(bg=color)


class ActionButton(tk.Button):
    """
    Styled button for primary actions with smooth hover effect.
    """
    def __init__(self, parent, text, command=None, bg=COLOR_ACCENT, fg="#FFFFFF",
                 hover_bg=COLOR_ACCENT_HOVER, **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            font=FONT_BUTTON,
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            padx=14,
            pady=7,
            cursor="hand2",
            **kwargs
        )
        self.default_bg = bg
        self.hover_bg = hover_bg
        self.bind("<Enter>", lambda e: self.config(bg=self.hover_bg))
        self.bind("<Leave>", lambda e: self.config(bg=self.default_bg))
