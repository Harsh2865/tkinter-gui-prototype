
import mysql.connector
from database import get_connection

# Allowed choices
VALID_ROOM_TYPES = ("Single", "Double", "Deluxe", "Suite")
VALID_ROOM_STATUSES = ("Available", "Occupied", "Maintenance")


def get_all_rooms():
    """
    Fetches all room records from MySQL, ordered by room number ascending.
    Returns:
        tuple: (success: bool, data_or_error: list[dict] | str)
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT room_id, room_number, room_type, price, status
            FROM rooms
            ORDER BY room_number ASC;
        """
        cursor.execute(query)
        rooms = cursor.fetchall()
        return True, rooms
    except mysql.connector.Error as err:
        return False, f"Database error while fetching rooms: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def search_and_filter_rooms(search_query="", room_type="All Types", status="All Statuses"):
    """
    Searches by room number and filters by room type and status.
    Uses parameterized SQL to prevent SQL injection.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        conditions = []
        params = []

        # Filter by search string in room_number
        if search_query and search_query.strip():
            conditions.append("room_number LIKE %s")
            params.append(f"%{search_query.strip()}%")

        # Filter by Room Type
        if room_type and room_type != "All Types":
            conditions.append("room_type = %s")
            params.append(room_type.strip())

        # Filter by Status
        if status and status != "All Statuses":
            conditions.append("status = %s")
            params.append(status.strip())

        query = "SELECT room_id, room_number, room_type, price, status FROM rooms"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY room_number ASC;"

        cursor.execute(query, tuple(params))
        rooms = cursor.fetchall()
        return True, rooms
    except mysql.connector.Error as err:
        return False, f"Database error during room search/filter: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def is_room_number_taken(room_number, exclude_room_id=None):
    """
    Checks if a room number already exists in the rooms table.
    When editing, exclude_room_id allows keeping the same room number for the same room.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if exclude_room_id is not None:
            query = "SELECT COUNT(*) FROM rooms WHERE room_number = %s AND room_id != %s;"
            cursor.execute(query, (room_number.strip(), exclude_room_id))
        else:
            query = "SELECT COUNT(*) FROM rooms WHERE room_number = %s;"
            cursor.execute(query, (room_number.strip(),))

        count = cursor.fetchone()[0]
        return count > 0
    except mysql.connector.Error:
        # On connection failure, assume conservative fallback
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def validate_room_data(room_number, room_type, price, status, exclude_room_id=None):
    """
    Validates room input parameters before attempting a database write.
    Returns:
        tuple: (is_valid: bool, error_message: str | None, cleaned_data: tuple | None)
    """
    # 1. Room Number Validation
    if not room_number or not str(room_number).strip():
        return False, "Room number cannot be empty.", None

    clean_room_num = str(room_number).strip()
    if len(clean_room_num) > 10:
        return False, "Room number must not exceed 10 characters.", None

    # Check uniqueness
    if is_room_number_taken(clean_room_num, exclude_room_id=exclude_room_id):
        return False, f"Room number '{clean_room_num}' already exists. Please choose a unique room number.", None

    # 2. Room Type Validation
    clean_type = str(room_type).strip()
    if clean_type not in VALID_ROOM_TYPES:
        return False, f"Invalid room type. Must be one of: {', '.join(VALID_ROOM_TYPES)}", None

    # 3. Price Validation
    try:
        clean_price = float(price)
        if clean_price <= 0:
            return False, "Nightly price must be a positive number greater than zero.", None
    except (ValueError, TypeError):
        return False, "Price must be a valid numeric amount (e.g. 150.00).", None

    # 4. Status Validation
    clean_status = str(status).strip()
    if clean_status not in VALID_ROOM_STATUSES:
        return False, f"Invalid status. Must be one of: {', '.join(VALID_ROOM_STATUSES)}", None

    return True, None, (clean_room_num, clean_type, round(clean_price, 2), clean_status)


def add_room(room_number, room_type, price, status="Available"):
    """
    Validates inputs and inserts a new room record into MySQL.
    Returns:
        tuple: (success: bool, message: str, new_room_id: int | None)
    """
    is_valid, err_msg, cleaned = validate_room_data(room_number, room_type, price, status)
    if not is_valid:
        return False, err_msg, None

    clean_num, clean_type, clean_price, clean_status = cleaned

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO rooms (room_number, room_type, price, status)
            VALUES (%s, %s, %s, %s);
        """
        cursor.execute(query, (clean_num, clean_type, clean_price, clean_status))
        conn.commit()
        new_id = cursor.lastrowid
        return True, f"Room '{clean_num}' added successfully!", new_id
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"Failed to add room: {err.msg}", None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def update_room(room_id, room_number, room_type, price, status):
    """
    Validates inputs and updates an existing room in MySQL.
    Returns:
        tuple: (success: bool, message: str)
    """
    if not room_id:
        return False, "Missing room ID."

    is_valid, err_msg, cleaned = validate_room_data(
        room_number, room_type, price, status, exclude_room_id=room_id
    )
    if not is_valid:
        return False, err_msg

    clean_num, clean_type, clean_price, clean_status = cleaned

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Prevent manually changing an occupied room to Available or Maintenance
        if clean_status != "Occupied":
            cursor.execute(
                "SELECT COUNT(*) FROM reservations WHERE room_id = %s AND status = 'Checked In';",
                (room_id,)
            )
            checked_in_cnt = cursor.fetchone()[0]
            if checked_in_cnt > 0:
                return False, (
                    f"Cannot change Room #{clean_num} status to '{clean_status}'. "
                    "There is currently an active guest checked into this room. "
                    "The guest must be checked out through the Reservations screen first."
                )

        query = """
            UPDATE rooms
            SET room_number = %s, room_type = %s, price = %s, status = %s
            WHERE room_id = %s;
        """
        cursor.execute(query, (clean_num, clean_type, clean_price, clean_status, room_id))
        conn.commit()

        if cursor.rowcount == 0:
            return False, f"Room ID {room_id} was not found or no changes were made."

        return True, f"Room '{clean_num}' updated successfully!"
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"Failed to update room: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def can_delete_room(room_id):
    """
    Checks if a room can be safely deleted without violating foreign key constraints.
    Returns:
        tuple: (can_delete: bool, reason_or_message: str)
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM reservations WHERE room_id = %s;"
        cursor.execute(query, (room_id,))
        count = cursor.fetchone()[0]

        if count > 0:
            return False, (
                f"Cannot delete this room. It is linked to {count} existing reservation(s).\n\n"
                "To preserve booking history and relational database integrity, rooms with "
                "active or past reservations cannot be removed."
            )
        return True, "Room has no linked reservations and can be safely deleted."
    except mysql.connector.Error as err:
        return False, f"Database check failed: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def delete_room(room_id):
    """
    Deletes a room only if it is not referenced by any reservations.
    Returns:
        tuple: (success: bool, message: str)
    """
    can_delete, reason = can_delete_room(room_id)
    if not can_delete:
        return False, reason

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "DELETE FROM rooms WHERE room_id = %s;"
        cursor.execute(query, (room_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return False, f"Room ID {room_id} was not found."

        return True, "Room deleted successfully."
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"Failed to delete room: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
