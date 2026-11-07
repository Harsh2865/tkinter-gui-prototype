

import sys
import tkinter as tk
from datetime import datetime

# Import UI themes and view modules
from ui.theme import (
    COLOR_BG, COLOR_SIDEBAR, COLOR_CARD_BG, COLOR_CARD_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT,
    FONT_BRAND, FONT_BRAND_SUB, FONT_TITLE_LARGE, FONT_SMALL,
    FONT_BODY, setup_ttk_styles
)
from ui.components import SidebarButton
from ui.dashboard_view import DashboardView
from ui.rooms_view import RoomsView
from ui.guests_view import GuestsView
from ui.reservations_view import ReservationsView


class StaywiseApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Staywise — Boutique Hotel Management System")
        self.root.geometry("1200x740")
        self.root.minsize(1040, 660)
        self.root.configure(bg=COLOR_BG)

        # Apply custom ttk styles for treeviews, buttons, and dropdowns
        setup_ttk_styles(self.root)

        # Track active views and navigation buttons
        self.current_screen = None
        self.nav_buttons = {}

        # Build application layout
        self._build_sidebar()
        self._build_header()
        self._build_content_area()

        # Set default view to Dashboard
        self.show_dashboard()

    def _build_sidebar(self):
        """
        Creates the fixed left navigation sidebar with branding,
        nav buttons, and system connection status.
        """
        self.sidebar = tk.Frame(self.root, bg=COLOR_SIDEBAR, width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # --- Brand Logo & Title ---
        brand_frame = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR, padx=20, pady=24)
        brand_frame.pack(fill="x")

        lbl_brand = tk.Label(
            brand_frame,
            text="STAYWISE",
            font=FONT_BRAND,
            fg="#FFFFFF",
            bg=COLOR_SIDEBAR,
            anchor="w"
        )
        lbl_brand.pack(fill="x")

        lbl_tagline = tk.Label(
            brand_frame,
            text="BOUTIQUE HOTEL OS",
            font=FONT_BRAND_SUB,
            fg="#95A898",
            bg=COLOR_SIDEBAR,
            anchor="w"
        )
        lbl_tagline.pack(fill="x", pady=(2, 0))

        # Thin divider line
        divider = tk.Frame(self.sidebar, bg="#334B43", height=1)
        divider.pack(fill="x", padx=16, pady=(0, 16))

        # --- Navigation Buttons ---
        nav_items = [
            ("dashboard", "Dashboard", "❖", self.show_dashboard),
            ("rooms", "Rooms", "⊞", self.show_rooms),
            ("guests", "Guests", "👤", self.show_guests),
            ("reservations", "Reservations", "🗓", self.show_reservations),
        ]

        for key, label, icon, cmd in nav_items:
            btn = SidebarButton(
                self.sidebar,
                text=label,
                icon=icon,
                command=cmd
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = btn

        # --- System Status Indicator (Bottom of Sidebar) ---
        status_frame = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR, padx=16, pady=20)
        status_frame.pack(side="bottom", fill="x")

        status_box = tk.Frame(
            status_frame,
            bg="#1E302A",
            padx=12,
            pady=10,
            highlightthickness=1,
            highlightbackground="#2E453D"
        )
        status_box.pack(fill="x")

        lbl_status_dot = tk.Label(
            status_box,
            text="●",
            font=FONT_SMALL,
            fg="#70C18F",
            bg="#1E302A"
        )
        lbl_status_dot.pack(side="left", padx=(0, 6))

        lbl_status_text = tk.Label(
            status_box,
            text="MySQL: Connected (staywise)",
            font=FONT_SMALL,
            fg="#C5D3C8",
            bg="#1E302A"
        )
        lbl_status_text.pack(side="left")

    def _build_header(self):
        """
        Builds the top header bar with dynamic screen title and live context.
        Uses natural geometry propagation to prevent subtitle clipping.
        """
        self.header = tk.Frame(
            self.root,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=24,
            pady=14
        )
        self.header.pack(side="top", fill="x")

        # Screen Title and Subtitle Container (Left)
        title_container = tk.Frame(self.header, bg=COLOR_CARD_BG)
        title_container.pack(side="left", fill="both")

        self.lbl_page_title = tk.Label(
            title_container,
            text="Dashboard",
            font=FONT_TITLE_LARGE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
            anchor="w"
        )
        self.lbl_page_title.pack(anchor="w")

        self.lbl_page_subtitle = tk.Label(
            title_container,
            text="Real-time occupancy metrics and today's schedule",
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG,
            anchor="w"
        )
        self.lbl_page_subtitle.pack(anchor="w", pady=(2, 0))

        # Context Information (Right)
        right_container = tk.Frame(self.header, bg=COLOR_CARD_BG)
        right_container.pack(side="right", fill="y")

        today_str = datetime.now().strftime("%A, %b %d, %Y")
        lbl_date = tk.Label(
            right_container,
            text=f"📅  {today_str}",
            font=FONT_BODY,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG
        )
        lbl_date.pack(side="right", expand=True)

    def _build_content_area(self):
        """
        Creates the main content container where the views are swapped.
        """
        self.content_container = tk.Frame(self.root, bg=COLOR_BG)
        self.content_container.pack(side="top", fill="both", expand=True)

        # Instantiate all screen views
        self.views = {
            "dashboard": DashboardView(self.content_container),
            "rooms": RoomsView(self.content_container),
            "guests": GuestsView(self.content_container),
            "reservations": ReservationsView(self.content_container),
        }

    def _switch_screen(self, screen_key, title, subtitle):
        """
        Common navigation routing method.
        Hides the current screen, shows the selected screen, and updates active tab state.
        """
        # Update active sidebar buttons
        for key, btn in self.nav_buttons.items():
            btn.set_active(key == screen_key)

        # Update Header Title & Subtitle
        self.lbl_page_title.config(text=title)
        self.lbl_page_subtitle.config(text=subtitle)

        # Hide all views and display the selected one
        for key, view in self.views.items():
            if key == screen_key:
                view.pack(fill="both", expand=True)
            else:
                view.pack_forget()

        self.current_screen = screen_key

    # ---------------- Explicit Navigation Callbacks ----------------

    def show_dashboard(self):
        """Callback to switch to Dashboard view."""
        self._switch_screen(
            "dashboard",
            "Executive Dashboard",
            "Overview of hotel occupancy, revenue metrics, and today's arrivals & departures"
        )
        if hasattr(self.views["dashboard"], "load_dashboard"):
            self.views["dashboard"].load_dashboard()

    def show_rooms(self):
        """Callback to switch to Rooms Management view."""
        self._switch_screen(
            "rooms",
            "Room Inventory Management",
            "Browse room types, configure nightly pricing, and track live room statuses"
        )
        if hasattr(self.views["rooms"], "load_rooms"):
            self.views["rooms"].load_rooms()

    def show_guests(self):
        """Callback to switch to Guests Directory view."""
        self._switch_screen(
            "guests",
            "Guest Directory & Profiles",
            "Manage hotel guest records, contact details, and booking history"
        )
        if hasattr(self.views["guests"], "load_guests"):
            self.views["guests"].load_guests()

    def show_reservations(self):
        """Callback to switch to Reservations view."""
        self._switch_screen(
            "reservations",
            "Reservations & Front Desk",
            "Create new bookings, manage date ranges, and handle check-in & check-out workflows"
        )
        if hasattr(self.views["reservations"], "load_reservations"):
            self.views["reservations"].load_reservations()


def main():
    """Application main entry point."""
    root = tk.Tk()
    app = StaywiseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
