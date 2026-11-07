import tkinter as tk
from tkinter import ttk, messagebox

from ui.theme import (
    COLOR_BG, COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    FONT_SECTION, FONT_BODY, FONT_BUTTON, FONT_SMALL, FONT_BODY_BOLD,
    COLOR_STATUS_AVAILABLE, COLOR_STATUS_OCCUPIED, COLOR_STATUS_MAINTENANCE,
    CURRENCY_SYMBOL
)
from ui.components import ActionButton
from logic.room_logic import (
    get_all_rooms, search_and_filter_rooms, add_room,
    update_room, delete_room, VALID_ROOM_TYPES, VALID_ROOM_STATUSES
)


class RoomFormDialog(tk.Toplevel):
    def __init__(self, parent, mode="add", room_data=None, on_success_callback=None):
        super().__init__(parent)
        self.mode = mode
        self.room_data = room_data or {}
        self.on_success_callback = on_success_callback

        title_text = "Add New Room" if mode == "add" else f"Edit Room #{self.room_data.get('room_number', '')}"
        self.title(f"Staywise — {title_text}")
        self.geometry("440x480")
        self.resizable(False, False)
        self.configure(bg=COLOR_CARD_BG)

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Center dialog over parent
        self.update_idletasks()
        pw = parent.winfo_toplevel()
        x = pw.winfo_x() + (pw.winfo_width() // 2) - (440 // 2)
        y = pw.winfo_y() + (pw.winfo_height() // 2) - (480 // 2)
        self.geometry(f"+{max(10, x)}+{max(10, y)}")

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
            text="Configure room number, category, nightly rate, and operational status.",
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG
        )
        lbl_desc.pack(anchor="w", pady=(2, 0))

        # Form Fields Container
        form_frame = tk.Frame(self, bg=COLOR_CARD_BG, padx=24, pady=20)
        form_frame.pack(fill="both", expand=True)

        # 1. Room Number
        lbl_num = tk.Label(
            form_frame,
            text="Room Number *",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_num.pack(anchor="w", pady=(0, 4))

        self.ent_number = ttk.Entry(form_frame, font=FONT_BODY)
        self.ent_number.pack(fill="x", pady=(0, 14))
        if self.mode == "edit":
            self.ent_number.insert(0, str(self.room_data.get("room_number", "")))

        # 2. Room Type Dropdown
        lbl_type = tk.Label(
            form_frame,
            text="Room Category / Type *",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_type.pack(anchor="w", pady=(0, 4))

        self.cmb_type = ttk.Combobox(
            form_frame,
            values=list(VALID_ROOM_TYPES),
            state="readonly",
            font=FONT_BODY
        )
        current_type = self.room_data.get("room_type", VALID_ROOM_TYPES[0])
        if current_type in VALID_ROOM_TYPES:
            self.cmb_type.current(VALID_ROOM_TYPES.index(current_type))
        else:
            self.cmb_type.current(0)
        self.cmb_type.pack(fill="x", pady=(0, 14))

        # 3. Nightly Price
        lbl_price = tk.Label(
            form_frame,
            text=f"Price per Night ({CURRENCY_SYMBOL}) *",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_price.pack(anchor="w", pady=(0, 4))

        self.ent_price = ttk.Entry(form_frame, font=FONT_BODY)
        self.ent_price.pack(fill="x", pady=(0, 14))
        if self.mode == "edit":
            self.ent_price.insert(0, str(self.room_data.get("price", "")))

        # 4. Status Dropdown
        lbl_status = tk.Label(
            form_frame,
            text="Operational Status *",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_status.pack(anchor="w", pady=(0, 4))

        self.cmb_status = ttk.Combobox(
            form_frame,
            values=list(VALID_ROOM_STATUSES),
            state="readonly",
            font=FONT_BODY
        )
        current_status = self.room_data.get("status", "Available")
        if current_status in VALID_ROOM_STATUSES:
            self.cmb_status.current(VALID_ROOM_STATUSES.index(current_status))
        else:
            self.cmb_status.current(0)
        self.cmb_status.pack(fill="x", pady=(0, 18))

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
            text="Save Room" if self.mode == "add" else "Update Room",
            command=self._on_save
        )
        btn_save.pack(side="right")

        # Focus room number
        self.ent_number.focus_set()

    def _on_save(self):
        """Validates input fields and saves to MySQL."""
        room_num = self.ent_number.get().strip()
        room_type = self.cmb_type.get().strip()
        price_str = self.ent_price.get().strip()
        status = self.cmb_status.get().strip()

        if self.mode == "add":
            success, message, new_id = add_room(room_num, room_type, price_str, status)
            if success:
                messagebox.showinfo("Success", message, parent=self)
                if self.on_success_callback:
                    self.on_success_callback()
                self.destroy()
            else:
                messagebox.showerror("Validation / Database Error", message, parent=self)
        else:
            room_id = self.room_data.get("room_id")
            success, message = update_room(room_id, room_num, room_type, price_str, status)
            if success:
                messagebox.showinfo("Success", message, parent=self)
                if self.on_success_callback:
                    self.on_success_callback()
                self.destroy()
            else:
                messagebox.showerror("Validation / Database Error", message, parent=self)


class RoomsView(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self.rooms_cache = []
        self._build_ui()
        self.load_rooms()

    def _build_ui(self):
        container = tk.Frame(self, bg=COLOR_BG, padx=24, pady=20)
        container.pack(fill="both", expand=True)

        # ---------------- Toolbar: Search & Filters ----------------
        toolbar = tk.Frame(
            container,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=16,
            pady=12
        )
        toolbar.pack(fill="x", pady=(0, 16))

        # Search Box
        lbl_search = tk.Label(
            toolbar,
            text="Search Room #:",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_search.pack(side="left", padx=(0, 8))

        self.ent_search = ttk.Entry(toolbar, width=14)
        self.ent_search.pack(side="left", padx=(0, 16))
        self.ent_search.bind("<KeyRelease>", self._on_filter_changed)

        # Room Type Filter
        lbl_type = tk.Label(
            toolbar,
            text="Type:",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_type.pack(side="left", padx=(0, 8))

        self.cmb_type = ttk.Combobox(
            toolbar,
            values=["All Types"] + list(VALID_ROOM_TYPES),
            state="readonly",
            width=12
        )
        self.cmb_type.current(0)
        self.cmb_type.pack(side="left", padx=(0, 16))
        self.cmb_type.bind("<<ComboboxSelected>>", self._on_filter_changed)

        # Room Status Filter
        lbl_status = tk.Label(
            toolbar,
            text="Status:",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_status.pack(side="left", padx=(0, 8))

        self.cmb_status = ttk.Combobox(
            toolbar,
            values=["All Statuses"] + list(VALID_ROOM_STATUSES),
            state="readonly",
            width=14
        )
        self.cmb_status.current(0)
        self.cmb_status.pack(side="left", padx=(0, 16))
        self.cmb_status.bind("<<ComboboxSelected>>", self._on_filter_changed)

        # Action Buttons on Right
        btn_add = ActionButton(
            toolbar,
            text="+ Add Room",
            command=self.open_add_room_dialog
        )
        btn_add.pack(side="right", padx=(6, 0))

        btn_edit = tk.Button(
            toolbar,
            text="Edit Room",
            font=FONT_BUTTON,
            bg="#EBE7DD",
            fg=COLOR_TEXT_PRIMARY,
            activebackground="#DFD9CD",
            relief="flat",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.open_edit_room_dialog
        )
        btn_edit.pack(side="right", padx=(6, 0))

        btn_delete = tk.Button(
            toolbar,
            text="Delete Room",
            font=FONT_BUTTON,
            bg="#F9E8E6",
            fg="#B94A48",
            activebackground="#F2D6D3",
            relief="flat",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.confirm_delete_room
        )
        btn_delete.pack(side="right", padx=(6, 0))

        btn_refresh = tk.Button(
            toolbar,
            text="⟳ Refresh",
            font=FONT_BUTTON,
            bg="#EBE7DD",
            fg=COLOR_TEXT_PRIMARY,
            activebackground="#DFD9CD",
            relief="flat",
            bd=0,
            padx=10,
            pady=7,
            cursor="hand2",
            command=self.load_rooms
        )
        btn_refresh.pack(side="right", padx=(6, 0))

        # ---------------- Rooms Table Container ----------------
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
            text="Hotel Room Directory",
            font=FONT_SECTION,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_table_title.pack(side="left")

        self.lbl_count = tk.Label(
            header_frame,
            text="Loading rooms...",
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG
        )
        self.lbl_count.pack(side="right")

        cols = ("id", "room_num", "room_type", "price", "status")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", height=12)

        self.tree.heading("id", text="Room ID", anchor="center")
        self.tree.heading("room_num", text="Room Number", anchor="w")
        self.tree.heading("room_type", text="Category / Type", anchor="w")
        self.tree.heading("price", text="Nightly Rate", anchor="e")
        self.tree.heading("status", text="Current Status", anchor="center")

        self.tree.column("id", width=90, anchor="center")
        self.tree.column("room_num", width=160, anchor="w")
        self.tree.column("room_type", width=200, anchor="w")
        self.tree.column("price", width=160, anchor="e")
        self.tree.column("status", width=160, anchor="center")

        # Visual status tags
        self.tree.tag_configure("Available", foreground="#2D6A4F")
        self.tree.tag_configure("Occupied", foreground="#B86200")
        self.tree.tag_configure("Maintenance", foreground="#B94A48")

        # Double click to edit
        self.tree.bind("<Double-1>", lambda event: self.open_edit_room_dialog())

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ---------------- Event Handlers & Data Binding ----------------

    def load_rooms(self):
        """Fetches rooms from MySQL and updates Treeview table."""
        search_txt = self.ent_search.get().strip()
        type_filter = self.cmb_type.get()
        status_filter = self.cmb_status.get()

        success, result = search_and_filter_rooms(search_txt, type_filter, status_filter)

        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not success:
            self.lbl_count.config(text="Database connection error", fg="#B94A48")
            messagebox.showerror("Database Error", result, parent=self)
            return

        rooms = result
        self.rooms_cache = rooms

        for r in rooms:
            price_formatted = f"{CURRENCY_SYMBOL}{float(r['price']):,.2f}"
            status = r["status"]
            self.tree.insert(
                "",
                "end",
                iid=str(r["room_id"]),
                values=(r["room_id"], r["room_number"], r["room_type"], price_formatted, status),
                tags=(status,)
            )

        total_cnt = len(rooms)
        if total_cnt == 0:
            if search_txt or type_filter != "All Types" or status_filter != "All Statuses":
                self.lbl_count.config(text="No matching rooms found", fg=COLOR_TEXT_SECONDARY)
            else:
                self.lbl_count.config(text="Inventory empty — click '+ Add Room' to begin", fg=COLOR_TEXT_SECONDARY)
        else:
            self.lbl_count.config(text=f"Showing {total_cnt} room{'s' if total_cnt != 1 else ''}", fg=COLOR_TEXT_SECONDARY)

    def _on_filter_changed(self, event=None):
        """Triggered when search input or dropdown filters change."""
        self.load_rooms()

    def _get_selected_room(self):
        """Returns the dictionary for the currently selected room, or None."""
        selected_items = self.tree.selection()
        if not selected_items:
            return None

        room_id_str = selected_items[0]
        try:
            target_id = int(room_id_str)
            for r in self.rooms_cache:
                if r["room_id"] == target_id:
                    return r
        except ValueError:
            pass
        return None

    def open_add_room_dialog(self):
        """Opens modal dialog to create a new room."""
        RoomFormDialog(
            self,
            mode="add",
            on_success_callback=self.load_rooms
        )

    def open_edit_room_dialog(self):
        """Opens modal dialog to edit the selected room."""
        selected = self._get_selected_room()
        if not selected:
            messagebox.showwarning(
                "Selection Required",
                "Please select a room from the table to edit.",
                parent=self
            )
            return

        RoomFormDialog(
            self,
            mode="edit",
            room_data=selected,
            on_success_callback=self.load_rooms
        )

    def confirm_delete_room(self):
        """
        Deletes the selected room after checking reservation references.
        Safe deletion enforces foreign key constraints without crashing.
        """
        selected = self._get_selected_room()
        if not selected:
            messagebox.showwarning(
                "Selection Required",
                "Please select a room from the table to delete.",
                parent=self
            )
            return

        room_id = selected["room_id"]
        room_num = selected["room_number"]

        # Confirm user intent
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to permanently delete Room #{room_num}?\n\n"
            "This action cannot be undone.",
            parent=self
        )
        if not confirm:
            return

        # Attempt safe deletion through room_logic
        success, message = delete_room(room_id)
        if success:
            messagebox.showinfo("Room Deleted", message, parent=self)
            self.load_rooms()
        else:
            # Displays referential integrity explanation or DB error
            messagebox.showwarning("Deletion Prevented", message, parent=self)
