

import re
import mysql.connector
from database import get_connection


def get_all_guests():
    """
    Fetches all guest records from MySQL with their total reservation count,
    ordered by full name ascending.
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
                g.guest_id, 
                g.full_name, 
                g.contact_number, 
                COUNT(r.reservation_id) AS booking_count
            FROM guests g
            LEFT JOIN reservations r ON g.guest_id = r.guest_id
            GROUP BY g.guest_id, g.full_name, g.contact_number
            ORDER BY g.full_name ASC;
        """
        cursor.execute(query)
        guests = cursor.fetchall()
        return True, guests
    except mysql.connector.Error as err:
        return False, f"Database error while fetching guests: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def search_guests(query=""):
    """
    Searches guests by full name or contact number substring.
    Uses parameterized SQL to prevent SQL injection.
    """
    clean_query = query.strip() if query else ""
    if not clean_query:
        return get_all_guests()

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        search_pattern = f"%{clean_query}%"
        sql = """
            SELECT 
                g.guest_id, 
                g.full_name, 
                g.contact_number, 
                COUNT(r.reservation_id) AS booking_count
            FROM guests g
            LEFT JOIN reservations r ON g.guest_id = r.guest_id
            WHERE g.full_name LIKE %s OR g.contact_number LIKE %s
            GROUP BY g.guest_id, g.full_name, g.contact_number
            ORDER BY g.full_name ASC;
        """
        cursor.execute(sql, (search_pattern, search_pattern))
        guests = cursor.fetchall()
        return True, guests
    except mysql.connector.Error as err:
        return False, f"Database error during guest search: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def validate_guest_data(full_name, contact_number):
    """
    Validates guest input fields.
    Returns:
        tuple: (is_valid: bool, error_message: str | None, cleaned_data: tuple | None)
    """
    # 1. Full Name Validation
    if not full_name or not str(full_name).strip():
        return False, "Guest full name cannot be empty.", None

    clean_name = str(full_name).strip()
    if len(clean_name) < 2:
        return False, "Guest name must be at least 2 characters.", None
    if len(clean_name) > 100:
        return False, "Guest name must not exceed 100 characters.", None

    # 2. Contact Number Validation
    if not contact_number or not str(contact_number).strip():
        return False, "Contact number cannot be empty.", None

    clean_contact = str(contact_number).strip()
    if len(clean_contact) > 20:
        return False, "Contact number must not exceed 20 characters.", None

    # Check allowed characters (digits, spaces, +, -, (, ), .)
    allowed_chars = set("0123456789+-() .")
    if not all(c in allowed_chars for c in clean_contact):
        return False, (
            "Contact number contains invalid characters. "
            "Please use only digits, spaces, +, -, and parentheses."
        ), None

    # Ensure there are at least 7 digits for a plausible telephone/mobile number
    digits_count = sum(1 for c in clean_contact if c.isdigit())
    if digits_count < 7:
        return False, "Contact number must contain at least 7 digits.", None

    return True, None, (clean_name, clean_contact)


def add_guest(full_name, contact_number):
    """
    Validates inputs and inserts a new guest record into MySQL.
    Returns:
        tuple: (success: bool, message: str, new_guest_id: int | None)
    """
    is_valid, err_msg, cleaned = validate_guest_data(full_name, contact_number)
    if not is_valid:
        return False, err_msg, None

    clean_name, clean_contact = cleaned

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO guests (full_name, contact_number) VALUES (%s, %s);"
        cursor.execute(query, (clean_name, clean_contact))
        conn.commit()
        new_id = cursor.lastrowid
        return True, f"Guest '{clean_name}' registered successfully!", new_id
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"Failed to add guest: {err.msg}", None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def update_guest(guest_id, full_name, contact_number):
    """
    Validates inputs and updates an existing guest record in MySQL.
    Returns:
        tuple: (success: bool, message: str)
    """
    if not guest_id:
        return False, "Missing guest ID."

    is_valid, err_msg, cleaned = validate_guest_data(full_name, contact_number)
    if not is_valid:
        return False, err_msg

    clean_name, clean_contact = cleaned

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "UPDATE guests SET full_name = %s, contact_number = %s WHERE guest_id = %s;"
        cursor.execute(query, (clean_name, clean_contact, guest_id))
        conn.commit()

        if cursor.rowcount == 0:
            return False, f"Guest ID {guest_id} was not found or no changes were made."

        return True, f"Guest '{clean_name}' updated successfully!"
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"Failed to update guest: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def can_delete_guest(guest_id):
    """
    Checks if a guest can be safely deleted without violating foreign key constraints.
    Returns:
        tuple: (can_delete: bool, reason_or_message: str)
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM reservations WHERE guest_id = %s;"
        cursor.execute(query, (guest_id,))
        count = cursor.fetchone()[0]

        if count > 0:
            return False, (
                f"Cannot delete this guest profile. It is linked to {count} existing reservation(s).\n\n"
                "To preserve front-desk booking history and relational database integrity, "
                "guests with associated reservations cannot be removed."
            )
        return True, "Guest has no linked reservations and can be safely deleted."
    except mysql.connector.Error as err:
        return False, f"Database check failed: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def delete_guest(guest_id):
    """
    Deletes a guest record only if no reservations reference it.
    Returns:
        tuple: (success: bool, message: str)
    """
    can_del, reason = can_delete_guest(guest_id)
    if not can_del:
        return False, reason

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "DELETE FROM guests WHERE guest_id = %s;"
        cursor.execute(query, (guest_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return False, f"Guest ID {guest_id} was not found."

        return True, "Guest profile deleted successfully."
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"Failed to delete guest: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
