# Staywise — Master Viva & Practical Coding Examination Guide
**Hotel Management System | Python (Tkinter + ttk) + MySQL Connector**
**Workspace:** `C:\Users\harsh\APP`

---

## Table of Contents
1. [Project Overview & Architectural Design](#1-project-overview--architectural-design)
2. [File-by-File Codebase Explanation](#2-file-by-file-codebase-explanation)
3. [Complete Tkinter Widget Inventory](#3-complete-tkinter-widget-inventory)
4. [Layout Managers Code Map (pack vs grid vs place)](#4-layout-managers-code-map)
5. [Events, Bindings, and Callbacks Code Map](#5-events-bindings-and-callbacks-code-map)
6. [Screen-by-Screen In-Depth Execution Flows](#6-screen-by-screen-in-depth-execution-flows)
7. [MySQL Database Integration & Relational Architecture](#7-mysql-database-integration--relational-architecture)
8. [Core Python Programming Concepts Used in Staywise](#8-core-python-programming-concepts-used-in-staywise)
9. [Comprehensive Viva Examination Q&A (55 Questions across 9 Categories)](#9-comprehensive-viva-examination-qa)
10. [Last-Minute Viva Quick Revision Sheet](#10-last-minute-viva-quick-revision-sheet)

---

# 1. Project Overview & Architectural Design

### 1.1 What is Staywise?
**Staywise** is a desktop-based boutique hotel management system built using **Python 3**, **Tkinter / ttk** for the graphical user interface (GUI), and **MySQL** for relational persistent storage. It manages room inventories, guest profiles, hotel bookings, front-desk check-in/check-out workflows, and executive occupancy metrics.

### 1.2 Architectural Pattern: 3-Tier Layered Architecture (UI / Business Logic / Database)
Staywise follows an industry-standard **Separation of Concerns (SoC)** architectural pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                       PRESENTATION TIER                     │
│  main.py (App Shell & Navigation)                           │
│  ui/theme.py (Styles, Palettes, Fonts)                      │
│  ui/components.py (Reusable StatCard, SidebarButton, etc.)  │
│  ui/*_view.py (Dashboard, Rooms, Guests, Reservations)      │
└──────────────────────────────┬──────────────────────────────┘
                               │ Calls logic functions
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      BUSINESS LOGIC TIER                    │
│  logic/room_logic.py (Validation, pricing, room status)     │
│  logic/guest_logic.py (Name/phone validation, referential)  │
│  logic/booking_logic.py (Date overlap conflict, lifecycle)  │
│  logic/dashboard_logic.py (KPI counts, today's schedule)    │
└──────────────────────────────┬──────────────────────────────┘
                               │ Requests DB connection & runs SQL
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        DATA ACCESS TIER                     │
│  database.py (get_connection, .env configuration)           │
│  MySQL Database: `staywise` (rooms, guests, reservations)   │
└─────────────────────────────────────────────────────────────┘
```

#### Why is the project split into `ui`, `logic`, and `database`?
1. **Maintainability & Clean Code**: If a business rule changes (for example, room numbers cannot exceed 10 characters or reservations must be minimum 1 night), you only edit `logic/`. You never touch the UI layout code.
2. **Crash Prevention & Separation of Concerns**: Database exceptions (`mysql.connector.Error`) are intercepted cleanly inside `logic/` and returned as `(False, "Error message")` tuples. The UI displays a friendly `messagebox.showerror` rather than terminating the Tkinter main event loop.
3. **Reusability**: Functions such as `get_selectable_guests()` and `get_selectable_rooms()` in `booking_logic.py` are reused across views without duplicating SQL queries.
4. **Security**: All SQL query logic and parameter binding (`%s`) reside in `logic/`, completely isolating the UI from raw query construction and preventing SQL injection.

---

# 2. File-by-File Codebase Explanation

### Summary Table of Project Files

| File Path | Role in System | Key Classes & Functions |
|---|---|---|
| `database.py` | Centralized database connection factory | `get_connection()` |
| `main.py` | Master window, sidebar, header, screen routing | `StaywiseApp`, `main()` |
| `ui/theme.py` | Design system, color palette, ttk styles | `setup_ttk_styles(root)`, color/font constants |
| `ui/components.py` | Reusable custom compound widgets | `StatCard`, `SidebarButton`, `ActionButton` |
| `ui/dashboard_view.py` | Executive KPI dashboard & today's schedule | `DashboardView`, `load_dashboard()` |
| `ui/rooms_view.py` | Room inventory screen & dialogs | `RoomsView`, `RoomFormDialog` |
| `ui/guests_view.py` | Guest directory screen & dialogs | `GuestsView`, `GuestFormDialog` |
| `ui/reservations_view.py`| Front-desk booking registry & dialogs | `ReservationsView`, `ReservationFormDialog` |
| `logic/room_logic.py` | Room validation, queries, and deletion safety | `get_all_rooms`, `add_room`, `update_room`, `delete_room`, `can_delete_room` |
| `logic/guest_logic.py` | Guest validation and referential checks | `get_all_guests`, `search_guests`, `add_guest`, `update_guest`, `delete_guest` |
| `logic/booking_logic.py` | Overlap algorithm, transactions, lifecycle | `validate_dates`, `check_date_overlap_conflict`, `create_reservation`, `check_in_reservation`, `check_out_reservation`, `cancel_reservation` |
| `logic/dashboard_logic.py`| SQL aggregations for KPIs and daily schedule | `get_dashboard_metrics()`, `get_todays_schedule()` |

---

### Detailed File Breakdown

#### 1. `database.py` (Lines 1–36)
- **Role**: Loads database credentials from `.env` using `python-dotenv` and yields an active MySQL connection via `mysql.connector.connect()`.
- **Key Function**: `get_connection()` (Lines 8–15) connects to `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME`.
- **Standalone execution**: Lines 17–36 provide a test routine when running `python database.py` directly, verifying table existence with `SHOW TABLES`.

#### 2. `main.py` (Lines 1–286)
- **Role**: Application entry point. Creates root `tk.Tk()`, sets title, geometry (`1200x740`), minimum size (`1040x660`), initializes TTK styling, constructs the two-column master layout (Sidebar on left, Header and Content Container on right), instantiates all 4 screen frames, and runs `root.mainloop()`.
- **Key Class**: `StaywiseApp` (Lines 30–276).
  - `_build_sidebar()` (Lines 58–144): Fixed 240px wide sidebar containing brand labels, 4 `SidebarButton` widgets, and a MySQL status indicator box.
  - `_build_header()` (Lines 145–197): Dynamic page title, subtitle, and today's date badge.
  - `_build_content_area()` (Lines 198–211): Container frame holding instances of `DashboardView`, `RoomsView`, `GuestsView`, and `ReservationsView`.
  - `_switch_screen(screen_key, title, subtitle)` (Lines 213–234): Common routing logic using `view.pack(fill="both", expand=True)` and `view.pack_forget()`.
  - Explicit navigation callbacks: `show_dashboard()`, `show_rooms()`, `show_guests()`, `show_reservations()` (Lines 237–276).

#### 3. `ui/theme.py` (Lines 1–125)
- **Role**: Defines the visual aesthetic (Boutique hotel palette: ivory `#F5F3EC`, pine forest `#263C35`, sage `#82916C`, terracotta `#B94A48`, amber `#C67D34`).
- **Typography**: Segoe UI font tuples (`FONT_TITLE_LARGE`, `FONT_BODY`, `FONT_BUTTON`, `FONT_CARD_VALUE`).
- **TTK Styling Function**: `setup_ttk_styles(root)` (Lines 45–125) customizes `Treeview`, `Treeview.Heading`, `TCombobox`, `Accent.TButton`, and `Secondary.TButton` using the `clam` theme engine.

#### 4. `ui/components.py` (Lines 1–175)
- **Role**: Custom reusable widgets constructed from native Tkinter primitives:
  - `StatCard(tk.Frame)` (Lines 16–75): Displays an accent color strip (`Frame`), title (`Label`), value (`Label`), and caption (`Label`). Contains `update_value(new_value, new_caption)`.
  - `SidebarButton(tk.Frame)` (Lines 77–148): Navigation item with an active indicator strip, icon label, text label, and hover/click event bindings (`<Button-1>`, `<Enter>`, `<Leave>`).
  - `ActionButton(tk.Button)` (Lines 150–175): Pre-styled flat button with automatic hover color transitions.

#### 5. `ui/dashboard_view.py` (Lines 1–263)
- **Role**: Executive dashboard screen.
- **Widgets**:
  - Row 1: 4 `StatCard` widgets (Total Rooms, Available, Occupied, Maintenance) arranged via `.grid()`.
  - Row 2: 3 `StatCard` widgets (Active Bookings, Today's Check-Ins, Today's Check-Outs) arranged via `.grid()`.
  - Table Container: Header frame with `Refresh Button`, status label, and a `ttk.Treeview` with vertical `ttk.Scrollbar` for today's arrival and departure schedule.
- **Data Hook**: `load_dashboard()` (Lines 192–263) queries `get_dashboard_metrics()` and `get_todays_schedule()`.

#### 6. `ui/rooms_view.py` (Lines 1–534)
- **Role**: Room inventory management screen and modal form.
- **Classes**:
  - `RoomFormDialog(tk.Toplevel)` (Lines 24–213): Modal dialog for adding or editing rooms. Contains `ttk.Entry` (number, price), `ttk.Combobox` (category, status), and Save/Cancel buttons.
  - `RoomsView(tk.Frame)` (Lines 215–534): Main screen containing search `ttk.Entry`, type filter `ttk.Combobox`, status filter `ttk.Combobox`, 4 toolbar action buttons, and a 5-column `ttk.Treeview` with vertical scrollbar.

#### 7. `ui/guests_view.py` (Lines 1–437)
- **Role**: Guest directory screen and modal form.
- **Classes**:
  - `GuestFormDialog(tk.Toplevel)` (Lines 21–171): Modal dialog for registering or editing a guest profile with `ttk.Entry` for full name and phone number.
  - `GuestsView(tk.Frame)` (Lines 173–437): Main screen with search entry (`<KeyRelease>` auto-search), toolbar buttons (Add, Edit, Delete, Refresh), and a 4-column `ttk.Treeview` showing guest IDs, names, contact numbers, and total booking counts.

#### 8. `ui/reservations_view.py` (Lines 1–755)
- **Role**: Front-desk operations screen and modal booking form.
- **Classes**:
  - `ReservationFormDialog(tk.Toplevel)` (Lines 27–347): Modal dialog for booking creation/update. Contains guest `Combobox`, room `Combobox`, check-in/out `Entry` fields in a 2-column `.grid()`, a dynamic live calculation preview card, and action buttons.
  - `ReservationsView(tk.Frame)` (Lines 349–755): Master registry screen with search entry, status filter `Combobox`, 6 toolbar buttons (New Reservation, Edit Dates, Check In, Check Out, Cancel Booking, Refresh), and an 8-column `ttk.Treeview`.

#### 9. `logic/room_logic.py` (Lines 1–321)
- **Role**: Room CRUD database access, field validation (`validate_room_data`), unique room number check (`is_room_number_taken`), and referential integrity check (`can_delete_room`).

#### 10. `logic/guest_logic.py` (Lines 1–265)
- **Role**: Guest CRUD database access, name & contact regex/character validation (`validate_guest_data`), SQL `LEFT JOIN` aggregations for reservation counts, and foreign key constraint safety checks (`can_delete_guest`).

#### 11. `logic/booking_logic.py` (Lines 1–636)
- **Role**: Reservation transactions. Validates date intervals (`validate_dates`), executes mathematical interval collision queries (`check_date_overlap_conflict`), performs atomic check-in/check-out/cancellation transactions with `FOR UPDATE` row locks, and synchronizes room status (`synchronize_room_status_after_change`).

#### 12. `logic/dashboard_logic.py` (Lines 1–155)
- **Role**: Aggregates hotel metrics via SQL `COUNT(CASE WHEN ... THEN 1 END)` queries in `get_dashboard_metrics()` and combines arrivals and departures using `UNION ALL` in `get_todays_schedule()`.

---

# 3. Complete Tkinter Widget Inventory

This table catalogues **EVERY** Tkinter and TTK widget instantiated in Staywise, with verified file names and exact line numbers.

| # | Widget Type | File | Line # | Parent Container | Purpose & Content | Layout Manager | Interaction & Callback |
|---|---|---|---|---|---|---|---|
| 1 | `tk.Tk` | `main.py` | 280 | Root window | Master desktop window (`1200x740`) | Window manager | Runs `root.mainloop()` (Line 282) |
| 2 | `tk.Frame` | `main.py` | 63 | `self.root` | Navigation sidebar container (width 240) | `.pack(side="left", fill="y")` | Static layout frame |
| 3 | `tk.Frame` | `main.py` | 68 | `self.sidebar` | Brand header container | `.pack(fill="x")` | Static layout frame |
| 4 | `tk.Label` | `main.py` | 71 | `brand_frame` | Displays brand name "STAYWISE" | `.pack(fill="x")` | Static text display |
| 5 | `tk.Label` | `main.py` | 81 | `brand_frame` | Displays subtitle "BOUTIQUE HOTEL OS" | `.pack(fill="x", pady=(2, 0))` | Static text display |
| 6 | `tk.Frame` | `main.py` | 92 | `self.sidebar` | Decorative horizontal separator (height 1) | `.pack(fill="x", padx=16, pady=(0, 16))` | Visual divider |
| 7 | `SidebarButton` (`Frame`) | `main.py` | 104 | `self.sidebar` | Dashboard navigation button | `.pack(fill="x", pady=2)` | Click calls `show_dashboard` (Line 237) |
| 8 | `SidebarButton` (`Frame`) | `main.py` | 104 | `self.sidebar` | Rooms navigation button | `.pack(fill="x", pady=2)` | Click calls `show_rooms` (Line 247) |
| 9 | `SidebarButton` (`Frame`) | `main.py` | 104 | `self.sidebar` | Guests navigation button | `.pack(fill="x", pady=2)` | Click calls `show_guests` (Line 257) |
| 10 | `SidebarButton` (`Frame`) | `main.py` | 104 | `self.sidebar` | Reservations navigation button | `.pack(fill="x", pady=2)` | Click calls `show_reservations` (Line 268) |
| 11 | `tk.Frame` | `main.py` | 114 | `self.sidebar` | Status container at bottom of sidebar | `.pack(side="bottom", fill="x")` | Static layout frame |
| 12 | `tk.Frame` | `main.py` | 117 | `status_frame` | Inner status box with border | `.pack(fill="x")` | Visual badge container |
| 13 | `tk.Label` | `main.py` | 127 | `status_box` | Green dot status indicator ("●") | `.pack(side="left", padx=(0, 6))` | Visual indicator |
| 14 | `tk.Label` | `main.py` | 136 | `status_box` | Database status: "MySQL: Connected (staywise)" | `.pack(side="left")` | System status text |
| 15 | `tk.Frame` | `main.py` | 150 | `self.root` | Top horizontal header bar | `.pack(side="top", fill="x")` | Master header frame |
| 16 | `tk.Frame` | `main.py` | 161 | `self.header` | Container for screen title & subtitle | `.pack(side="left", fill="both")` | Title container |
| 17 | `tk.Label` | `main.py` | 164 | `title_container` | Dynamic screen title (`self.lbl_page_title`) | `.pack(anchor="w")` | Text updated on screen switch |
| 18 | `tk.Label` | `main.py` | 174 | `title_container` | Dynamic screen description (`self.lbl_page_subtitle`) | `.pack(anchor="w", pady=(2, 0))` | Text updated on screen switch |
| 19 | `tk.Frame` | `main.py` | 185 | `self.header` | Context container on right of header | `.pack(side="right", fill="y")` | Date container |
| 20 | `tk.Label` | `main.py` | 189 | `right_container` | Today's formatted calendar date (`📅 ...`) | `.pack(side="right", expand=True)` | Live date display |
| 21 | `tk.Frame` | `main.py` | 202 | `self.root` | Content area container where views swap | `.pack(side="top", fill="both", expand=True)` | View swapping container |
| 22 | `DashboardView` (`Frame`) | `main.py` | 207 | `content_container` | Master executive dashboard view | `.pack(fill="both", expand=True)` | Managed by `_switch_screen` |
| 23 | `RoomsView` (`Frame`) | `main.py` | 208 | `content_container` | Master rooms management view | `.pack_forget()` / `.pack(...)` | Managed by `_switch_screen` |
| 24 | `GuestsView` (`Frame`) | `main.py` | 209 | `content_container` | Master guests management view | `.pack_forget()` / `.pack(...)` | Managed by `_switch_screen` |
| 25 | `ReservationsView` (`Frame`) | `main.py` | 210 | `content_container` | Master reservations management view | `.pack_forget()` / `.pack(...)` | Managed by `_switch_screen` |
| 26 | `tk.Frame` | `ui/components.py` | 22 | `parent` (arbitrary) | `StatCard` outer card container | Managed by parent (`.grid`) | Reusable KPI card |
| 27 | `tk.Frame` | `ui/components.py` | 34 | `StatCard` | Colored top accent strip (height 3) | `.pack(fill="x", side="top", pady=(0, 10))` | Visual decoration |
| 28 | `tk.Label` | `ui/components.py` | 38 | `StatCard` | Metric title label (`lbl_title`) | `.pack(fill="x", anchor="w")` | Uppercase metric title |
| 29 | `tk.Label` | `ui/components.py` | 49 | `StatCard` | Metric number label (`lbl_value`) | `.pack(fill="x", anchor="w", pady=(2, 4))` | Large bold value display |
| 30 | `tk.Label` | `ui/components.py` | 60 | `StatCard` | Metric context caption (`lbl_caption`) | `.pack(fill="x", anchor="w")` | Subtitle caption |
| 31 | `tk.Frame` | `ui/components.py` | 83 | `parent` (`self.sidebar`) | `SidebarButton` container | `.pack(fill="x", pady=2)` | Bound to click & hover |
| 32 | `tk.Frame` | `ui/components.py` | 88 | `SidebarButton` | Left active indicator pill (width 4) | `.pack(side="left", fill="y")` | Changes color when active |
| 33 | `tk.Label` | `ui/components.py` | 92 | `SidebarButton` | Unicode icon symbol (`lbl_icon`) | `.pack(side="left", padx=(10, 4), pady=10)` | Button icon |
| 34 | `tk.Label` | `ui/components.py` | 103 | `SidebarButton` | Button text label (`lbl_text`) | `.pack(side="left", fill="x", expand=True, pady=10)` | Button text |
| 35 | `tk.Button` | `ui/components.py` | 156 | `parent` (arbitrary) | `ActionButton` primary button | Managed by caller | Bound to hover events |
| 36 | `tk.Frame` | `ui/dashboard_view.py` | 33 | `DashboardView` | Main content container | `.pack(fill="both", expand=True)` | Margin container |
| 37 | `tk.Frame` | `ui/dashboard_view.py` | 37 | `container` | Row 1 cards grid container | `.pack(fill="x", pady=(0, 14))` | 4-column grid container |
| 38 | `StatCard` | `ui/dashboard_view.py` | 43 | `cards_row1` | "Total Rooms" KPI card | `.grid(row=0, column=0, padx=(0, 10), sticky="nsew")` | Shows total rooms count |
| 39 | `StatCard` | `ui/dashboard_view.py` | 52 | `cards_row1` | "Available Rooms" KPI card | `.grid(row=0, column=1, padx=(0, 10), sticky="nsew")` | Shows available rooms count |
| 40 | `StatCard` | `ui/dashboard_view.py` | 61 | `cards_row1` | "Occupied Rooms" KPI card | `.grid(row=0, column=2, padx=(0, 10), sticky="nsew")` | Shows occupied rooms count |
| 41 | `StatCard` | `ui/dashboard_view.py` | 70 | `cards_row1` | "Under Maintenance" KPI card | `.grid(row=0, column=3, padx=(0, 0), sticky="nsew")` | Shows maintenance count |
| 42 | `tk.Frame` | `ui/dashboard_view.py` | 80 | `container` | Row 2 cards grid container | `.pack(fill="x", pady=(0, 20))` | 3-column grid container |
| 43 | `StatCard` | `ui/dashboard_view.py` | 86 | `cards_row2` | "Active Bookings" KPI card | `.grid(row=0, column=0, padx=(0, 10), sticky="nsew")` | Shows active bookings count |
| 44 | `StatCard` | `ui/dashboard_view.py` | 95 | `cards_row2` | "Today's Check-Ins" KPI card | `.grid(row=0, column=1, padx=(0, 10), sticky="nsew")` | Shows today's arrivals count |
| 45 | `StatCard` | `ui/dashboard_view.py` | 104 | `cards_row2` | "Today's Check-Outs" KPI card | `.grid(row=0, column=2, padx=(0, 0), sticky="nsew")` | Shows today's departures count |
| 46 | `tk.Frame` | `ui/dashboard_view.py` | 114 | `container` | Schedule card container | `.pack(fill="both", expand=True)` | Bordered card frame |
| 47 | `tk.Frame` | `ui/dashboard_view.py` | 124 | `table_container` | Schedule header row | `.pack(fill="x", pady=(0, 12))` | Table title & action bar |
| 48 | `tk.Label` | `ui/dashboard_view.py` | 127 | `header_row` | Section title: "Today's Arrival & Departure Schedule" | `.pack(side="left")` | Static section heading |
| 49 | `tk.Button` | `ui/dashboard_view.py` | 137 | `header_row` | "⟳ Refresh Dashboard" button | `.pack(side="right", padx=(8, 0))` | `command=self.load_dashboard` |
| 50 | `tk.Label` | `ui/dashboard_view.py` | 153 | `header_row` | Live sync status label (`self.lbl_status`) | `.pack(side="right")` | Displays sync timestamp |
| 51 | `ttk.Treeview` | `ui/dashboard_view.py` | 164 | `table_container` | Today's schedule 6-column table | `.pack(side="left", fill="both", expand=True)` | Displays arrivals/departures |
| 52 | `ttk.Scrollbar`| `ui/dashboard_view.py` | 184 | `table_container` | Vertical scrollbar for schedule table | `.pack(side="right", fill="y")` | `command=self.tree.yview` |
| 53 | `tk.Toplevel` | `ui/rooms_view.py` | 30 | `parent` (`RoomsView`) | `RoomFormDialog` modal popup window | Window manager modal | `self.grab_set()` |
| 54 | `tk.Frame` | `ui/rooms_view.py` | 56 | `RoomFormDialog` | Modal dialog header container | `.pack(fill="x")` | Header frame |
| 55 | `tk.Label` | `ui/rooms_view.py` | 59 | `header` | Dialog title (Add / Edit Room) | `.pack(anchor="w")` | Modal title text |
| 56 | `tk.Label` | `ui/rooms_view.py` | 68 | `header` | Dialog subtitle description | `.pack(anchor="w", pady=(2, 0))` | Description text |
| 57 | `tk.Frame` | `ui/rooms_view.py` | 78 | `RoomFormDialog` | Input fields container | `.pack(fill="both", expand=True)` | Form body frame |
| 58 | `tk.Label` | `ui/rooms_view.py` | 82 | `form_frame` | Label: "Room Number *" | `.pack(anchor="w", pady=(0, 4))` | Field label |
| 59 | `ttk.Entry` | `ui/rooms_view.py` | 91 | `form_frame` | Text entry for room number (`ent_number`) | `.pack(fill="x", pady=(0, 14))` | Keyboard typing input |
| 60 | `tk.Label` | `ui/rooms_view.py` | 97 | `form_frame` | Label: "Room Category / Type *" | `.pack(anchor="w", pady=(0, 4))` | Field label |
| 61 | `ttk.Combobox` | `ui/rooms_view.py` | 106 | `form_frame` | Category dropdown (`Single`, `Double`, etc.) | `.pack(fill="x", pady=(0, 14))` | Dropdown selection |
| 62 | `tk.Label` | `ui/rooms_view.py` | 120 | `form_frame` | Label: "Price per Night (₹) *" | `.pack(anchor="w", pady=(0, 4))` | Field label |
| 63 | `ttk.Entry` | `ui/rooms_view.py` | 129 | `form_frame` | Text entry for nightly price (`ent_price`) | `.pack(fill="x", pady=(0, 14))` | Keyboard typing input |
| 64 | `tk.Label` | `ui/rooms_view.py` | 135 | `form_frame` | Label: "Operational Status *" | `.pack(anchor="w", pady=(0, 4))` | Field label |
| 65 | `ttk.Combobox` | `ui/rooms_view.py` | 144 | `form_frame` | Status dropdown (`Available`, `Occupied`, etc.)| `.pack(fill="x", pady=(0, 18))` | Dropdown selection |
| 66 | `tk.Frame` | `ui/rooms_view.py` | 158 | `RoomFormDialog` | Bottom action button bar | `.pack(fill="x", side="bottom")` | Button bar frame |
| 67 | `tk.Button` | `ui/rooms_view.py` | 161 | `btn_bar` | "Cancel" button | `.pack(side="right", padx=(8, 0))` | `command=self.destroy` |
| 68 | `ActionButton` | `ui/rooms_view.py` | 177 | `btn_bar` | "Save Room" / "Update Room" button | `.pack(side="right")` | `command=self._on_save` (Line 187) |
| 69 | `tk.Frame` | `ui/rooms_view.py` | 227 | `RoomsView` | Rooms main content container | `.pack(fill="both", expand=True)` | Content margin frame |
| 70 | `tk.Frame` | `ui/rooms_view.py` | 231 | `container` | Filter & action toolbar | `.pack(fill="x", pady=(0, 16))` | Filter toolbar frame |
| 71 | `tk.Label` | `ui/rooms_view.py` | 242 | `toolbar` | Label: "Search Room #:" | `.pack(side="left", padx=(0, 8))` | Search field label |
| 72 | `ttk.Entry` | `ui/rooms_view.py` | 251 | `toolbar` | Search box (`ent_search`) | `.pack(side="left", padx=(0, 16))` | Bound to `<KeyRelease>` (Line 253) |
| 73 | `tk.Label` | `ui/rooms_view.py` | 256 | `toolbar` | Label: "Type:" | `.pack(side="left", padx=(0, 8))` | Dropdown filter label |
| 74 | `ttk.Combobox` | `ui/rooms_view.py` | 265 | `toolbar` | Filter by room category (`cmb_type`) | `.pack(side="left", padx=(0, 16))` | Bound to `<<ComboboxSelected>>` (Line 273) |
| 75 | `tk.Label` | `ui/rooms_view.py` | 276 | `toolbar` | Label: "Status:" | `.pack(side="left", padx=(0, 8))` | Dropdown filter label |
| 76 | `ttk.Combobox` | `ui/rooms_view.py` | 285 | `toolbar` | Filter by operational status (`cmb_status`) | `.pack(side="left", padx=(0, 16))` | Bound to `<<ComboboxSelected>>` (Line 293) |
| 77 | `ActionButton` | `ui/rooms_view.py` | 296 | `toolbar` | "+ Add Room" button | `.pack(side="right", padx=(6, 0))` | `command=self.open_add_room_dialog` (Line 474) |
| 78 | `tk.Button` | `ui/rooms_view.py` | 303 | `toolbar` | "Edit Room" button | `.pack(side="right", padx=(6, 0))` | `command=self.open_edit_room_dialog` (Line 482) |
| 79 | `tk.Button` | `ui/rooms_view.py` | 319 | `toolbar` | "Delete Room" button | `.pack(side="right", padx=(6, 0))` | `command=self.confirm_delete_room` (Line 500) |
| 80 | `tk.Button` | `ui/rooms_view.py` | 335 | `toolbar` | "⟳ Refresh" button | `.pack(side="right", padx=(6, 0))` | `command=self.load_rooms` (Line 414) |
| 81 | `tk.Frame` | `ui/rooms_view.py` | 352 | `container` | Rooms table card container | `.pack(fill="both", expand=True)` | Card container frame |
| 82 | `tk.Frame` | `ui/rooms_view.py` | 362 | `table_container` | Table header frame | `.pack(fill="x", pady=(0, 10))` | Header frame |
| 83 | `tk.Label` | `ui/rooms_view.py` | 365 | `header_frame` | Table title: "Hotel Room Directory" | `.pack(side="left")` | Section title |
| 84 | `tk.Label` | `ui/rooms_view.py` | 374 | `header_frame` | Rooms count status label (`lbl_count`) | `.pack(side="right")` | Dynamic count text |
| 85 | `ttk.Treeview` | `ui/rooms_view.py` | 384 | `table_container` | 5-column rooms table (`self.tree`) | `.pack(side="left", fill="both", expand=True)` | Bound to `<Double-1>` (Line 404) |
| 86 | `ttk.Scrollbar`| `ui/rooms_view.py` | 406 | `table_container` | Vertical scrollbar for rooms table | `.pack(side="right", fill="y")` | `command=self.tree.yview` |
| 87 | `tk.Toplevel` | `ui/guests_view.py`| 27 | `parent` (`GuestsView`)| `GuestFormDialog` modal popup window | Window manager modal | `self.grab_set()` |
| 88 | `tk.Frame` | `ui/guests_view.py`| 53 | `GuestFormDialog` | Modal dialog header container | `.pack(fill="x")` | Header frame |
| 89 | `tk.Label` | `ui/guests_view.py`| 56 | `header` | Dialog title (Register / Edit Guest) | `.pack(anchor="w")` | Title text |
| 90 | `tk.Label` | `ui/guests_view.py`| 65 | `header` | Dialog subtitle description | `.pack(anchor="w", pady=(2, 0))` | Subtitle text |
| 91 | `tk.Frame` | `ui/guests_view.py`| 75 | `GuestFormDialog` | Input fields container | `.pack(fill="both", expand=True)` | Form frame |
| 92 | `tk.Label` | `ui/guests_view.py`| 79 | `form_frame` | Label: "Guest Full Name *" | `.pack(anchor="w", pady=(0, 4))` | Field label |
| 93 | `ttk.Entry` | `ui/guests_view.py`| 88 | `form_frame` | Text entry for guest name (`ent_name`) | `.pack(fill="x", pady=(0, 16))` | Keyboard typing input |
| 94 | `tk.Label` | `ui/guests_view.py`| 94 | `form_frame` | Label: "Contact Number / Phone *" | `.pack(anchor="w", pady=(0, 4))` | Field label |
| 95 | `ttk.Entry` | `ui/guests_view.py`| 103 | `form_frame` | Text entry for phone (`ent_contact`) | `.pack(fill="x", pady=(0, 6))` | Keyboard typing input |
| 96 | `tk.Label` | `ui/guests_view.py`| 108 | `form_frame` | Hint label for phone format | `.pack(anchor="w", pady=(0, 10))` | Guidance hint text |
| 97 | `tk.Frame` | `ui/guests_view.py`| 118 | `GuestFormDialog` | Bottom action button bar | `.pack(fill="x", side="bottom")` | Button bar frame |
| 98 | `tk.Button` | `ui/guests_view.py`| 121 | `btn_bar` | "Cancel" button | `.pack(side="right", padx=(8, 0))` | `command=self.destroy` |
| 99 | `ActionButton` | `ui/guests_view.py`| 137 | `btn_bar` | "Save Guest" / "Update Guest" button | `.pack(side="right")` | `command=self._on_save` (Line 147) |
| 100| `tk.Frame` | `ui/guests_view.py`| 185 | `GuestsView` | Guests main content container | `.pack(fill="both", expand=True)` | Content margin frame |
| 101| `tk.Frame` | `ui/guests_view.py`| 189 | `container` | Toolbar container | `.pack(fill="x", pady=(0, 16))` | Toolbar frame |
| 102| `tk.Label` | `ui/guests_view.py`| 199 | `toolbar` | Label: "Search Guest:" | `.pack(side="left", padx=(0, 8))` | Search field label |
| 103| `ttk.Entry` | `ui/guests_view.py`| 208 | `toolbar` | Search box (`ent_search`) | `.pack(side="left", padx=(0, 16))` | Bound to `<KeyRelease>` (Line 210) |
| 104| `ActionButton` | `ui/guests_view.py`| 213 | `toolbar` | "+ Add Guest" button | `.pack(side="right", padx=(6, 0))` | `command=self.open_add_guest_dialog` (Line 380) |
| 105| `tk.Button` | `ui/guests_view.py`| 220 | `toolbar` | "Edit Guest" button | `.pack(side="right", padx=(6, 0))` | `command=self.open_edit_guest_dialog` (Line 388) |
| 106| `tk.Button` | `ui/guests_view.py`| 237 | `toolbar` | "Delete Guest" button | `.pack(side="right", padx=(6, 0))` | `command=self.confirm_delete_guest` (Line 406) |
| 107| `tk.Button` | `ui/guests_view.py`| 252 | `toolbar` | "⟳ Refresh" button | `.pack(side="right", padx=(6, 0))` | `command=self.load_guests` (Line 324) |
| 108| `tk.Frame` | `ui/guests_view.py`| 269 | `container` | Guests table card container | `.pack(fill="both", expand=True)` | Card container frame |
| 109| `tk.Frame` | `ui/guests_view.py`| 279 | `table_container` | Header frame | `.pack(fill="x", pady=(0, 10))` | Header frame |
| 110| `tk.Label` | `ui/guests_view.py`| 282 | `header_frame` | Table title: "Registered Guests Directory" | `.pack(side="left")` | Title label |
| 111| `tk.Label` | `ui/guests_view.py`| 291 | `header_frame` | Guests count status label (`lbl_count`) | `.pack(side="right")` | Dynamic count text |
| 112| `ttk.Treeview` | `ui/guests_view.py`| 301 | `table_container` | 4-column guests table (`self.tree`) | `.pack(side="left", fill="both", expand=True)` | Bound to `<Double-1>` (Line 314) |
| 113| `ttk.Scrollbar`| `ui/guests_view.py`| 316 | `table_container` | Vertical scrollbar for guests table | `.pack(side="right", fill="y")` | `command=self.tree.yview` |
| 114| `tk.Toplevel` | `ui/reservations_view.py`| 33 | `parent` (`ReservationsView`)| `ReservationFormDialog` modal popup | Window manager modal | `self.grab_set()` |
| 115| `tk.Frame` | `ui/reservations_view.py`| 62 | `ReservationFormDialog` | Modal dialog header container | `.pack(fill="x")` | Header frame |
| 116| `tk.Label` | `ui/reservations_view.py`| 65 | `header` | Dialog title (New / Edit Booking) | `.pack(anchor="w")` | Title text |
| 117| `tk.Label` | `ui/reservations_view.py`| 74 | `header` | Dialog subtitle description | `.pack(anchor="w", pady=(2, 0))` | Subtitle text |
| 118| `tk.Frame` | `ui/reservations_view.py`| 84 | `ReservationFormDialog` | Input fields container | `.pack(fill="both", expand=True)` | Form body frame |
| 119| `tk.Label` | `ui/reservations_view.py`| 88 | `form_frame` | Label: "Guest Profile *" | `.pack(anchor="w", pady=(0, 4))` | Field label |
| 120| `ttk.Combobox` | `ui/reservations_view.py`| 98 | `form_frame` | Guest dropdown list (`cmb_guest`) | `.pack(fill="x", pady=(0, 14))` | Selection dropdown |
| 121| `tk.Label` | `ui/reservations_view.py`| 120 | `form_frame` | Label: "Assigned Room *" | `.pack(anchor="w", pady=(0, 4))` | Field label |
| 122| `ttk.Combobox` | `ui/reservations_view.py`| 130 | `form_frame` | Room dropdown list (`cmb_room`) | `.pack(fill="x", pady=(0, 14))` | Bound to `<<ComboboxSelected>>` (Line 228) |
| 123| `tk.Label` | `ui/reservations_view.py`| 151 | `form_frame` | Room locked warning (if Checked In) | `.pack(anchor="w", pady=(0, 10))` | Lock message (conditional) |
| 124| `tk.Frame` | `ui/reservations_view.py`| 163 | `form_frame` | 2-column dates grid container | `.pack(fill="x", pady=(0, 14))` | Contains date grid |
| 125| `tk.Label` | `ui/reservations_view.py`| 169 | `dates_frame` | Label: "Check-In Date (YYYY-MM-DD) *" | `.grid(row=0, column=0, sticky="w", pady=(0, 4), padx=(0, 8))` | Field label |
| 126| `ttk.Entry` | `ui/reservations_view.py`| 178 | `dates_frame` | Check-in date entry (`ent_cin`) | `.grid(row=1, column=0, sticky="ew", padx=(0, 8))` | Bound to `<KeyRelease>` (Line 229) |
| 127| `tk.Label` | `ui/reservations_view.py`| 182 | `dates_frame` | Label: "Check-Out Date (YYYY-MM-DD) *"| `.grid(row=0, column=1, sticky="w", pady=(0, 4), padx=(8, 0))` | Field label |
| 128| `ttk.Entry` | `ui/reservations_view.py`| 191 | `dates_frame` | Check-out date entry (`ent_cout`) | `.grid(row=1, column=1, sticky="ew", padx=(8, 0))` | Bound to `<KeyRelease>` (Line 230) |
| 129| `tk.Frame` | `ui/reservations_view.py`| 206 | `form_frame` | Live calculation preview card | `.pack(fill="x", pady=(0, 10))` | Preview card frame |
| 130| `tk.Label` | `ui/reservations_view.py`| 216 | `calc_box` | Live price calculation text (`lbl_calc_info`)| `.pack(anchor="w")` | Real-time calculation |
| 131| `tk.Frame` | `ui/reservations_view.py`| 234 | `ReservationFormDialog` | Bottom action button bar | `.pack(fill="x", side="bottom")` | Button bar frame |
| 132| `tk.Button` | `ui/reservations_view.py`| 237 | `btn_bar` | "Cancel" button | `.pack(side="right", padx=(8, 0))` | `command=self.destroy` |
| 133| `ActionButton` | `ui/reservations_view.py`| 253 | `btn_bar` | "Confirm Reservation" button | `.pack(side="right")` | `command=self._on_save` (Line 309) |
| 134| `tk.Frame` | `ui/reservations_view.py`| 361 | `ReservationsView`| Reservations main content container | `.pack(fill="both", expand=True)` | Content margin frame |
| 135| `tk.Frame` | `ui/reservations_view.py`| 365 | `container` | Filter & action toolbar | `.pack(fill="x", pady=(0, 16))` | Toolbar frame |
| 136| `tk.Label` | `ui/reservations_view.py`| 375 | `toolbar` | Label: "Search Booking:" | `.pack(side="left", padx=(0, 8))` | Search field label |
| 137| `ttk.Entry` | `ui/reservations_view.py`| 384 | `toolbar` | Search box (`ent_search`) | `.pack(side="left", padx=(0, 16))` | Bound to `<KeyRelease>` (Line 386) |
| 138| `tk.Label` | `ui/reservations_view.py`| 388 | `toolbar` | Label: "Filter Status:" | `.pack(side="left", padx=(0, 8))` | Status filter label |
| 139| `ttk.Combobox` | `ui/reservations_view.py`| 397 | `toolbar` | Status filter dropdown (`cmb_status`) | `.pack(side="left", padx=(0, 16))` | Bound to `<<ComboboxSelected>>` (Line 405) |
| 140| `ActionButton` | `ui/reservations_view.py`| 408 | `toolbar` | "+ New Reservation" button | `.pack(side="right", padx=(6, 0))` | `command=self.open_add_reservation_dialog` (Line 637) |
| 141| `tk.Button` | `ui/reservations_view.py`| 415 | `toolbar` | "Edit Dates" button | `.pack(side="right", padx=(6, 0))` | `command=self.open_edit_reservation_dialog` (Line 645) |
| 142| `tk.Button` | `ui/reservations_view.py`| 431 | `toolbar` | "Check In" button | `.pack(side="right", padx=(6, 0))` | `command=self.handle_check_in` (Line 672) |
| 143| `tk.Button` | `ui/reservations_view.py`| 447 | `toolbar` | "Check Out" button | `.pack(side="right", padx=(6, 0))` | `command=self.handle_check_out` (Line 701) |
| 144| `tk.Button` | `ui/reservations_view.py`| 463 | `toolbar` | "Cancel Booking" button | `.pack(side="right", padx=(6, 0))` | `command=self.handle_cancel_booking` (Line 729) |
| 145| `tk.Button` | `ui/reservations_view.py`| 479 | `toolbar` | "⟳ Refresh" button | `.pack(side="right", padx=(6, 0))` | `command=self.load_reservations` (Line 565) |
| 146| `tk.Frame` | `ui/reservations_view.py`| 496 | `container` | Reservations table card container | `.pack(fill="both", expand=True)` | Card container frame |
| 147| `tk.Frame` | `ui/reservations_view.py`| 506 | `table_container` | Header frame | `.pack(fill="x", pady=(0, 10))` | Header frame |
| 148| `tk.Label` | `ui/reservations_view.py`| 509 | `header_frame` | Table title: "Master Reservations Registry" | `.pack(side="left")` | Title label |
| 149| `tk.Label` | `ui/reservations_view.py`| 518 | `header_frame` | Count status label (`lbl_count`) | `.pack(side="right")` | Dynamic count text |
| 150| `ttk.Treeview` | `ui/reservations_view.py`| 528 | `table_container` | 8-column reservations table (`self.tree`)| `.pack(side="left", fill="both", expand=True)` | Bound to `<Double-1>` (Line 555) |
| 151| `ttk.Scrollbar`| `ui/reservations_view.py`| 557 | `table_container` | Vertical scrollbar for table | `.pack(side="right", fill="y")` | `command=self.tree.yview` |

### Widgets NOT Used in Staywise (Important Viva Clarification)
If asked in viva whether your project uses `Text`, `Canvas`, `Checkbutton`, `Radiobutton`, `LabelFrame`, `Menu`, or `Message`:
- **Answer**: *"No, our project deliberately does not use them. We use `ttk.Entry` for all text inputs, `ttk.Combobox` instead of Radiobuttons/Checkbuttons for clean single-select choices, `tk.Frame` with custom borders instead of `LabelFrame` to follow modern flat boutique styling, and explicit `SidebarButton` widgets instead of a top `Menu` bar."*

---

# 4. Layout Managers Code Map

Tkinter provides three geometry managers: `.pack()`, `.grid()`, and `.place()`. In Staywise, **`.pack()`** is used for hierarchical document flow (toolbars, headers, tables), **`.grid()`** is used for tabular multi-column cards and side-by-side inputs, and **`.place()`** is deliberately avoided because absolute pixel coordinates break when windows are resized.

### Key Layout Parameters Explained

| Parameter | Used In | Exact Purpose in Staywise |
|---|---|---|
| `side="left" / "right" / "top" / "bottom"` | `.pack()` | Controls which edge of the parent container the widget attaches to. E.g., `self.sidebar.pack(side="left")` docks the sidebar to the left edge of the master window. |
| `fill="x" / "y" / "both" / "none"` | `.pack()` | Dictates whether the widget stretches to occupy extra allocation space horizontally (`x`), vertically (`y`), or both (`both`). E.g., `header.pack(side="top", fill="x")` stretches full width. |
| `expand=True / False` | `.pack()` | Allocates any leftover parent space to this child. E.g., `content_container.pack(fill="both", expand=True)` ensures the active screen expands when the user maximizes the window. |
| `padx` / `pady` | `.pack()` & `.grid()` | External spacing around the widget. Can be an integer or a 2-tuple `(left, right)` / `(top, bottom)`. E.g., `pady=(2, 0)` adds 2px above and 0px below. |
| `row` / `column` | `.grid()` | 0-indexed grid cell coordinates. E.g., `card_available.grid(row=0, column=1)`. |
| `sticky="nsew" / "w" / "ew"` | `.grid()` | Directional alignment inside the grid cell (North, South, East, West). `sticky="nsew"` forces the widget to stretch and fill the entire cell. |

---

### Code Examples from Staywise

#### Example 1: Draining and expanding main content (`main.py`, Lines 63–65, 202–203)
```python
# Fixed width left sidebar (Line 63)
self.sidebar = tk.Frame(self.root, bg=COLOR_SIDEBAR, width=240)
self.sidebar.pack(side="left", fill="y")
self.sidebar.pack_propagate(False)  # Prevents sidebar from shrinking to fit child widgets

# Flexible main content container (Line 202)
self.content_container = tk.Frame(self.root, bg=COLOR_BG)
self.content_container.pack(side="top", fill="both", expand=True)
```
- **Why?** `side="left"` docks the sidebar on the left. `pack_propagate(False)` locks the width at 240 pixels. `expand=True` ensures the remaining screen area expands to fill the entire monitor.

#### Example 2: Uniform multi-column KPI cards (`ui/dashboard_view.py`, Lines 40–51)
```python
cards_row1 = tk.Frame(container, bg=COLOR_BG)
cards_row1.pack(fill="x", pady=(0, 14))

# Configure 4 equal-width responsive columns
for col in range(4):
    cards_row1.columnconfigure(col, weight=1, uniform="row1_cards")

self.card_total.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
self.card_available.grid(row=0, column=1, padx=(0, 10), sticky="nsew")
```
- **Why?** `columnconfigure(..., weight=1, uniform="...")` guarantees all 4 cards share exactly 25% of the horizontal space. `sticky="nsew"` forces the cards to expand in all four cardinal directions.

#### Example 3: Side-by-side date fields in form dialog (`ui/reservations_view.py`, Lines 163–193)
```python
dates_frame = tk.Frame(form_frame, bg=COLOR_CARD_BG)
dates_frame.pack(fill="x", pady=(0, 14))
dates_frame.columnconfigure(0, weight=1)
dates_frame.columnconfigure(1, weight=1)

lbl_cin.grid(row=0, column=0, sticky="w", pady=(0, 4), padx=(0, 8))
self.ent_cin.grid(row=1, column=0, sticky="ew", padx=(0, 8))

lbl_cout.grid(row=0, column=1, sticky="w", pady=(0, 4), padx=(8, 0))
self.ent_cout.grid(row=1, column=1, sticky="ew", padx=(8, 0))
```
- **Why?** The date labels sit directly above their respective input boxes in columns 0 and 1, ensuring alignment without manual pixel offsets.

---

# 5. Events, Bindings, and Callbacks Code Map

Tkinter is an **event-driven GUI**. Every user interaction (button click, typing, dropdown selection) triggers an event that invokes a Python function known as a **callback**.

### Summary of Events in Staywise

| Event Type | Tkinter Syntax | Used In | Callback Function | Exact Line | Purpose |
|---|---|---|---|---|---|
| Button Click | `command=cmd` | `main.py` | `show_dashboard` | Line 108 | Swaps content area to Dashboard view |
| Button Click | `command=cmd` | `main.py` | `show_rooms` | Line 108 | Swaps content area to Rooms view |
| Button Click | `command=cmd` | `main.py` | `show_guests` | Line 108 | Swaps content area to Guests view |
| Button Click | `command=cmd` | `main.py` | `show_reservations`| Line 108 | Swaps content area to Reservations view|
| Mouse Click | `.bind("<Button-1>")` | `ui/components.py` | `_on_click` | Line 115 | Handles sidebar navigation button clicks|
| Hover Enter | `.bind("<Enter>")` | `ui/components.py` | `_on_enter` / lambda | Line 116, 174| Changes background color on hover |
| Hover Leave | `.bind("<Leave>")` | `ui/components.py` | `_on_leave` / lambda | Line 117, 175| Restores default background color |
| Key Typing | `.bind("<KeyRelease>")`| `ui/rooms_view.py` | `_on_filter_changed`| Line 253 | Live search rooms as user types |
| Key Typing | `.bind("<KeyRelease>")`| `ui/guests_view.py` | `_on_search_changed`| Line 210 | Live search guests as user types |
| Key Typing | `.bind("<KeyRelease>")`| `ui/reservations_view.py`| `_on_filter_changed`| Line 386 | Live search bookings as user types |
| Key Typing | `.bind("<KeyRelease>")`| `ui/reservations_view.py`| `_update_calc_preview`| Lines 229, 230| Live price calculation preview |
| Dropdown Select | `.bind("<<ComboboxSelected>>")`| `ui/rooms_view.py`| `_on_filter_changed`| Lines 273, 293| Filter rooms by Type or Status |
| Dropdown Select | `.bind("<<ComboboxSelected>>")`| `ui/reservations_view.py`| `_on_filter_changed`| Line 405 | Filter bookings by status |
| Dropdown Select | `.bind("<<ComboboxSelected>>")`| `ui/reservations_view.py`| `_update_calc_preview`| Line 228 | Updates estimated booking total |
| Double Click | `.bind("<Double-1>")`| `ui/rooms_view.py` | lambda -> `open_edit_room_dialog`| Line 404 | Double clicking table row opens Edit dialog|
| Double Click | `.bind("<Double-1>")`| `ui/guests_view.py` | lambda -> `open_edit_guest_dialog`| Line 314 | Double clicking table row opens Edit dialog|
| Double Click | `.bind("<Double-1>")`| `ui/reservations_view.py`| lambda -> `open_edit_reservation_dialog`| Line 555 | Double clicking row opens Edit dialog |

---

### Detailed Callback Traces

#### Trace 1: Adding a Room
- **Trigger**: User clicks `+ Add Room` button in `ui/rooms_view.py` (Line 296).
- **Callback**: `self.open_add_room_dialog` (Lines 474–480).
- **Dialog Created**: `RoomFormDialog(self, mode="add", on_success_callback=self.load_rooms)` (Lines 24–53).
- **Save Click**: User clicks `Save Room` (Line 177), invoking `self._on_save` (Lines 187–213).
- **Execution**:
  1. `_on_save` extracts inputs: `room_num = self.ent_number.get().strip()`, `cmb_type.get()`, `ent_price.get()`, `cmb_status.get()`.
  2. Calls `logic/room_logic.py:add_room(...)` (Line 195).
  3. `add_room` calls `validate_room_data` (Line 124) which verifies non-empty, length $\le 10$, unique room number in MySQL (`is_room_number_taken`), valid enum type, positive price, and valid status.
  4. If valid, opens `conn = get_connection()`, prepares `INSERT INTO rooms ... VALUES (%s, %s, %s, %s)`, executes with tuple params, calls `conn.commit()`, and returns `(True, "Room added successfully!", new_id)`.
  5. UI displays `messagebox.showinfo("Success", ...)` (Line 197), triggers `on_success_callback()` which is `self.load_rooms()` (Line 414), and closes dialog with `self.destroy()`.
  6. `load_rooms()` queries MySQL and redraws the Treeview table with the new room.

#### Trace 2: Live Search as User Types
- **Trigger**: User types a character into `ent_search` on the Guests screen (`ui/guests_view.py`, Line 208).
- **Event Binding**: `self.ent_search.bind("<KeyRelease>", self._on_search_changed)` (Line 210).
- **Callback**: `_on_search_changed` (Lines 360–362) calls `self.load_guests()` (Line 324).
- **Execution**:
  1. `load_guests()` reads `search_txt = self.ent_search.get().strip()`.
  2. Calls `logic/guest_logic.py:search_guests(query)` (Line 52).
  3. `search_guests` creates SQL pattern `f"%{clean_query}%"` and runs parameterized SQL:
     ```sql
     SELECT g.guest_id, g.full_name, g.contact_number, COUNT(r.reservation_id) AS booking_count
     FROM guests g
     LEFT JOIN reservations r ON g.guest_id = r.guest_id
     WHERE g.full_name LIKE %s OR g.contact_number LIKE %s
     GROUP BY g.guest_id, g.full_name, g.contact_number
     ORDER BY g.full_name ASC;
     ```
  4. Returns `(True, guests_list)`.
  5. `load_guests()` clears current Treeview items via `for item in self.tree.get_children(): self.tree.delete(item)` and inserts the filtered rows via `self.tree.insert(...)`.

---

# 6. Screen-by-Screen In-Depth Execution Flows

## 6.1 Screen A: Executive Dashboard

### Visual Components & Locations
1. **Header & Context**:
   - `lbl_page_title`: Line 164 in `main.py`, text dynamically updated to "Executive Dashboard".
   - `lbl_page_subtitle`: Line 174 in `main.py`, text dynamically updated.
   - `lbl_date`: Line 189 in `main.py`, formats current date using `datetime.now().strftime("%A, %b %d, %Y")`.
2. **Top Metrics Row (4 Cards)**:
   - Total Rooms (`card_total`): Line 43 in `ui/dashboard_view.py`, accent `#263C35`.
   - Available Rooms (`card_available`): Line 52 in `ui/dashboard_view.py`, accent `#4E7C5F`.
   - Occupied Rooms (`card_occupied`): Line 61 in `ui/dashboard_view.py`, accent `#C67D34`.
   - Under Maintenance (`card_maintenance`): Line 70 in `ui/dashboard_view.py`, accent `#B94A48`.
3. **Action Metrics Row (3 Cards)**:
   - Active Bookings (`card_active_res`): Line 86 in `ui/dashboard_view.py`, accent `#436E82`.
   - Today's Expected Check-Ins (`card_checkins`): Line 95 in `ui/dashboard_view.py`, accent `#82916C`.
   - Today's Expected Check-Outs (`card_checkouts`): Line 104 in `ui/dashboard_view.py`, accent `#A2703F`.
4. **Schedule Table**:
   - Title: "Today's Arrival & Departure Schedule" (Line 127).
   - Refresh Button: Line 137, invokes `self.load_dashboard`.
   - Treeview Table: Line 164, 6 columns (`id`, `event_type`, `guest`, `room`, `dates`, `status`).

### How `StatCard` Works
`StatCard` inherits from `tk.Frame` (`ui/components.py`, Lines 16–75). In its constructor:
- It configures a white card background (`#FFFFFF`) with a 1px border (`#E5E1D5`).
- It packs a 3px accent frame at the top (`accent_strip`).
- It packs three labels: `lbl_title` (small bold uppercase), `lbl_value` (large 22pt bold text), and `lbl_caption` (muted descriptive text).
- `update_value(new_value, new_caption)` (Line 70) dynamically changes the displayed text via `.config(text=...)` without rebuilding widgets.

### Data Fetching & UI Update Flow
When `load_dashboard()` runs (Lines 192–263):
1. Calls `logic/dashboard_logic.py:get_dashboard_metrics()` (Line 16), which runs two optimized SQL aggregation queries:
   ```sql
   -- Query 1: Room breakdown
   SELECT COUNT(*) AS total_rooms,
          COUNT(CASE WHEN status = 'Available' THEN 1 END) AS available_rooms,
          COUNT(CASE WHEN status = 'Occupied' THEN 1 END) AS occupied_rooms,
          COUNT(CASE WHEN status = 'Maintenance' THEN 1 END) AS maintenance_rooms
   FROM rooms;

   -- Query 2: Reservations breakdown
   SELECT COUNT(CASE WHEN status IN ('Booked', 'Checked In') THEN 1 END) AS active_bookings,
          COUNT(CASE WHEN check_in = CURDATE() AND status = 'Booked' THEN 1 END) AS today_checkins,
          COUNT(CASE WHEN check_out = CURDATE() AND status = 'Checked In' THEN 1 END) AS today_checkouts
   FROM reservations;
   ```
2. The dictionary of counts is parsed and formatted:
   - `self.card_total.update_value(m["total_rooms"], ...)`
   - `self.card_available.update_value(m["available_rooms"], ...)`
   - `self.card_occupied.update_value(m["occupied_rooms"], ...)`
   - `self.card_maintenance.update_value(m["maintenance_rooms"], ...)`
   - `self.card_active_res.update_value(m["active_bookings"], ...)`
   - `self.card_checkins.update_value(f"{m['today_checkins']} Arrivals", ...)`
   - `self.card_checkouts.update_value(f"{m['today_checkouts']} Departures", ...)`
3. Calls `get_todays_schedule()` (Line 78), which runs a `UNION ALL` query fetching arrivals (`check_in = CURDATE() AND status = 'Booked'`) and departures (`check_out = CURDATE() AND status = 'Checked In'`).
4. Clears old rows from `self.tree` and inserts each record with colored visual status tags (`Arrival` in slate blue, `Departure` in amber brown).

---

## 6.2 Screen B: Room Inventory Management

### Key Widgets & Dialogs
- **Search Box**: `self.ent_search` (`ttk.Entry`, Line 251). Bound to `<KeyRelease>` at Line 253.
- **Type Filter**: `self.cmb_type` (`ttk.Combobox`, Line 265). Values: `["All Types", "Single", "Double", "Deluxe", "Suite"]`. Bound to `<<ComboboxSelected>>` at Line 273.
- **Status Filter**: `self.cmb_status` (`ttk.Combobox`, Line 285). Values: `["All Statuses", "Available", "Occupied", "Maintenance"]`. Bound to `<<ComboboxSelected>>` at Line 293.
- **Action Buttons**: `+ Add Room` (Line 296), `Edit Room` (Line 303), `Delete Room` (Line 319), `⟳ Refresh` (Line 335).
- **Rooms Table**: `self.tree` (`ttk.Treeview`, Line 384). 5 columns: `id`, `room_num`, `room_type`, `price`, `status`.
- **RoomFormDialog**: `tk.Toplevel` modal window (Lines 24–213).

### Execution Flows

#### 1. Add Room Flow
1. User clicks `+ Add Room` $\rightarrow$ `open_add_room_dialog()` $\rightarrow$ opens `RoomFormDialog(mode="add")`.
2. User enters room number (e.g. `101`), chooses category (`Deluxe`), enters rate (`2500.00`), chooses status (`Available`), and clicks `Save Room`.
3. `_on_save()` calls `logic/room_logic.py:add_room()`.
4. `add_room()` validates data:
   - Room number must not be empty and must not exceed 10 characters.
   - `is_room_number_taken()` verifies room `101` doesn't already exist.
   - Price must be float $> 0$.
5. Executes `INSERT INTO rooms (room_number, room_type, price, status) VALUES (%s, %s, %s, %s)`.
6. `conn.commit()`, closes cursor and connection.
7. Modal shows success messagebox, triggers `load_rooms()`, and destroys modal.

#### 2. Edit Room Flow
1. User selects a row in Treeview and clicks `Edit Room` (or double-clicks row).
2. `_get_selected_room()` retrieves cached dictionary for selected row.
3. Opens `RoomFormDialog(mode="edit", room_data=selected)`.
4. Modal pre-populates fields with existing room data.
5. User edits price or status and clicks `Update Room`.
6. `_on_save()` calls `logic/room_logic.py:update_room()`.
7. **Business Rule Guard**: If the user attempts to change status away from `Occupied` while a guest is actively checked into this room, `update_room()` queries `SELECT COUNT(*) FROM reservations WHERE room_id = %s AND status = 'Checked In'` and rejects the edit with an informative message.
8. Executes `UPDATE rooms SET room_number = %s, room_type = %s, price = %s, status = %s WHERE room_id = %s`.
9. `conn.commit()`, refreshes table, destroys dialog.

#### 3. Delete Room Flow (Referential Integrity Guard)
1. User selects room and clicks `Delete Room`.
2. Prompts confirmation: `messagebox.askyesno("Confirm Deletion", ...)`.
3. Calls `logic/room_logic.py:delete_room(room_id)`.
4. `delete_room()` first calls `can_delete_room(room_id)` (Line 259), executing:
   ```sql
   SELECT COUNT(*) FROM reservations WHERE room_id = %s;
   ```
5. If count $> 0$, deletion is **prevented**:
   *"Cannot delete this room. It is linked to X existing reservation(s). To preserve booking history and relational database integrity, rooms with active or past reservations cannot be removed."*
6. If count $= 0$, executes `DELETE FROM rooms WHERE room_id = %s;` and calls `conn.commit()`.

---

## 6.3 Screen C: Guest Directory & Profiles

### Key Widgets & Dialogs
- **Search Box**: `self.ent_search` (`ttk.Entry`, Line 208).
- **Toolbar Buttons**: `+ Add Guest` (Line 213), `Edit Guest` (Line 220), `Delete Guest` (Line 237), `⟳ Refresh` (Line 252).
- **Guests Table**: `self.tree` (`ttk.Treeview`, Line 301). 4 columns: `id`, `name`, `contact`, `bookings`.
- **GuestFormDialog**: `tk.Toplevel` modal window (Lines 21–171).

### Execution Flows

#### 1. Add Guest Flow
1. User clicks `+ Add Guest` $\rightarrow$ opens `GuestFormDialog(mode="add")`.
2. User enters name (e.g. `Jane Doe`) and phone (e.g. `+1 555-0192`) and clicks `Save Guest`.
3. `_on_save()` calls `logic/guest_logic.py:add_guest()`.
4. `validate_guest_data()` enforces:
   - Full name cannot be empty, minimum 2 characters, maximum 100 characters.
   - Contact number cannot be empty, maximum 20 characters.
   - Characters allowed: digits, spaces, `+`, `-`, `(`, `)`, `.`.
   - Must contain at least 7 digits for a plausible telephone number.
5. Executes `INSERT INTO guests (full_name, contact_number) VALUES (%s, %s);`.
6. `conn.commit()`, refreshes table, closes dialog.

#### 2. Edit Guest Flow
1. User selects guest and clicks `Edit Guest` (or double-clicks row).
2. Opens `GuestFormDialog(mode="edit", guest_data=selected)`.
3. Fields are pre-filled; user updates information and clicks `Update Guest`.
4. Executes `UPDATE guests SET full_name = %s, contact_number = %s WHERE guest_id = %s;`.
5. `conn.commit()`, refreshes table, closes dialog.

#### 3. Delete Guest Flow (Referential Integrity Guard)
1. User selects guest and clicks `Delete Guest`.
2. Calls `logic/guest_logic.py:delete_guest(guest_id)`.
3. `can_delete_guest(guest_id)` executes:
   ```sql
   SELECT COUNT(*) FROM reservations WHERE guest_id = %s;
   ```
4. If the guest has associated reservations, deletion is **aborted**:
   *"Cannot delete this guest profile. It is linked to X existing reservation(s). To preserve front-desk booking history and relational database integrity, guests with associated reservations cannot be removed."*
5. If count $= 0$, executes `DELETE FROM guests WHERE guest_id = %s;`.

---

## 6.4 Screen D: Reservations & Front-Desk Operations

### Key Widgets & Dialogs
- **Search Box**: `self.ent_search` (`ttk.Entry`, Line 384). Searches guest names and room numbers.
- **Status Filter**: `self.cmb_status` (`ttk.Combobox`, Line 397). Values: `["All Statuses", "Booked", "Checked In", "Checked Out", "Cancelled"]`.
- **Toolbar Buttons**: `+ New Reservation` (Line 408), `Edit Dates` (Line 415), `Check In` (Line 431), `Check Out` (Line 447), `Cancel Booking` (Line 463), `⟳ Refresh` (Line 479).
- **Reservations Table**: `self.tree` (`ttk.Treeview`, Line 528). 8 columns: `id`, `guest`, `room`, `check_in`, `check_out`, `nights`, `total`, `status`.
- **ReservationFormDialog**: `tk.Toplevel` modal (Lines 27–347).

### Live Price Calculation Preview
In `ReservationFormDialog` (Lines 206–232):
- As the user changes the selected room (`<<ComboboxSelected>>`) or types into the check-in / check-out date entries (`<KeyRelease>`), `_update_calc_preview()` runs immediately.
- It parses dates with `datetime.strptime(str, "%Y-%m-%d")`, calculates `nights = (cout_date - cin_date).days`, multiplies by room rate, and displays:
  `Rate: ₹2,500.00/night  •  3 nights  •  Estimated Total: ₹7,500.00`.
- If `checkout <= checkin`, it warns in red text: `⚠ Check-out date must be strictly after check-in date.`

### The Mathematical Date-Overlap Collision Logic
When creating or updating a reservation, Staywise verifies that no other guest has booked that room during that interval (`logic/booking_logic.py`, Lines 55–85):

$$\text{Conflict exists if: } (\text{New Check-In} < \text{Existing Check-Out}) \land (\text{New Check-Out} > \text{Existing Check-In})$$

```sql
SELECT r.reservation_id, r.check_in, r.check_out, r.status, g.full_name
FROM reservations r
JOIN guests g ON r.guest_id = g.guest_id
WHERE r.room_id = %s
  AND r.status IN ('Booked', 'Checked In')
  AND r.check_in < %s   -- existing check_in < new check_out
  AND r.check_out > %s  -- existing check_out > new check_in
  AND (%s IS NULL OR r.reservation_id != %s)
LIMIT 1
LOCK IN SHARE MODE;
```
- **Adjacent Bookings Allowed**: If Guest A checks out on `2026-11-05` and Guest B checks in on `2026-11-05`, they do NOT overlap because `new_check_in (2026-11-05) < existing_check_out (2026-11-05)` evaluates to `False`. This allows standard same-day hotel turnover.

### Lifecycle State Machine Transitions
Reservations transition strictly through a defined finite state machine:

```
                  ┌──────────────┐
                  │    BOOKED    │
                  └──────┬───────┘
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
    ┌──────────────┐            ┌──────────────┐
    │  CHECKED IN  │            │  CANCELLED   │
    └──────┬───────┘            └──────────────┘
           ▼
    ┌──────────────┐
    │ CHECKED OUT  │
    └──────────────┘
```

1. **Check-In (`handle_check_in`)** (`logic/booking_logic.py`, Lines 382–465):
   - Current status must be `Booked`.
   - Check-in date cannot be in the future (`cin_date <= date.today()`).
   - Verifies room is not already occupied by another in-house guest.
   - Atomically updates:
     `UPDATE reservations SET status = 'Checked In' WHERE reservation_id = %s;`
     `UPDATE rooms SET status = 'Occupied' WHERE room_id = %s;`
   - Calls `conn.commit()`.
2. **Check-Out (`handle_check_out`)** (`logic/booking_logic.py`, Lines 467–523):
   - Current status must be `Checked In`.
   - Atomically updates:
     `UPDATE reservations SET status = 'Checked Out' WHERE reservation_id = %s;`
   - Calls `synchronize_room_status_after_change(cursor, room_id)`:
     - If room is `Maintenance`, preserves `Maintenance`.
     - Checks if any other reservations are currently `Checked In` for this room. If none, sets room status back to `Available`.
   - Calls `conn.commit()`.
3. **Cancellation (`handle_cancel_booking`)** (`logic/booking_logic.py`, Lines 525–583):
   - Only `Booked` reservations can be cancelled.
   - Cannot cancel `Checked In` (must Check Out) or `Checked Out`.
   - Updates reservation status to `Cancelled` and synchronizes room status.

---

# 7. MySQL Database Integration & Relational Architecture

### 7.1 Relational Schema & Table Definitions

```
 ┌──────────────────────┐             ┌──────────────────────────────┐
 │        ROOMS         │             │         RESERVATIONS         │
 ├──────────────────────┤             ├──────────────────────────────┤
 │ PK  room_id (INT)    │1           *│ PK  reservation_id (INT)     │
 │     room_number (VC) │─────────────│ FK  room_id (INT)            │
 │     room_type (VC)   │             │ FK  guest_id (INT)           │
 │     price (DECIMAL)  │             │     check_in (DATE)          │
 │     status (VC)      │             │     check_out (DATE)         │
 └──────────────────────┘             │     status (VC)              │
                                      └──────────────┬───────────────┘
 ┌──────────────────────┐                            │*
 │        GUESTS        │                            │
 ├──────────────────────┤                            │
 │ PK  guest_id (INT)   │1                           │
 │     full_name (VC)   │────────────────────────────┘
 │     contact_number   │
 └──────────────────────┘
```

1. **`rooms` Table**:
   - `room_id`: Primary Key, auto-increment integer.
   - `room_number`: Unique string (up to 10 chars, e.g. "101", "204B").
   - `room_type`: Category enum (`Single`, `Double`, `Deluxe`, `Suite`).
   - `price`: Nightly rate (`DECIMAL(10,2)`).
   - `status`: Operational state (`Available`, `Occupied`, `Maintenance`).
2. **`guests` Table**:
   - `guest_id`: Primary Key, auto-increment integer.
   - `full_name`: Guest legal name (`VARCHAR(100)`).
   - `contact_number`: Phone number (`VARCHAR(20)`).
3. **`reservations` Table**:
   - `reservation_id`: Primary Key, auto-increment integer.
   - `guest_id`: Foreign Key referencing `guests(guest_id)`.
   - `room_id`: Foreign Key referencing `rooms(room_id)`.
   - `check_in`: Stay arrival date (`DATE`).
   - `check_out`: Stay departure date (`DATE`).
   - `status`: Reservation state (`Booked`, `Checked In`, `Checked Out`, `Cancelled`).

---

### 7.2 Database Operations Explained

#### 1. `get_connection()` (`database.py`, Lines 8–15)
Calls `mysql.connector.connect()` with credentials read from the environment. Returns an active MySQL connection handle.

#### 2. `conn.cursor(dictionary=True)`
Creates a cursor that returns rows as Python dictionaries (`{"room_number": "101", ...}`) instead of raw tuples (`("101", ...)`). This makes column lookups readable and safe against column index shifts.

#### 3. Parameterized SQL Queries (`%s`)
**Never concatenate strings into SQL statements!**
```python
# CORRECT & SECURE (Used in Staywise):
cursor.execute("SELECT * FROM rooms WHERE room_number = %s;", (room_num,))

# DANGEROUS SQL INJECTION (Never used):
# cursor.execute(f"SELECT * FROM rooms WHERE room_number = '{room_num}';")
```
- **Why?** The MySQL driver escapes special characters (quotes, semicolons, comments) so that user input is treated strictly as data literals, never executable SQL commands.

#### 4. `conn.commit()` vs `conn.rollback()`
- **`conn.commit()`**: Permanently saves all `INSERT`, `UPDATE`, or `DELETE` operations executed during the transaction to the database disk.
- **`conn.rollback()`**: If an exception occurs, or if business rules are violated (e.g. date collision detected), `conn.rollback()` completely cancels all uncommitted changes, leaving the database in its original clean state.

#### 5. `try ... except ... finally` Resource Management Pattern
Every single database function in Staywise adheres to this strict defensive template:
```python
conn = None
cursor = None
try:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # execute SQL operations...
    conn.commit()
except mysql.connector.Error as err:
    if conn:
        conn.rollback()
    return False, f"Database error: {err.msg}"
finally:
    if cursor:
        cursor.close()
    if conn and conn.is_connected():
        conn.close()
```
- **Why?** Prevents database connection leaks and socket exhaustion. Even if the application crashes or an unhandled query error occurs, the `finally` block guarantees cursor and socket release back to the MySQL server.

---

### 7.3 End-to-End Execution Flow Diagram

```
User Action: Click "Check In" Button in UI
│
├── 1. Tkinter Event: command=self.handle_check_in (ui/reservations_view.py:443)
│
├── 2. UI Validation: _get_selected_reservation() checks if row is selected
│
├── 3. User Confirmation: messagebox.askyesno("Confirm Check-In", ...)
│
├── 4. Business Logic Call: check_in_reservation(res_id) (logic/booking_logic.py:382)
│
├── 5. DB Connection: conn = get_connection(), conn.autocommit = False
│
├── 6. SQL Lock & Verify:
│      SELECT ... FROM reservations ... WHERE reservation_id = %s FOR UPDATE;
│      Enforces: status == 'Booked' and check_in <= CURDATE()
│
├── 7. SQL Atomic Updates:
│      UPDATE reservations SET status = 'Checked In' WHERE reservation_id = %s;
│      UPDATE rooms SET status = 'Occupied' WHERE room_id = %s;
│
├── 8. Commit: conn.commit()
│
├── 9. Return Result: (True, "Guest checked into Room #101!")
│
└── 10. UI Refresh:
       - messagebox.showinfo("Check-In Complete", message)
       - self.load_reservations() fetches fresh data and updates Treeview
```

---

# 8. Core Python Programming Concepts Used in Staywise

### 1. Object-Oriented Programming (Classes & Inheritance)
- Every major UI view inherits from `tk.Frame`:
  ```python
  class DashboardView(tk.Frame):
      def __init__(self, parent, **kwargs):
          super().__init__(parent, bg=COLOR_BG, **kwargs)
  ```
  - `super().__init__(parent)` invokes the constructor of the parent `tk.Frame` class, properly initializing the underlying Tkinter widget structure.
- Modal dialogs inherit from `tk.Toplevel`:
  ```python
  class RoomFormDialog(tk.Toplevel):
      def __init__(self, parent, mode="add", ...):
          super().__init__(parent)
  ```

### 2. Constructor `__init__()` and `self`
- `__init__()` is the initializer method automatically invoked when a class instance is created.
- `self` represents the specific instance of the class. It binds attributes (such as `self.tree`, `self.ent_search`, `self.rooms_cache`) and methods to that instance so they can be accessed across different class functions.

### 3. Exception Handling (`try ... except ... finally`)
- Used in all database logic files (`room_logic.py`, `guest_logic.py`, etc.) to catch `mysql.connector.Error`, issue a `conn.rollback()`, and ensure sockets are closed in `finally:`.
- Used in date parsing (`datetime.strptime`) to catch `ValueError` if a user inputs malformed text.

### 4. Conditional Statements & Control Flow (`if ... elif ... else`)
- Validates inputs before running SQL queries.
- Manages UI states (e.g. if room count is 0, display *"Inventory empty"* vs *"Showing 12 rooms"*).

### 5. Collections (Lists, Tuples, Dictionaries)
- **Lists**: `self.rooms_cache = []` stores in-memory lists of room records.
- **Tuples**: `VALID_ROOM_TYPES = ("Single", "Double", "Deluxe", "Suite")` provides immutable constants. Also used for SQL parameters: `cursor.execute(query, (clean_num, clean_type))`.
- **Dictionaries**: Returned by `cursor = conn.cursor(dictionary=True)` for key-based column access (`r["room_number"]`).

### 6. String Formatting & F-Strings
- Used extensively for dynamic labels:
  `f"Room {r['room_number']} — {r['room_type']} (₹{float(r['price']):,.2f}/night)"`
- Number formatting: `:,.2f` formats numbers with comma thousands-separators and 2 decimal places (e.g. `25000.5` $\rightarrow$ `25,000.50`).

### 7. Lambda Functions (Anonymous Functions)
- Used in event bindings when an argument needs to be passed to the callback:
  ```python
  # ui/rooms_view.py: Line 404
  self.tree.bind("<Double-1>", lambda event: self.open_edit_room_dialog())

  # ui/components.py: Lines 174-175
  self.bind("<Enter>", lambda e: self.config(bg=self.hover_bg))
  self.bind("<Leave>", lambda e: self.config(bg=self.default_bg))
  ```

### 8. Date and Time Handling (`datetime`, `date`, `timedelta`)
- `datetime.now().strftime("%A, %b %d, %Y")` formats the header date.
- `datetime.strptime(str, "%Y-%m-%d").date()` parses date text input.
- `nights = (cout_date - cin_date).days` calculates stay length.
- `date.today() + timedelta(days=2)` provides default 2-night check-out dates.

---

# 9. Comprehensive Viva Examination Q&A

### Category 1: Tkinter Basics
1. **Q: What is Tkinter?**
   - **A:** Tkinter is the standard Python interface to the Tk GUI toolkit. It provides cross-platform windowing, widgets, and an event-driven loop.
2. **Q: What is `root = tk.Tk()`?**
   - **A:** It initializes the Tcl/Tk interpreter and creates the top-level master application window.
3. **Q: What is `root.mainloop()`?**
   - **A:** It starts the Tkinter event loop. It waits for user events (mouse clicks, keystrokes, window resizing), routes them to callback functions, and continuously redraws the UI until the window closes.
4. **Q: What is the difference between `tkinter` and `tkinter.ttk`?**
   - **A:** Classic `tkinter` provides basic widgets (`Frame`, `Label`, `Button`). `tkinter.ttk` (Themed Tkinter) provides modern styled widgets (`Treeview`, `Combobox`, `Scrollbar`) that support themes and advanced formatting.
5. **Q: What does `self.root.geometry("1200x740")` do?**
   - **A:** Sets the default width of the window to 1200 pixels and height to 740 pixels.
6. **Q: What does `self.root.minsize(1040, 660)` do?**
   - **A:** Sets a minimum boundary so the user cannot resize the window below 1040px wide by 660px high, preventing UI components from being squashed.

---

### Category 2: Widgets and Layout Managers
7. **Q: What is the difference between `Label` and `Entry`?**
   - **A:** `Label` displays non-editable static or dynamic text/images. `Entry` is an interactive single-line input field that accepts keyboard typing from the user.
8. **Q: What is a `ttk.Treeview` and why is it used in Staywise?**
   - **A:** `ttk.Treeview` is a multi-column tabular data grid widget. It is used in Staywise to display lists of rooms, guests, reservations, and daily schedules with column headers and row selection.
9. **Q: What is a `ttk.Combobox`?**
   - **A:** A drop-down selection widget that combines a text field with a pop-up listbox. We set `state="readonly"` so users can only pick allowed choices.
10. **Q: What is the difference between `.pack()` and `.grid()`?**
    - **A:** `.pack()` places widgets along container edges (`top`, `bottom`, `left`, `right`) in a sequential document flow. `.grid()` aligns widgets in a 2-dimensional grid of rows and columns.
11. **Q: Can you mix `.pack()` and `.grid()` in the same window?**
    - **A:** Never inside the *same parent container frame* (it causes Tkinter geometry freeze). However, you *can* use `.pack()` on a parent frame and `.grid()` inside its child frame, exactly as we do in Staywise.
12. **Q: What does `pack_propagate(False)` do on the sidebar?**
    - **A:** It prevents the sidebar frame from automatically resizing (shrinking) to fit the dimensions of its child buttons, preserving its fixed width of 240px.
13. **Q: What does `sticky="nsew"` do in `.grid()`?**
    - **A:** It stretches the widget to touch the North, South, East, and West borders of its grid cell, ensuring it completely fills the available column and row space.
14. **Q: What is `Toplevel` and how does Staywise use it?**
    - **A:** `tk.Toplevel` creates an independent pop-up child window. Staywise uses it for `RoomFormDialog`, `GuestFormDialog`, and `ReservationFormDialog`.
15. **Q: What does `self.grab_set()` do on a modal dialog?**
    - **A:** It directs all application mouse and keyboard events exclusively to the dialog window, making it modal and preventing users from clicking background screens until the dialog is closed.

---

### Category 3: Events and Callbacks
16. **Q: What is a callback in Tkinter?**
    - **A:** A callback is a Python function reference passed to a widget (via `command=` or `.bind()`) that Tkinter executes when a specific user event occurs.
17. **Q: What is the difference between `command=` and `.bind()`?**
    - **A:** `command=` is a built-in shortcut parameter on Buttons and Scrollbars for primary actions (click, scroll) and does not pass an event object. `.bind()` attaches lower-level events (`<Button-1>`, `<KeyRelease>`, `<Double-1>`, `<Enter>`) to any widget and passes an `Event` object to the handler.
18. **Q: What is `<KeyRelease>` and why do we use it for searching?**
    - **A:** It fires immediately after the user releases a keyboard key. In Staywise, it triggers live instant filtering in search boxes without requiring the user to press Enter or click a button.
19. **Q: What does `<<ComboboxSelected>>` do?**
    - **A:** It is a virtual event generated by `ttk.Combobox` whenever the user picks an item from the drop-down list.
20. **Q: How does double-clicking a Treeview row open the edit dialog?**
    - **A:** We bind `<Double-1>` (mouse double click) to `self.tree.bind("<Double-1>", lambda event: self.open_edit_room_dialog())`. The handler retrieves the selected row ID and opens the dialog.
21. **Q: Why do we use `lambda event:` when binding `<Double-1>`?**
    - **A:** Tkinter `.bind()` passes an `event` object to the callback. `lambda event:` accepts this event argument and calls our method without argument mismatch errors.
22. **Q: How do hover effects work on `SidebarButton` and `ActionButton`?**
    - **A:** We bind `<Enter>` to set the background to a lighter highlight color, and `<Leave>` to restore the original background color.

---

### Category 4: Python OOP Concepts
23. **Q: What is a class and an object?**
    - **A:** A class is a blueprint or template defining attributes and methods. An object is an instantiated instance of that class (e.g. `RoomsView` is a class; `self.views["rooms"]` is an object).
24. **Q: What is the purpose of `__init__()`?**
    - **A:** It is the constructor method in Python. It initializes the object's initial attributes and builds its user interface upon creation.
25. **Q: Why is `self` required in Python methods?**
    - **A:** `self` explicitly references the current class instance, allowing methods to read and modify attributes belonging to that specific object (like `self.tree`).
26. **Q: What is inheritance and where is it used in Staywise?**
    - **A:** Inheritance allows a class to acquire attributes and behaviors from a parent class. For example, `DashboardView(tk.Frame)` inherits from `tk.Frame`, and `RoomFormDialog(tk.Toplevel)` inherits from `tk.Toplevel`.
27. **Q: What does `super().__init__(parent)` do?**
    - **A:** It calls the constructor of the superclass (`tk.Frame`), ensuring Tkinter's internal C/Tcl widget data structures are initialized before we add our custom elements.
28. **Q: What is encapsulation in Staywise?**
    - **A:** Internal helper methods are prefixed with an underscore (e.g. `_build_ui()`, `_on_save()`, `_update_calc_preview()`), signaling that they are private implementation details not meant to be called externally.

---

### Category 5: MySQL & Database Fundamentals
29. **Q: What library connects Python to MySQL in this project?**
    - **A:** `mysql-connector-python` (version 8.0+), the official MySQL driver for Python.
30. **Q: What is the purpose of `database.py`?**
    - **A:** It acts as a centralized connection factory (`get_connection()`), reading credentials from `.env` so database connection parameters are not hardcoded across multiple files.
31. **Q: What is a database cursor?**
    - **A:** A cursor is a control structure that enables traversal and execution of SQL statements over a database connection.
32. **Q: What does `cursor = conn.cursor(dictionary=True)` do?**
    - **A:** It configures the cursor to return rows as Python dictionaries (`{"room_number": "101"}`) instead of tuples, improving code clarity.
33. **Q: What is the difference between `fetchone()` and `fetchall()`?**
    - **A:** `fetchone()` retrieves the next single row of a query result (or `None`). `fetchall()` retrieves all remaining rows as a list.
34. **Q: Why must cursors and connections be closed in a `finally` block?**
    - **A:** Sockets and MySQL thread resources must be released back to the operating system and database server, even if a Python exception occurs, to avoid connection leaks.
35. **Q: What is SQL Injection and how does Staywise prevent it?**
    - **A:** SQL injection occurs when malicious user input modifies SQL command structure. Staywise prevents it completely by using parameterized queries with `%s` placeholders, separating SQL code from user data.

---

### Category 6: CRUD Operations in Staywise
36. **Q: Where is Create implemented for rooms?**
    - **A:** In `logic/room_logic.py:add_room()`, executing `INSERT INTO rooms (room_number, room_type, price, status) VALUES (%s, %s, %s, %s);`.
37. **Q: Where is Read implemented for rooms?**
    - **A:** In `logic/room_logic.py:get_all_rooms()` and `search_and_filter_rooms()`, executing `SELECT ... FROM rooms ORDER BY room_number ASC;`.
38. **Q: Where is Update implemented for rooms?**
    - **A:** In `logic/room_logic.py:update_room()`, executing `UPDATE rooms SET ... WHERE room_id = %s;`.
39. **Q: Where is Delete implemented for rooms?**
    - **A:** In `logic/room_logic.py:delete_room()`, executing `DELETE FROM rooms WHERE room_id = %s;`.
40. **Q: What happens if a user tries to delete a room that has past reservations?**
    - **A:** The system checks `can_delete_room()` first. Because reservations reference `room_id`, the deletion is blocked with an informative message to maintain referential integrity.
41. **Q: What happens if a user tries to delete a guest who has reservations?**
    - **A:** `can_delete_guest()` checks `SELECT COUNT(*) FROM reservations WHERE guest_id = %s`. If count $> 0$, deletion is safely blocked.

---

### Category 7: SQL Queries, Joins, and Aggregations
42. **Q: What SQL JOIN is used in `get_all_reservations()`?**
    - **A:** An `INNER JOIN` between `reservations`, `guests`, and `rooms`:
      ```sql
      FROM reservations r
      JOIN guests g ON r.guest_id = g.guest_id
      JOIN rooms rm ON r.room_id = rm.room_id
      ```
43. **Q: Why is `LEFT JOIN` used in `get_all_guests()`?**
    - **A:** `guests LEFT JOIN reservations` ensures guests who have zero reservations are still returned in the directory with a count of 0.
44. **Q: What does `DATEDIFF(r.check_out, r.check_in)` do in SQL?**
    - **A:** It calculates the integer number of nights between the check-in and check-out dates directly in MySQL.
45. **Q: How is total reservation revenue calculated in SQL?**
    - **A:** `(DATEDIFF(r.check_out, r.check_in) * rm.price) AS total_amount`.
46. **Q: What SQL function gets today's date in MySQL?**
    - **A:** `CURDATE()`.
47. **Q: Why does `get_todays_schedule()` use `UNION ALL`?**
    - **A:** It combines two independent result sets: today's arrivals (`check_in = CURDATE() AND status = 'Booked'`) and today's departures (`check_out = CURDATE() AND status = 'Checked In'`) into a single unified table.

---

### Category 8: Transactions and State Integrity
48. **Q: What is a database transaction?**
    - **A:** A transaction is a sequence of database operations treated as a single, atomic unit of work (ACID properties). Either all operations succeed (`commit`), or none do (`rollback`).
49. **Q: Why does `booking_logic.py` use `conn.autocommit = False`?**
    - **A:** To begin a multi-step atomic transaction. When checking in a guest, both updating the reservation to `Checked In` and updating the room to `Occupied` must succeed together.
50. **Q: What is `FOR UPDATE` in SQL queries?**
    - **A:** It issues an exclusive row-level lock in MySQL InnoDB. It prevents other concurrent sessions from modifying or booking that room until the current transaction completes.
51. **Q: What is the mathematical condition for detecting booking overlap?**
    - **A:** `new_check_in < existing_check_out AND new_check_out > existing_check_in` for active bookings (`Booked` or `Checked In`).

---

### Category 9: Staywise Specific Implementation Questions
52. **Q: How does the application switch between the 4 screens?**
    - **A:** In `main.py`, all 4 screens are instantiated into a dictionary `self.views`. When a navigation button is clicked, `_switch_screen()` calls `view.pack_forget()` on all inactive views and `selected_view.pack(fill="both", expand=True)` on the active one.
53. **Q: What happens when a guest checks out?**
    - **A:** Reservation status becomes `Checked Out`. Then `synchronize_room_status_after_change()` checks if the room is under Maintenance or has any other checked-in guest; if not, room status returns to `Available`.
54. **Q: Why can a user not check in before their check-in date?**
    - **A:** `check_in_reservation()` checks `if cin_date > date.today():` and rejects early check-in, ensuring rooms are not occupied before their scheduled arrival window.
55. **Q: How is the estimated total calculated live in the reservation dialog?**
    - **A:** `_update_calc_preview()` binds to date key releases and room selection changes. It calculates nights between check-in and check-out, multiplies by the room's nightly rate, and updates `self.lbl_calc_info`.

---

# 10. Last-Minute Viva Quick Revision Sheet

Print or review this table 10 minutes before your viva:

| Concept | Staywise Implementation Reference | Viva Answer Summary |
|---|---|---|
| **Entry Point** | `main.py:278 (def main)` | `root = tk.Tk()`, instantiates `StaywiseApp(root)`, runs `root.mainloop()`. |
| **Window Dimensions** | `main.py:39-40` | `1200x740` starting geometry, `1040x660` minimum size. |
| **Theme System** | `ui/theme.py:45 (setup_ttk_styles)` | Custom TTK `clam` styling for Treeview, Combobox, and flat Buttons. |
| **Screen Switching** | `main.py:213 (_switch_screen)` | Uses `pack_forget()` to hide inactive screens and `pack(fill="both", expand=True)` to show active. |
| **Reusable Card** | `ui/components.py:16 (StatCard)` | Compound `tk.Frame` with accent strip and 3 labels; updated via `update_value()`. |
| **Navigation Button**| `ui/components.py:77 (SidebarButton)`| Custom `tk.Frame` with hover effects (`<Enter>`, `<Leave>`) and active indicator pill. |
| **Table Widget** | `ttk.Treeview` | Multi-column grid; populated using `.insert("", "end", values=...)`. |
| **Table Row Click** | `.bind("<Double-1>")` | Double clicking a Treeview row fetches ID via `self.tree.selection()` and opens Edit dialog. |
| **Modal Popups** | `tk.Toplevel` | Child window with `self.transient(parent)` and `self.grab_set()` for modal focus. |
| **Live Filtering** | `.bind("<KeyRelease>")` | Fires on every keystroke in search Entry; immediately calls refresh functions. |
| **Dropdown Widget** | `ttk.Combobox(state="readonly")`| Dropdown list; selection detected via `<<ComboboxSelected>>` virtual event. |
| **DB Connection** | `database.py:8 (get_connection)` | Returns `mysql.connector.connect()` with credentials loaded from `.env`. |
| **Safe SQL Execution**| Parameterized Queries (`%s`) | Prevents SQL injection by passing query values as separate tuples. |
| **Transactions** | `conn.autocommit = False` | Ensures multi-table operations (reservation + room status) commit or rollback together. |
| **Overlap Detection**| `booking_logic.py:55` | `new_in < existing_out AND new_out > existing_in` (same-day turnover allowed). |
| **Referential Safety**| `can_delete_room` / `can_delete_guest`| Verifies `COUNT(*) = 0` in `reservations` before permitting row deletion. |
| **Resource Cleanup** | `try ... except ... finally` | Always closes `cursor` and `conn` in `finally` to prevent connection socket exhaustion. |

