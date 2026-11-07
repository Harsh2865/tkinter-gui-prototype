"""
Staywise — Reservation Business Logic Module
Handles reservation CRUD, date-overlap conflict validation, front-desk
lifecycle state transitions (Booked -> Checked In -> Checked Out / Cancelled),
and room status synchronization within atomic MySQL transactions.

Academic Alignment: APP Unit 5
- Parameterized SQL (%s)
- Date range overlap mathematical interval checking
- Database transaction management (commit & rollback)
- Safe resource closing
"""

from datetime import datetime, date
import mysql.connector
from database import get_connection

VALID_RESERVATION_STATUSES = ("Booked", "Checked In", "Checked Out", "Cancelled")


def validate_dates(check_in_input, check_out_input):
    """
    Validates check-in and check-out dates.
    Enforces format YYYY-MM-DD and check_out > check_in (minimum 1 night).
    Returns:
        tuple: (is_valid: bool, error_message: str | None, cin_date: date | None, cout_date: date | None)
    """
    if not check_in_input or not str(check_in_input).strip():
        return False, "Check-in date cannot be empty.", None, None
    if not check_out_input or not str(check_out_input).strip():
        return False, "Check-out date cannot be empty.", None, None

    try:
        if isinstance(check_in_input, (datetime, date)):
            cin = check_in_input if isinstance(check_in_input, date) else check_in_input.date()
        else:
            cin = datetime.strptime(str(check_in_input).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False, "Check-in date must follow the YYYY-MM-DD format (e.g. 2026-11-01).", None, None

    try:
        if isinstance(check_out_input, (datetime, date)):
            cout = check_out_input if isinstance(check_out_input, date) else check_out_input.date()
        else:
            cout = datetime.strptime(str(check_out_input).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False, "Check-out date must follow the YYYY-MM-DD format (e.g. 2026-11-05).", None, None

    if cout <= cin:
        return False, "Check-out date must be later than check-in date (at least 1 night stay).", None, None

    return True, None, cin, cout


def check_date_overlap_conflict(cursor, room_id, check_in_date, check_out_date, exclude_reservation_id=None):
    """
    Checks if a room has any overlapping active reservation.
    Mathematical interval condition:
        new_check_in < existing_check_out AND new_check_out > existing_check_in
    Adjacent bookings (new_check_in == existing_check_out or new_check_out == existing_check_in)
    are permitted and do NOT conflict.
    Active statuses checked: 'Booked' and 'Checked In'.
    Returns:
        tuple: (has_conflict: bool, conflicting_reservation: dict | None)
    """
    query = """
        SELECT r.reservation_id, r.check_in, r.check_out, r.status, g.full_name
        FROM reservations r
        JOIN guests g ON r.guest_id = g.guest_id
        WHERE r.room_id = %s
          AND r.status IN ('Booked', 'Checked In')
          AND r.check_in < %s
          AND r.check_out > %s
          AND (%s IS NULL OR r.reservation_id != %s)
        LIMIT 1
        LOCK IN SHARE MODE;
    """
    cin_str = check_in_date.strftime("%Y-%m-%d")
    cout_str = check_out_date.strftime("%Y-%m-%d")
    cursor.execute(query, (room_id, cout_str, cin_str, exclude_reservation_id, exclude_reservation_id))
    conflict = cursor.fetchone()
    if conflict:
        return True, conflict
    return False, None


def get_all_reservations():
    """
    Fetches all reservations with guest and room details via SQL JOINs.
    Returns:
        tuple: (success: bool, data_or_error: list[dict] | str)
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                r.reservation_id,
                r.guest_id,
                g.full_name AS guest_name,
                g.contact_number AS guest_contact,
                r.room_id,
                rm.room_number,
                rm.room_type,
                rm.price AS nightly_price,
                r.check_in,
                r.check_out,
                DATEDIFF(r.check_out, r.check_in) AS nights,
                (DATEDIFF(r.check_out, r.check_in) * rm.price) AS total_amount,
                r.status
            FROM reservations r
            JOIN guests g ON r.guest_id = g.guest_id
            JOIN rooms rm ON r.room_id = rm.room_id
            ORDER BY r.check_in DESC, r.reservation_id DESC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return True, rows
    except mysql.connector.Error as err:
        return False, f"Database error fetching reservations: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def search_and_filter_reservations(search_query="", status="All Statuses"):
    """
    Searches reservations by guest name or room number and filters by status.
    Uses parameterized SQL to prevent SQL injection.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        conditions = []
        params = []

        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            conditions.append("(g.full_name LIKE %s OR rm.room_number LIKE %s)")
            params.extend([term, term])

        if status and status != "All Statuses":
            conditions.append("r.status = %s")
            params.append(status.strip())

        query = """
            SELECT 
                r.reservation_id,
                r.guest_id,
                g.full_name AS guest_name,
                g.contact_number AS guest_contact,
                r.room_id,
                rm.room_number,
                rm.room_type,
                rm.price AS nightly_price,
                r.check_in,
                r.check_out,
                DATEDIFF(r.check_out, r.check_in) AS nights,
                (DATEDIFF(r.check_out, r.check_in) * rm.price) AS total_amount,
                r.status
            FROM reservations r
            JOIN guests g ON r.guest_id = g.guest_id
            JOIN rooms rm ON r.room_id = rm.room_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY r.check_in DESC, r.reservation_id DESC;"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return True, rows
    except mysql.connector.Error as err:
        return False, f"Database error during reservation search: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def create_reservation(guest_id, room_id, check_in_input, check_out_input):
    """
    Creates a new reservation within a safe database transaction.
    Validates dates, verifies room is not in Maintenance, checks date overlaps,
    and writes to MySQL.
    Returns:
        tuple: (success: bool, message: str, new_reservation_id: int | None)
    """
    if not guest_id:
        return False, "Please select a valid guest.", None
    if not room_id:
        return False, "Please select a valid room.", None

    is_valid, err_msg, cin, cout = validate_dates(check_in_input, check_out_input)
    if not is_valid:
        return False, err_msg, None

    conn = None
    cursor = None
    try:
        conn = get_connection()
        conn.autocommit = False
        cursor = conn.cursor(dictionary=True)

        # 1. Verify guest exists
        cursor.execute("SELECT guest_id, full_name FROM guests WHERE guest_id = %s;", (guest_id,))
        guest = cursor.fetchone()
        if not guest:
            conn.rollback()
            return False, "The selected guest record was not found.", None

        # 2. Verify room exists and check Maintenance status
        cursor.execute("SELECT room_id, room_number, status, price FROM rooms WHERE room_id = %s FOR UPDATE;", (room_id,))
        room = cursor.fetchone()
        if not room:
            conn.rollback()
            return False, "The selected room was not found.", None

        if room["status"] == "Maintenance":
            conn.rollback()
            return False, f"Room {room['room_number']} is currently marked for Maintenance and cannot be booked.", None

        # 3. Check for overlapping bookings
        has_conflict, conf = check_date_overlap_conflict(cursor, room_id, cin, cout)
        if has_conflict:
            conn.rollback()
            c_in = conf["check_in"].strftime("%Y-%m-%d") if hasattr(conf["check_out"], "strftime") else str(conf["check_in"])
            c_out = conf["check_out"].strftime("%Y-%m-%d") if hasattr(conf["check_out"], "strftime") else str(conf["check_out"])
            return False, (
                f"Booking conflict for Room #{room['room_number']}.\n\n"
                f"Room is already booked by '{conf['full_name']}' from {c_in} to {c_out} "
                f"(Status: {conf['status']}).\n\n"
                "Please choose different dates or another available room."
            ), None

        # 4. Insert the new reservation
        query = """
            INSERT INTO reservations (guest_id, room_id, check_in, check_out, status)
            VALUES (%s, %s, %s, %s, 'Booked');
        """
        cursor.execute(query, (guest_id, room_id, cin.strftime("%Y-%m-%d"), cout.strftime("%Y-%m-%d")))
        new_res_id = cursor.lastrowid

        conn.commit()
        return True, f"Reservation #{new_res_id} created successfully for {guest['full_name']}!", new_res_id
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"Failed to create reservation: {err.msg}", None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def update_reservation(reservation_id, guest_id, room_id, check_in_input, check_out_input):
    """
    Updates dates or room/guest assignment for an existing reservation.
    Excludes the reservation's own ID from conflict detection.
    Returns:
        tuple: (success: bool, message: str)
    """
    if not reservation_id:
        return False, "Missing reservation ID."
    if not guest_id:
        return False, "Please select a valid guest."
    if not room_id:
        return False, "Please select a valid room."

    is_valid, err_msg, cin, cout = validate_dates(check_in_input, check_out_input)
    if not is_valid:
        return False, err_msg

    conn = None
    cursor = None
    try:
        conn = get_connection()
        conn.autocommit = False
        cursor = conn.cursor(dictionary=True)

        # 1. Fetch current reservation state
        cursor.execute("SELECT reservation_id, status, room_id FROM reservations WHERE reservation_id = %s FOR UPDATE;", (reservation_id,))
        current_res = cursor.fetchone()
        if not current_res:
            conn.rollback()
            return False, f"Reservation #{reservation_id} was not found."

        if current_res["status"] in ("Checked Out", "Cancelled"):
            conn.rollback()
            return False, f"Cannot edit dates for a reservation that is already {current_res['status']}."

        # Prevent changing assigned room for an in-house (Checked In) guest
        if current_res["status"] == "Checked In" and int(room_id) != int(current_res["room_id"]):
            conn.rollback()
            return False, (
                "Cannot change the assigned room of an active 'Checked In' reservation. "
                "The guest is currently in-house. Only stay dates can be modified."
            )

        # 2. Check room status
        cursor.execute("SELECT room_id, room_number, status FROM rooms WHERE room_id = %s FOR UPDATE;", (room_id,))
        room = cursor.fetchone()
        if not room:
            conn.rollback()
            return False, "The selected room was not found."

        if room["status"] == "Maintenance":
            conn.rollback()
            return False, f"Room {room['room_number']} is currently marked for Maintenance and cannot be booked."

        # 3. Check for date overlap conflicts (excluding this reservation)
        has_conflict, conf = check_date_overlap_conflict(
            cursor, room_id, cin, cout, exclude_reservation_id=reservation_id
        )
        if has_conflict:
            conn.rollback()
            c_in = conf["check_in"].strftime("%Y-%m-%d") if hasattr(conf["check_in"], "strftime") else str(conf["check_in"])
            c_out = conf["check_out"].strftime("%Y-%m-%d") if hasattr(conf["check_out"], "strftime") else str(conf["check_out"])
            return False, (
                f"Booking conflict for Room #{room['room_number']}.\n\n"
                f"Conflicting booking exists for '{conf['full_name']}' from {c_in} to {c_out}.\n"
                "Please choose different dates or another room."
            )

        # 4. Update reservation
        query = """
            UPDATE reservations
            SET guest_id = %s, room_id = %s, check_in = %s, check_out = %s
            WHERE reservation_id = %s;
        """
        cursor.execute(query, (guest_id, room_id, cin.strftime("%Y-%m-%d"), cout.strftime("%Y-%m-%d"), reservation_id))

        conn.commit()
        return True, f"Reservation #{reservation_id} updated successfully!"
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"Failed to update reservation: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def synchronize_room_status_after_change(cursor, room_id):
    """
    Safely calculates and updates the room's operational status.
    Rules:
      1. If the room is marked 'Maintenance', it remains 'Maintenance'.
      2. If ANY reservation for this room is currently 'Checked In', status is 'Occupied'.
      3. Otherwise, room status is set to 'Available'.
    """
    cursor.execute("SELECT status FROM rooms WHERE room_id = %s FOR UPDATE;", (room_id,))
    room_row = cursor.fetchone()
    if not room_row:
        return

    # Never overwrite a Maintenance condition
    if room_row["status"] == "Maintenance":
        return

    # Check for any currently checked-in reservations
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM reservations WHERE room_id = %s AND status = 'Checked In';",
        (room_id,)
    )
    checked_in_cnt = cursor.fetchone()["cnt"]

    new_status = "Occupied" if checked_in_cnt > 0 else "Available"
    cursor.execute("UPDATE rooms SET status = %s WHERE room_id = %s;", (new_status, room_id))


def check_in_reservation(reservation_id):
    """
    Performs atomic guest check-in:
    - Enforces valid transition: only 'Booked' can be 'Checked In'.
    - Verifies room is not occupied by another active guest.
    - Updates reservation status to 'Checked In'.
    - Updates room status to 'Occupied'.
    Returns:
        tuple: (success: bool, message: str)
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        conn.autocommit = False
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT r.reservation_id, r.room_id, r.status, r.check_in, r.check_out, g.full_name, rm.room_number
            FROM reservations r
            JOIN guests g ON r.guest_id = g.guest_id
            JOIN rooms rm ON r.room_id = rm.room_id
            WHERE r.reservation_id = %s
            FOR UPDATE;
        """, (reservation_id,))
        res = cursor.fetchone()

        if not res:
            conn.rollback()
            return False, f"Reservation #{reservation_id} was not found."

        # Validate lifecycle transition
        if res["status"] != "Booked":
            conn.rollback()
            return False, (
                f"Cannot check in reservation #{reservation_id}. "
                f"Current status is '{res['status']}'. Only 'Booked' reservations can be checked in."
            )

        # Prevent checking in before scheduled check-in date
        cin_val = res["check_in"]
        cin_date = cin_val if isinstance(cin_val, date) else datetime.strptime(str(cin_val), "%Y-%m-%d").date()
        if cin_date > date.today():
            conn.rollback()
            return False, (
                f"Cannot check in early. Reservation #{reservation_id} is scheduled for arrival on "
                f"{cin_date.strftime('%Y-%m-%d')}, which is in the future. "
                "Check-in is only permitted on or after the scheduled arrival date."
            )

        room_id = res["room_id"]

        # Check if room is already occupied by another checked-in guest
        cursor.execute("""
            SELECT r.reservation_id, g.full_name
            FROM reservations r
            JOIN guests g ON r.guest_id = g.guest_id
            WHERE r.room_id = %s AND r.status = 'Checked In' AND r.reservation_id != %s;
        """, (room_id, reservation_id))
        other_guest = cursor.fetchone()
        if other_guest:
            conn.rollback()
            return False, (
                f"Room #{res['room_number']} is currently occupied by guest '{other_guest['full_name']}' "
                f"(Reservation #{other_guest['reservation_id']}).\n"
                "The current guest must check out before a new guest can check in."
            )

        # Execute check-in
        cursor.execute("UPDATE reservations SET status = 'Checked In' WHERE reservation_id = %s;", (reservation_id,))
        cursor.execute("UPDATE rooms SET status = 'Occupied' WHERE room_id = %s;", (room_id,))

        conn.commit()
        return True, f"Guest '{res['full_name']}' has been successfully checked into Room #{res['room_number']}!"
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"Check-in failed: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def check_out_reservation(reservation_id):
    """
    Performs atomic guest check-out:
    - Enforces valid transition: only 'Checked In' can transition to 'Checked Out'.
    - Updates reservation status to 'Checked Out'.
    - Synchronizes room status safely (Available if no other active checked-in booking).
    Returns:
        tuple: (success: bool, message: str)
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        conn.autocommit = False
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT r.reservation_id, r.room_id, r.status, g.full_name, rm.room_number
            FROM reservations r
            JOIN guests g ON r.guest_id = g.guest_id
            JOIN rooms rm ON r.room_id = rm.room_id
            WHERE r.reservation_id = %s
            FOR UPDATE;
        """, (reservation_id,))
        res = cursor.fetchone()

        if not res:
            conn.rollback()
            return False, f"Reservation #{reservation_id} was not found."

        if res["status"] != "Checked In":
            conn.rollback()
            return False, (
                f"Cannot check out reservation #{reservation_id}. "
                f"Current status is '{res['status']}'. Only 'Checked In' reservations can be checked out."
            )

        room_id = res["room_id"]

        # Update reservation
        cursor.execute("UPDATE reservations SET status = 'Checked Out' WHERE reservation_id = %s;", (reservation_id,))

        # Synchronize room status
        synchronize_room_status_after_change(cursor, room_id)

        conn.commit()
        return True, f"Guest '{res['full_name']}' has been successfully checked out of Room #{res['room_number']}!"
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"Check-out failed: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def cancel_reservation(reservation_id):
    """
    Cancels a booking:
    - Enforces valid transition: only 'Booked' can be 'Cancelled'.
    - Cannot cancel a reservation that is already Checked In or Checked Out.
    - Synchronizes room status safely.
    Returns:
        tuple: (success: bool, message: str)
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        conn.autocommit = False
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT r.reservation_id, r.room_id, r.status, g.full_name, rm.room_number
            FROM reservations r
            JOIN guests g ON r.guest_id = g.guest_id
            JOIN rooms rm ON r.room_id = rm.room_id
            WHERE r.reservation_id = %s
            FOR UPDATE;
        """, (reservation_id,))
        res = cursor.fetchone()

        if not res:
            conn.rollback()
            return False, f"Reservation #{reservation_id} was not found."

        if res["status"] == "Cancelled":
            conn.rollback()
            return False, f"Reservation #{reservation_id} is already cancelled."

        if res["status"] == "Checked Out":
            conn.rollback()
            return False, "Cannot cancel a completed (Checked Out) reservation."

        if res["status"] == "Checked In":
            conn.rollback()
            return False, "Cannot cancel a currently Checked In guest. Please use Check Out instead."

        room_id = res["room_id"]

        cursor.execute("UPDATE reservations SET status = 'Cancelled' WHERE reservation_id = %s;", (reservation_id,))
        synchronize_room_status_after_change(cursor, room_id)

        conn.commit()
        return True, f"Reservation #{reservation_id} for '{res['full_name']}' has been cancelled."
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"Cancellation failed: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def get_selectable_guests():
    """
    Helper to fetch registered guests for the reservation form dropdown.
    Returns:
        list of tuples: [(guest_id, display_label), ...]
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT guest_id, full_name, contact_number FROM guests ORDER BY full_name ASC;")
        guests = cursor.fetchall()
        return [(g["guest_id"], f"{g['full_name']} ({g['contact_number']})") for g in guests]
    except mysql.connector.Error:
        return []
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def get_selectable_rooms():
    """
    Helper to fetch all rooms for the reservation form dropdown.
    Returns:
        list of tuples: [(room_id, display_label, status), ...]
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT room_id, room_number, room_type, price, status FROM rooms ORDER BY room_number ASC;")
        rooms = cursor.fetchall()
        return [
            (
                r["room_id"],
                f"Room {r['room_number']} — {r['room_type']} (₹{float(r['price']):,.2f}/night)",
                r["status"],
                float(r["price"])
            )
            for r in rooms
        ]
    except mysql.connector.Error:
        return []
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
