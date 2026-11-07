from datetime import datetime, timedelta, date
import tkinter as tk
from tkinter import ttk, messagebox

from ui.theme import (
    COLOR_BG, COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    FONT_SECTION, FONT_BODY, FONT_BUTTON, FONT_SMALL, FONT_BODY_BOLD,
    COLOR_STATUS_AVAILABLE, COLOR_STATUS_OCCUPIED, COLOR_STATUS_MAINTENANCE,
    COLOR_STATUS_BOOKED, CURRENCY_SYMBOL
)
from ui.components import ActionButton
from logic.booking_logic import (
    get_all_reservations, search_and_filter_reservations,
    create_reservation, update_reservation, check_in_reservation,
    check_out_reservation, cancel_reservation, get_selectable_guests,
    get_selectable_rooms, VALID_RESERVATION_STATUSES
)


class ReservationFormDialog(tk.Toplevel):
    """
    Modal dialog window for Creating or Editing a Hotel Reservation.
    Enforces room availability, date validation, and overlap checks.
    """
    def __init__(self, parent, mode="add", res_data=None, on_success_callback=None):
        super().__init__(parent)
        self.mode = mode
        self.res_data = res_data or {}
        self.on_success_callback = on_success_callback

        title_text = "Create New Reservation" if mode == "add" else f"Edit Booking #{self.res_data.get('reservation_id')}"
        self.title(f"Staywise — {title_text}")
        self.geometry("500x560")
        self.resizable(False, False)
        self.configure(bg=COLOR_CARD_BG)

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Center over parent
        self.update_idletasks()
        pw = parent.winfo_toplevel()
        x = pw.winfo_x() + (pw.winfo_width() // 2) - (500 // 2)
        y = pw.winfo_y() + (pw.winfo_height() // 2) - (560 // 2)
        self.geometry(f"+{max(10, x)}+{max(10, y)}")

        self.guests_list = get_selectable_guests()
        self.rooms_list = get_selectable_rooms()

        self._build_form(title_text)

    def _build_form(self, title_text):
        # Header Container
        header = tk.Frame(self, bg=COLOR_BG, padx=20, pady=16)
        header.pack(fill="x")

        lbl_title = tk.Label(
            header,
            text=title_text,
            font=FONT_SECTION,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG
        )
        lbl_title.pack(anchor="w")

        lbl_desc = tk.Label(
            header,
            text="Select guest, assigned room, and stay date interval.",
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG
        )
        lbl_desc.pack(anchor="w", pady=(2, 0))

        # Form Fields Container
        form_frame = tk.Frame(self, bg=COLOR_CARD_BG, padx=24, pady=16)
        form_frame.pack(fill="both", expand=True)

        # 1. Guest Selection
        lbl_guest = tk.Label(
            form_frame,
            text="Guest Profile *",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_guest.pack(anchor="w", pady=(0, 4))

        guest_names = [label for _, label in self.guests_list]
        self.cmb_guest = ttk.Combobox(
            form_frame,
            values=guest_names,
            state="readonly",
            font=FONT_BODY
        )
        if not guest_names:
            self.cmb_guest.set("No guests registered — register a guest first")
        else:
            # Pre-select matching guest if editing
            curr_guest_id = self.res_data.get("guest_id")
            selected_idx = 0
            if curr_guest_id:
                for idx, (gid, _) in enumerate(self.guests_list):
                    if gid == curr_guest_id:
                        selected_idx = idx
                        break
            self.cmb_guest.current(selected_idx)

        self.cmb_guest.pack(fill="x", pady=(0, 14))

        # 2. Room Selection
        lbl_room = tk.Label(
            form_frame,
            text="Assigned Room *",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_room.pack(anchor="w", pady=(0, 4))

        room_labels = [item[1] for item in self.rooms_list]
        self.cmb_room = ttk.Combobox(
            form_frame,
            values=room_labels,
            state="readonly",
            font=FONT_BODY
        )
        if not room_labels:
            self.cmb_room.set("No rooms in inventory")
        else:
            curr_room_id = self.res_data.get("room_id")
            selected_room_idx = 0
            if curr_room_id:
                for idx, item in enumerate(self.rooms_list):
                    if item[0] == curr_room_id:
                        selected_room_idx = idx
                        break
            self.cmb_room.current(selected_room_idx)

        # If guest is already checked in, lock room dropdown
        if self.mode == "edit" and self.res_data.get("status") == "Checked In":
            self.cmb_room.configure(state="disabled")
            lbl_room_lock = tk.Label(
                form_frame,
                text="🔒 Assigned room is locked for in-house guests (dates only).",
                font=FONT_SMALL,
                fg=COLOR_TEXT_SECONDARY,
                bg=COLOR_CARD_BG
            )
            lbl_room_lock.pack(anchor="w", pady=(0, 10))
        else:
            self.cmb_room.pack(fill="x", pady=(0, 14))

        # 3. Dates Container (Check-in & Check-out side by side)
        dates_frame = tk.Frame(form_frame, bg=COLOR_CARD_BG)
        dates_frame.pack(fill="x", pady=(0, 14))
        dates_frame.columnconfigure(0, weight=1)
        dates_frame.columnconfigure(1, weight=1)

        # Check-in Date
        lbl_cin = tk.Label(
            dates_frame,
            text="Check-In Date (YYYY-MM-DD) *",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_cin.grid(row=0, column=0, sticky="w", pady=(0, 4), padx=(0, 8))

        self.ent_cin = ttk.Entry(dates_frame, font=FONT_BODY)
        self.ent_cin.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        # Check-out Date
        lbl_cout = tk.Label(
            dates_frame,
            text="Check-Out Date (YYYY-MM-DD) *",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_cout.grid(row=0, column=1, sticky="w", pady=(0, 4), padx=(8, 0))

        self.ent_cout = ttk.Entry(dates_frame, font=FONT_BODY)
        self.ent_cout.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        # Set default dates
        if self.mode == "edit":
            cin_val = self.res_data.get("check_in")
            cout_val = self.res_data.get("check_out")
            self.ent_cin.insert(0, cin_val.strftime("%Y-%m-%d") if hasattr(cin_val, "strftime") else str(cin_val))
            self.ent_cout.insert(0, cout_val.strftime("%Y-%m-%d") if hasattr(cout_val, "strftime") else str(cout_val))
        else:
            today = date.today()
            self.ent_cin.insert(0, today.strftime("%Y-%m-%d"))
            self.ent_cout.insert(0, (today + timedelta(days=2)).strftime("%Y-%m-%d"))

        # 4. Calculation Preview Card
        calc_box = tk.Frame(
            form_frame,
            bg="#F9F8F5",
            highlightthickness=1,
            highlightbackground="#E2DED2",
            padx=12,
            pady=10
        )
        calc_box.pack(fill="x", pady=(0, 10))

        self.lbl_calc_info = tk.Label(
            calc_box,
            text="ℹ  Reservation interval is check-in inclusive to check-out exclusive.",
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg="#F9F8F5",
            justify="left",
            wraplength=420
        )
        self.lbl_calc_info.pack(anchor="w")

        # Bind live price preview updates
        self.cmb_room.bind("<<ComboboxSelected>>", self._update_calc_preview)
        self.ent_cin.bind("<KeyRelease>", self._update_calc_preview)
        self.ent_cout.bind("<KeyRelease>", self._update_calc_preview)
        self._update_calc_preview()

        # Bottom Button Bar
        btn_bar = tk.Frame(self, bg=COLOR_BG, padx=20, pady=14)
        btn_bar.pack(fill="x", side="bottom")

        btn_cancel = tk.Button(
            btn_bar,
            text="Cancel",
            font=FONT_BUTTON,
            bg="#EBE7DD",
            fg=COLOR_TEXT_PRIMARY,
            activebackground="#DFD9CD",
            relief="flat",
            bd=0,
            padx=14,
            pady=7,
            cursor="hand2",
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=(8, 0))

        btn_save = ActionButton(
            btn_bar,
            text="Confirm Reservation" if self.mode == "add" else "Update Reservation",
            command=self._on_save
        )
        btn_save.pack(side="right")

    def _update_calc_preview(self, event=None):
        """Dynamically computes and displays nightly rate and estimated total."""
        room_idx = self.cmb_room.current()
        price = None
        if 0 <= room_idx < len(self.rooms_list):
            item = self.rooms_list[room_idx]
            if len(item) > 3:
                price = item[3]

        cin_str = self.ent_cin.get().strip()
        cout_str = self.ent_cout.get().strip()

        try:
            cin_date = datetime.strptime(cin_str, "%Y-%m-%d").date()
            cout_date = datetime.strptime(cout_str, "%Y-%m-%d").date()
            nights = (cout_date - cin_date).days
            if nights > 0 and price is not None:
                est_total = nights * float(price)
                self.lbl_calc_info.config(
                    text=f"Rate: {CURRENCY_SYMBOL}{float(price):,.2f}/night  •  {nights} night{'s' if nights != 1 else ''}  •  Estimated Total: {CURRENCY_SYMBOL}{est_total:,.2f}",
                    fg=COLOR_TEXT_PRIMARY
                )
            elif nights <= 0:
                self.lbl_calc_info.config(
                    text="⚠  Check-out date must be strictly after check-in date.",
                    fg="#B94A48"
                )
            elif price is not None:
                self.lbl_calc_info.config(
                    text=f"Rate: {CURRENCY_SYMBOL}{float(price):,.2f}/night  •  Enter stay dates to preview total.",
                    fg=COLOR_TEXT_SECONDARY
                )
            else:
                self.lbl_calc_info.config(
                    text="ℹ  Reservation interval is check-in inclusive to check-out exclusive.",
                    fg=COLOR_TEXT_SECONDARY
                )
        except ValueError:
            if price is not None:
                self.lbl_calc_info.config(
                    text=f"Rate: {CURRENCY_SYMBOL}{float(price):,.2f}/night  •  Enter dates (YYYY-MM-DD).",
                    fg=COLOR_TEXT_SECONDARY
                )
            else:
                self.lbl_calc_info.config(
                    text="ℹ  Reservation interval is check-in inclusive to check-out exclusive.",
                    fg=COLOR_TEXT_SECONDARY
                )

    def _on_save(self):
        """Validates form and executes reservation transaction."""
        # Check guest selection
        guest_idx = self.cmb_guest.current()
        if guest_idx < 0 or guest_idx >= len(self.guests_list):
            messagebox.showwarning("Validation Error", "Please select a registered guest from the dropdown.", parent=self)
            return
        guest_id = self.guests_list[guest_idx][0]

        # Check room selection
        room_idx = self.cmb_room.current()
        if room_idx < 0 or room_idx >= len(self.rooms_list):
            messagebox.showwarning("Validation Error", "Please select an assigned room from the dropdown.", parent=self)
            return
        room_id = self.rooms_list[room_idx][0]

        cin_str = self.ent_cin.get().strip()
        cout_str = self.ent_cout.get().strip()

        if self.mode == "add":
            success, message, new_id = create_reservation(guest_id, room_id, cin_str, cout_str)
            if success:
                messagebox.showinfo("Success", message, parent=self)
                if self.on_success_callback:
                    self.on_success_callback()
                self.destroy()
            else:
                messagebox.showerror("Booking Conflict / Error", message, parent=self)
        else:
            res_id = self.res_data.get("reservation_id")
            success, message = update_reservation(res_id, guest_id, room_id, cin_str, cout_str)
            if success:
                messagebox.showinfo("Success", message, parent=self)
                if self.on_success_callback:
                    self.on_success_callback()
                self.destroy()
            else:
                messagebox.showerror("Booking Conflict / Error", message, parent=self)


class ReservationsView(tk.Frame):
    """
    Reservations screen displaying master bookings registry from MySQL,
    search by guest/room, status filtering, and front-desk actions.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self.reservations_cache = []
        self._build_ui()
        self.load_reservations()

    def _build_ui(self):
        container = tk.Frame(self, bg=COLOR_BG, padx=24, pady=20)
        container.pack(fill="both", expand=True)

        # ---------------- Toolbar: Search, Filters & Actions ----------------
        toolbar = tk.Frame(
            container,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=16,
            pady=12
        )
        toolbar.pack(fill="x", pady=(0, 16))

        lbl_search = tk.Label(
            toolbar,
            text="Search Booking:",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_search.pack(side="left", padx=(0, 8))

        self.ent_search = ttk.Entry(toolbar, width=16)
        self.ent_search.pack(side="left", padx=(0, 16))
        self.ent_search.bind("<KeyRelease>", self._on_filter_changed)

        lbl_status = tk.Label(
            toolbar,
            text="Filter Status:",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_status.pack(side="left", padx=(0, 8))

        self.cmb_status = ttk.Combobox(
            toolbar,
            values=["All Statuses"] + list(VALID_RESERVATION_STATUSES),
            state="readonly",
            width=14
        )
        self.cmb_status.current(0)
        self.cmb_status.pack(side="left", padx=(0, 16))
        self.cmb_status.bind("<<ComboboxSelected>>", self._on_filter_changed)

        # Action Buttons on Right
        btn_add = ActionButton(
            toolbar,
            text="+ New Reservation",
            command=self.open_add_reservation_dialog
        )
        btn_add.pack(side="right", padx=(6, 0))

        btn_edit = tk.Button(
            toolbar,
            text="Edit Dates",
            font=FONT_BUTTON,
            bg="#EBE7DD",
            fg=COLOR_TEXT_PRIMARY,
            activebackground="#DFD9CD",
            relief="flat",
            bd=0,
            padx=10,
            pady=7,
            cursor="hand2",
            command=self.open_edit_reservation_dialog
        )
        btn_edit.pack(side="right", padx=(6, 0))

        btn_checkin = tk.Button(
            toolbar,
            text="Check In",
            font=FONT_BUTTON,
            bg="#DCE7DF",
            fg="#2D5A3E",
            activebackground="#CEDDD2",
            relief="flat",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.handle_check_in
        )
        btn_checkin.pack(side="right", padx=(6, 0))

        btn_checkout = tk.Button(
            toolbar,
            text="Check Out",
            font=FONT_BUTTON,
            bg="#EBE7DD",
            fg=COLOR_TEXT_PRIMARY,
            activebackground="#DFD9CD",
            relief="flat",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.handle_check_out
        )
        btn_checkout.pack(side="right", padx=(6, 0))

        btn_cancel = tk.Button(
            toolbar,
            text="Cancel Booking",
            font=FONT_BUTTON,
            bg="#F9E8E6",
            fg="#B94A48",
            activebackground="#F2D6D3",
            relief="flat",
            bd=0,
            padx=10,
            pady=7,
            cursor="hand2",
            command=self.handle_cancel_booking
        )
        btn_cancel.pack(side="right", padx=(6, 0))

        btn_refresh = tk.Button(
            toolbar,
            text="⟳ Refresh",
            font=FONT_BUTTON,
            bg="#EBE7DD",
            fg=COLOR_TEXT_PRIMARY,
            activebackground="#DFD9CD",
            relief="flat",
            bd=0,
            padx=8,
            pady=7,
            cursor="hand2",
            command=self.load_reservations
        )
        btn_refresh.pack(side="right", padx=(6, 0))

        # ---------------- Reservations Table Container ----------------
        table_container = tk.Frame(
            container,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=16,
            pady=16
        )
        table_container.pack(fill="both", expand=True)

        header_frame = tk.Frame(table_container, bg=COLOR_CARD_BG)
        header_frame.pack(fill="x", pady=(0, 10))

        lbl_table_title = tk.Label(
            header_frame,
            text="Master Reservations Registry",
            font=FONT_SECTION,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_table_title.pack(side="left")

        self.lbl_count = tk.Label(
            header_frame,
            text="Loading reservations...",
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG
        )
        self.lbl_count.pack(side="right")

        cols = ("id", "guest", "room", "check_in", "check_out", "nights", "total", "status")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", height=12)

        self.tree.heading("id", text="Booking ID", anchor="center")
        self.tree.heading("guest", text="Guest Name", anchor="w")
        self.tree.heading("room", text="Assigned Room", anchor="w")
        self.tree.heading("check_in", text="Check-In", anchor="center")
        self.tree.heading("check_out", text="Check-Out", anchor="center")
        self.tree.heading("nights", text="Nights", anchor="center")
        self.tree.heading("total", text="Est. Total", anchor="e")
        self.tree.heading("status", text="Current Status", anchor="center")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("guest", width=180, anchor="w")
        self.tree.column("room", width=160, anchor="w")
        self.tree.column("check_in", width=110, anchor="center")
        self.tree.column("check_out", width=110, anchor="center")
        self.tree.column("nights", width=70, anchor="center")
        self.tree.column("total", width=110, anchor="e")
        self.tree.column("status", width=110, anchor="center")

        # Visual status tags
        self.tree.tag_configure("Booked", foreground="#35617D")
        self.tree.tag_configure("Checked In", foreground="#B86200")
        self.tree.tag_configure("Checked Out", foreground="#2D6A4F")
        self.tree.tag_configure("Cancelled", foreground="#A93E3A")

        # Double click to edit
        self.tree.bind("<Double-1>", lambda event: self.open_edit_reservation_dialog())

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ---------------- Event Handlers & Data Binding ----------------

    def load_reservations(self):
        """Fetches reservations from MySQL and populates Treeview table."""
        search_txt = self.ent_search.get().strip()
        status_filter = self.cmb_status.get()

        success, result = search_and_filter_reservations(search_txt, status_filter)

        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not success:
            self.lbl_count.config(text="Database connection error", fg="#B94A48")
            messagebox.showerror("Database Error", result, parent=self)
            return

        reservations = result
        self.reservations_cache = reservations

        for r in reservations:
            cin = r["check_in"].strftime("%Y-%m-%d") if hasattr(r["check_in"], "strftime") else str(r["check_in"])
            cout = r["check_out"].strftime("%Y-%m-%d") if hasattr(r["check_out"], "strftime") else str(r["check_out"])
            total_formatted = f"{CURRENCY_SYMBOL}{float(r['total_amount']):,.2f}"
            room_desc = f"Room {r['room_number']} ({r['room_type']})"
            status = r["status"]

            self.tree.insert(
                "",
                "end",
                iid=str(r["reservation_id"]),
                values=(
                    r["reservation_id"],
                    r["guest_name"],
                    room_desc,
                    cin,
                    cout,
                    f"{r['nights']}n",
                    total_formatted,
                    status
                ),
                tags=(status,)
            )

        total_cnt = len(reservations)
        if total_cnt == 0:
            if search_txt or status_filter != "All Statuses":
                self.lbl_count.config(text="No matching reservations found", fg=COLOR_TEXT_SECONDARY)
            else:
                self.lbl_count.config(text="No reservations booked yet — click '+ New Reservation' to book", fg=COLOR_TEXT_SECONDARY)
        else:
            self.lbl_count.config(text=f"Showing {total_cnt} reservation{'s' if total_cnt != 1 else ''}", fg=COLOR_TEXT_SECONDARY)

    def _on_filter_changed(self, event=None):
        """Triggered when search input or status filter changes."""
        self.load_reservations()

    def _get_selected_reservation(self):
        """Returns the dictionary for the currently selected reservation, or None."""
        selected_items = self.tree.selection()
        if not selected_items:
            return None

        res_id_str = selected_items[0]
        try:
            target_id = int(res_id_str)
            for r in self.reservations_cache:
                if r["reservation_id"] == target_id:
                    return r
        except ValueError:
            pass
        return None

    def open_add_reservation_dialog(self):
        """Opens modal dialog to create a new booking."""
        ReservationFormDialog(
            self,
            mode="add",
            on_success_callback=self.load_reservations
        )

    def open_edit_reservation_dialog(self):
        """Opens modal dialog to edit dates of the selected reservation."""
        selected = self._get_selected_reservation()
        if not selected:
            messagebox.showwarning(
                "Selection Required",
                "Please select a reservation from the table to edit.",
                parent=self
            )
            return

        if selected["status"] in ("Checked Out", "Cancelled"):
            messagebox.showwarning(
                "Cannot Edit Completed Booking",
                f"Reservation #{selected['reservation_id']} is already {selected['status']}.\n"
                "Dates cannot be modified for closed or cancelled bookings.",
                parent=self
            )
            return

        ReservationFormDialog(
            self,
            mode="edit",
            res_data=selected,
            on_success_callback=self.load_reservations
        )

    def handle_check_in(self):
        """Executes guest check-in workflow."""
        selected = self._get_selected_reservation()
        if not selected:
            messagebox.showwarning(
                "Selection Required",
                "Please select a reservation from the table to check in.",
                parent=self
            )
            return

        res_id = selected["reservation_id"]
        confirm = messagebox.askyesno(
            "Confirm Check-In",
            f"Check in guest '{selected['guest_name']}' into Room #{selected['room_number']}?\n\n"
            f"Booking ID: #{res_id}\n"
            f"Stay Duration: {selected['check_in']} to {selected['check_out']} ({selected['nights']} nights)",
            parent=self
        )
        if not confirm:
            return

        success, message = check_in_reservation(res_id)
        if success:
            messagebox.showinfo("Check-In Complete", message, parent=self)
            self.load_reservations()
        else:
            messagebox.showerror("Check-In Failed", message, parent=self)

    def handle_check_out(self):
        """Executes guest check-out workflow."""
        selected = self._get_selected_reservation()
        if not selected:
            messagebox.showwarning(
                "Selection Required",
                "Please select a reservation from the table to check out.",
                parent=self
            )
            return

        res_id = selected["reservation_id"]
        confirm = messagebox.askyesno(
            "Confirm Check-Out",
            f"Check out guest '{selected['guest_name']}' from Room #{selected['room_number']}?\n\n"
            f"Total Bill: {CURRENCY_SYMBOL}{float(selected['total_amount']):,.2f}",
            parent=self
        )
        if not confirm:
            return

        success, message = check_out_reservation(res_id)
        if success:
            messagebox.showinfo("Check-Out Complete", message, parent=self)
            self.load_reservations()
        else:
            messagebox.showerror("Check-Out Failed", message, parent=self)

    def handle_cancel_booking(self):
        """Executes booking cancellation workflow."""
        selected = self._get_selected_reservation()
        if not selected:
            messagebox.showwarning(
                "Selection Required",
                "Please select a reservation from the table to cancel.",
                parent=self
            )
            return

        res_id = selected["reservation_id"]
        confirm = messagebox.askyesno(
            "Confirm Cancellation",
            f"Are you sure you want to cancel Reservation #{res_id} for '{selected['guest_name']}'?\n\n"
            "This will release the room for future bookings.",
            parent=self
        )
        if not confirm:
            return

        success, message = cancel_reservation(res_id)
        if success:
            messagebox.showinfo("Reservation Cancelled", message, parent=self)
            self.load_reservations()
        else:
            messagebox.showerror("Cancellation Failed", message, parent=self)
