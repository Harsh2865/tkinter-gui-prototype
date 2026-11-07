import tkinter as tk
from tkinter import ttk, messagebox

from ui.theme import (
    COLOR_BG, COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    FONT_SECTION, FONT_BODY, FONT_BUTTON, FONT_SMALL, FONT_BODY_BOLD
)
from ui.components import ActionButton
from logic.guest_logic import (
    get_all_guests, search_guests, add_guest, update_guest, delete_guest
)


class GuestFormDialog(tk.Toplevel):
    def __init__(self, parent, mode="add", guest_data=None, on_success_callback=None):
        super().__init__(parent)
        self.mode = mode
        self.guest_data = guest_data or {}
        self.on_success_callback = on_success_callback

        title_text = "Register New Guest" if mode == "add" else f"Edit Guest: {self.guest_data.get('full_name', '')}"
        self.title(f"Staywise — {title_text}")
        self.geometry("440x360")
        self.resizable(False, False)
        self.configure(bg=COLOR_CARD_BG)

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Center over parent
        self.update_idletasks()
        pw = parent.winfo_toplevel()
        x = pw.winfo_x() + (pw.winfo_width() // 2) - (440 // 2)
        y = pw.winfo_y() + (pw.winfo_height() // 2) - (360 // 2)
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
            text="Enter guest profile information and contact details.",
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG
        )
        lbl_desc.pack(anchor="w", pady=(2, 0))

        # Form Fields Container
        form_frame = tk.Frame(self, bg=COLOR_CARD_BG, padx=24, pady=20)
        form_frame.pack(fill="both", expand=True)

        # 1. Full Name
        lbl_name = tk.Label(
            form_frame,
            text="Guest Full Name *",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_name.pack(anchor="w", pady=(0, 4))

        self.ent_name = ttk.Entry(form_frame, font=FONT_BODY)
        self.ent_name.pack(fill="x", pady=(0, 16))
        if self.mode == "edit":
            self.ent_name.insert(0, str(self.guest_data.get("full_name", "")))

        # 2. Contact Number
        lbl_contact = tk.Label(
            form_frame,
            text="Contact Number / Phone *",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_contact.pack(anchor="w", pady=(0, 4))

        self.ent_contact = ttk.Entry(form_frame, font=FONT_BODY)
        self.ent_contact.pack(fill="x", pady=(0, 6))
        if self.mode == "edit":
            self.ent_contact.insert(0, str(self.guest_data.get("contact_number", "")))

        lbl_contact_hint = tk.Label(
            form_frame,
            text="e.g. +1 555-0192, +44 20 7946 0991, or 9876543210 (min 7 digits)",
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG
        )
        lbl_contact_hint.pack(anchor="w", pady=(0, 10))

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
            text="Save Guest" if self.mode == "add" else "Update Guest",
            command=self._on_save
        )
        btn_save.pack(side="right")

        # Focus name field
        self.ent_name.focus_set()

    def _on_save(self):
        """Validates inputs and saves guest to MySQL."""
        name = self.ent_name.get().strip()
        contact = self.ent_contact.get().strip()

        if self.mode == "add":
            success, message, new_id = add_guest(name, contact)
            if success:
                messagebox.showinfo("Success", message, parent=self)
                if self.on_success_callback:
                    self.on_success_callback()
                self.destroy()
            else:
                messagebox.showerror("Validation / Database Error", message, parent=self)
        else:
            guest_id = self.guest_data.get("guest_id")
            success, message = update_guest(guest_id, name, contact)
            if success:
                messagebox.showinfo("Success", message, parent=self)
                if self.on_success_callback:
                    self.on_success_callback()
                self.destroy()
            else:
                messagebox.showerror("Validation / Database Error", message, parent=self)


class GuestsView(tk.Frame):
    """
    Guests registry screen providing real-time listing from MySQL,
    search by name or contact number, and CRUD actions.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self.guests_cache = []
        self._build_ui()
        self.load_guests()

    def _build_ui(self):
        container = tk.Frame(self, bg=COLOR_BG, padx=24, pady=20)
        container.pack(fill="both", expand=True)

        # ---------------- Toolbar: Search & Actions ----------------
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
            text="Search Guest:",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_search.pack(side="left", padx=(0, 8))

        self.ent_search = ttk.Entry(toolbar, width=28)
        self.ent_search.pack(side="left", padx=(0, 16))
        self.ent_search.bind("<KeyRelease>", self._on_search_changed)

        # Action Buttons on Right
        btn_add = ActionButton(
            toolbar,
            text="+ Add Guest",
            command=self.open_add_guest_dialog
        )
        btn_add.pack(side="right", padx=(6, 0))

        btn_edit = tk.Button(
            toolbar,
            text="Edit Guest",
            font=FONT_BUTTON,
            bg="#EBE7DD",
            fg=COLOR_TEXT_PRIMARY,
            activebackground="#DFD9CD",
            relief="flat",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.open_edit_guest_dialog
        )
        btn_edit.pack(side="right", padx=(6, 0))

        btn_delete = tk.Button(
            toolbar,
            text="Delete Guest",
            font=FONT_BUTTON,
            bg="#F9E8E6",
            fg="#B94A48",
            activebackground="#F2D6D3",
            relief="flat",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.confirm_delete_guest
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
            command=self.load_guests
        )
        btn_refresh.pack(side="right", padx=(6, 0))

        # ---------------- Guests Table Container ----------------
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
            text="Registered Guests Directory",
            font=FONT_SECTION,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG
        )
        lbl_table_title.pack(side="left")

        self.lbl_count = tk.Label(
            header_frame,
            text="Loading guests...",
            font=FONT_SMALL,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_BG
        )
        self.lbl_count.pack(side="right")

        cols = ("id", "name", "contact", "bookings")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", height=12)

        self.tree.heading("id", text="Guest ID", anchor="center")
        self.tree.heading("name", text="Guest Full Name", anchor="w")
        self.tree.heading("contact", text="Contact Number", anchor="w")
        self.tree.heading("bookings", text="Total Reservations", anchor="center")

        self.tree.column("id", width=90, anchor="center")
        self.tree.column("name", width=300, anchor="w")
        self.tree.column("contact", width=220, anchor="w")
        self.tree.column("bookings", width=180, anchor="center")

        # Double click row to edit
        self.tree.bind("<Double-1>", lambda event: self.open_edit_guest_dialog())

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ---------------- Event Handlers & Data Binding ----------------

    def load_guests(self):
        """Fetches guests from MySQL and populates Treeview table."""
        search_txt = self.ent_search.get().strip()
        success, result = search_guests(search_txt)

        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not success:
            self.lbl_count.config(text="Database connection error", fg="#B94A48")
            messagebox.showerror("Database Error", result, parent=self)
            return

        guests = result
        self.guests_cache = guests

        for g in guests:
            count = g["booking_count"]
            booking_label = f"{count} Booking{'s' if count != 1 else ''}"
            self.tree.insert(
                "",
                "end",
                iid=str(g["guest_id"]),
                values=(g["guest_id"], g["full_name"], g["contact_number"], booking_label)
            )

        total_cnt = len(guests)
        if total_cnt == 0:
            if search_txt:
                self.lbl_count.config(text="No matching guests found", fg=COLOR_TEXT_SECONDARY)
            else:
                self.lbl_count.config(text="Guest registry empty — click '+ Add Guest' to register", fg=COLOR_TEXT_SECONDARY)
        else:
            self.lbl_count.config(text=f"Showing {total_cnt} registered guest{'s' if total_cnt != 1 else ''}", fg=COLOR_TEXT_SECONDARY)

    def _on_search_changed(self, event=None):
        """Filter table dynamically as user types in search box."""
        self.load_guests()

    def _get_selected_guest(self):
        """Returns the dictionary for the currently selected guest, or None."""
        selected_items = self.tree.selection()
        if not selected_items:
            return None

        guest_id_str = selected_items[0]
        try:
            target_id = int(guest_id_str)
            for g in self.guests_cache:
                if g["guest_id"] == target_id:
                    return g
        except ValueError:
            pass
        return None

    def open_add_guest_dialog(self):
        """Opens modal dialog to register a new guest."""
        GuestFormDialog(
            self,
            mode="add",
            on_success_callback=self.load_guests
        )

    def open_edit_guest_dialog(self):
        """Opens modal dialog to edit the selected guest."""
        selected = self._get_selected_guest()
        if not selected:
            messagebox.showwarning(
                "Selection Required",
                "Please select a guest from the table to edit.",
                parent=self
            )
            return

        GuestFormDialog(
            self,
            mode="edit",
            guest_data=selected,
            on_success_callback=self.load_guests
        )

    def confirm_delete_guest(self):
        """
        Deletes the selected guest after checking reservation references.
        Safe deletion enforces foreign key constraints without crashing.
        """
        selected = self._get_selected_guest()
        if not selected:
            messagebox.showwarning(
                "Selection Required",
                "Please select a guest from the table to delete.",
                parent=self
            )
            return

        guest_id = selected["guest_id"]
        guest_name = selected["full_name"]

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to permanently delete guest profile '{guest_name}'?\n\n"
            "This action cannot be undone.",
            parent=self
        )
        if not confirm:
            return

        success, message = delete_guest(guest_id)
        if success:
            messagebox.showinfo("Guest Deleted", message, parent=self)
            self.load_guests()
        else:
            messagebox.showwarning("Deletion Prevented", message, parent=self)
