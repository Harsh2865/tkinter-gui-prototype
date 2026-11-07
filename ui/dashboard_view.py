from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox

from ui.theme import (
    COLOR_BG, COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    FONT_SECTION, FONT_BODY, FONT_BUTTON, FONT_SMALL, FONT_BODY_BOLD,
    COLOR_STATUS_AVAILABLE, COLOR_STATUS_OCCUPIED, COLOR_STATUS_MAINTENANCE,
    COLOR_STATUS_BOOKED
)
from ui.components import StatCard
from logic.dashboard_logic import get_dashboard_metrics, get_todays_schedule


class DashboardView(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._build_ui()
        self.load_dashboard()

    def _build_ui(self):
        container = tk.Frame(self, bg=COLOR_BG, padx=24, pady=20)
        container.pack(fill="both", expand=True)

        # ---------------- Section 1: Top Metrics Grid (4 Cards) ----------------
        cards_row1 = tk.Frame(container, bg=COLOR_BG)
        cards_row1.pack(fill="x", pady=(0, 14))

        for col in range(4):
            cards_row1.columnconfigure(col, weight=1, uniform="row1_cards")

        self.card_total = StatCard(
            cards_row1,
            title="Total Rooms",
            value="—",
            caption="Registered in hotel inventory",
            accent_color="#263C35"
        )
        self.card_total.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        self.card_available = StatCard(
            cards_row1,
            title="Available Rooms",
            value="—",
            caption="Ready for immediate check-in",
            accent_color=COLOR_STATUS_AVAILABLE
        )
        self.card_available.grid(row=0, column=1, padx=(0, 10), sticky="nsew")

        self.card_occupied = StatCard(
            cards_row1,
            title="Occupied Rooms",
            value="—",
            caption="Currently in-house guests",
            accent_color=COLOR_STATUS_OCCUPIED
        )
        self.card_occupied.grid(row=0, column=2, padx=(0, 10), sticky="nsew")

        self.card_maintenance = StatCard(
            cards_row1,
            title="Under Maintenance",
            value="—",
            caption="Out of order / service",
            accent_color=COLOR_STATUS_MAINTENANCE
        )
        self.card_maintenance.grid(row=0, column=3, padx=(0, 0), sticky="nsew")

        # ---------------- Section 2: Action Metrics Grid (3 Cards) ----------------
        cards_row2 = tk.Frame(container, bg=COLOR_BG)
        cards_row2.pack(fill="x", pady=(0, 20))

        for col in range(3):
            cards_row2.columnconfigure(col, weight=1, uniform="row2_cards")

        self.card_active_res = StatCard(
            cards_row2,
            title="Active Bookings",
            value="—",
            caption="Booked & in-house reservations",
            accent_color=COLOR_STATUS_BOOKED
        )
        self.card_active_res.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        self.card_checkins = StatCard(
            cards_row2,
            title="Today's Expected Check-Ins",
            value="—",
            caption="Arrivals scheduled for today",
            accent_color=COLOR_ACCENT
        )
        self.card_checkins.grid(row=0, column=1, padx=(0, 10), sticky="nsew")

        self.card_checkouts = StatCard(
            cards_row2,
            title="Today's Expected Check-Outs",
            value="—",
            caption="Departures scheduled for today",
            accent_color="#A2703F"
        )
        self.card_checkouts.grid(row=0, column=2, padx=(0, 0), sticky="nsew")

        # ---------------- Section 3: Today's Schedule Table ----------------
        table_container = tk.Frame(
            container,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=16,
            pady=16
        )
        table_container.pack(fill="both", expand=True)

        header_row = tk.Frame(table_container, bg=COLOR_CARD_BG)
        header_row.pack(fill="x", pady=(0, 12))

        lbl_sched = tk.Label(
            header_row,
            text="Today's Arrival & Departure Schedule",
            font=FONT_SECTION,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_sched.pack(side="left")

        # Refresh Button
        btn_refresh = tk.Button(
            header_row,
            text="⟳ Refresh Dashboard",
            font=FONT_BUTTON,
            bg="#EBE7DD",
            fg=COLOR_TEXT_PRIMARY,
            activebackground="#DFD9CD",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.load_dashboard
        )
        btn_refresh.pack(side="right", padx=(8, 0))

        self.lbl_status = tk.Label(
            header_row,
            text="Syncing with database...",
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG
        )
        self.lbl_status.pack(side="right")

        # Schedule Table (Treeview)
        cols = ("id", "event_type", "guest", "room", "dates", "status")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", height=7)

        self.tree.heading("id", text="Booking ID", anchor="center")
        self.tree.heading("event_type", text="Schedule Type", anchor="w")
        self.tree.heading("guest", text="Guest Name", anchor="w")
        self.tree.heading("room", text="Assigned Room", anchor="w")
        self.tree.heading("dates", text="Stay Duration", anchor="w")
        self.tree.heading("status", text="Current Status", anchor="center")

        self.tree.column("id", width=85, anchor="center")
        self.tree.column("event_type", width=170, anchor="w")
        self.tree.column("guest", width=220, anchor="w")
        self.tree.column("room", width=180, anchor="w")
        self.tree.column("dates", width=240, anchor="w")
        self.tree.column("status", width=120, anchor="center")

        # Visual status tags
        self.tree.tag_configure("Arrival (Check-In)", foreground="#265B7D")
        self.tree.tag_configure("Departure (Check-Out)", foreground="#9B612E")

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ---------------- Live Data Loading ----------------

    def load_dashboard(self):
        """
        Fetches live statistics and today's schedule from MySQL.
        Updates all 7 cards and the schedule table dynamically without
        creating duplicate widgets.
        """
        # 1. Load Metric Counts
        ok_metrics, metrics_data = get_dashboard_metrics()
        if not ok_metrics:
            self.lbl_status.config(text="Database connection failed", fg="#B94A48")
            self.card_total.update_value("ERR", "Database offline")
            self.card_available.update_value("ERR", "Database offline")
            self.card_occupied.update_value("ERR", "Database offline")
            self.card_maintenance.update_value("ERR", "Database offline")
            self.card_active_res.update_value("ERR", "Database offline")
            self.card_checkins.update_value("ERR", "Database offline")
            self.card_checkouts.update_value("ERR", "Database offline")
            return

        m = metrics_data
        self.card_total.update_value(m["total_rooms"], "Registered in inventory")
        self.card_available.update_value(m["available_rooms"], "Ready for guest arrival")
        self.card_occupied.update_value(m["occupied_rooms"], "Currently in-house guests")
        self.card_maintenance.update_value(m["maintenance_rooms"], "Out of service")

        self.card_active_res.update_value(m["active_bookings"], "Booked & Checked In")
        self.card_checkins.update_value(f"{m['today_checkins']} Arrivals", "Scheduled for today")
        self.card_checkouts.update_value(f"{m['today_checkouts']} Departures", "Scheduled for today")

        # 2. Load Today's Schedule Table
        ok_sched, schedule_data = get_todays_schedule()

        # Clear existing items safely
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not ok_sched:
            self.lbl_status.config(text="Failed to load schedule", fg="#B94A48")
            return

        schedule = schedule_data
        for item in schedule:
            tag = item["schedule_type"]
            room_desc = f"Room {item['room_number']} ({item['room_type']})"
            self.tree.insert(
                "",
                "end",
                iid=str(item["reservation_id"]),
                values=(
                    item["reservation_id"],
                    item["schedule_type"],
                    item["guest_name"],
                    room_desc,
                    item["dates"],
                    item["status"]
                ),
                tags=(tag,)
            )

        now_str = datetime.now().strftime("%I:%M %p")
        if not schedule:
            today_str = date.today().strftime("%b %d, %Y")
            self.lbl_status.config(
                text=f"No arrivals or departures scheduled for today ({today_str}) • Synced {now_str}",
                fg=COLOR_TEXT_SECONDARY
            )
        else:
            cnt = len(schedule)
            self.lbl_status.config(
                text=f"{cnt} scheduled operation{'s' if cnt != 1 else ''} today • Synced {now_str}",
                fg=COLOR_TEXT_SECONDARY
            )
