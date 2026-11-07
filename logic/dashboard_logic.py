

import mysql.connector
from database import get_connection


def get_dashboard_metrics():
    """
    Computes live dashboard statistics from MySQL:
    - Total Rooms (registered in inventory)
    - Available Rooms (current room status = 'Available')
    - Occupied Rooms (current room status = 'Occupied')
    - Maintenance Rooms (current room status = 'Maintenance')
    - Active Bookings (status IN ('Booked', 'Checked In'))
    - Today's Check-Ins (check_in = CURDATE() AND status = 'Booked')
    - Today's Check-Outs (check_out = CURDATE() AND status = 'Checked In')

    Returns:
        tuple: (success: bool, metrics_or_error: dict | str)
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Rooms breakdown
        room_query = """
            SELECT 
                COUNT(*) AS total_rooms,
                COUNT(CASE WHEN status = 'Available' THEN 1 END) AS available_rooms,
                COUNT(CASE WHEN status = 'Occupied' THEN 1 END) AS occupied_rooms,
                COUNT(CASE WHEN status = 'Maintenance' THEN 1 END) AS maintenance_rooms
            FROM rooms;
        """
        cursor.execute(room_query)
        room_stats = cursor.fetchone() or {}

        # 2. Reservations breakdown
        res_query = """
            SELECT 
                COUNT(CASE WHEN status IN ('Booked', 'Checked In') THEN 1 END) AS active_bookings,
                COUNT(CASE WHEN check_in = CURDATE() AND status = 'Booked' THEN 1 END) AS today_checkins,
                COUNT(CASE WHEN check_out = CURDATE() AND status = 'Checked In' THEN 1 END) AS today_checkouts
            FROM reservations;
        """
        cursor.execute(res_query)
        res_stats = cursor.fetchone() or {}

        metrics = {
            "total_rooms": int(room_stats.get("total_rooms", 0)),
            "available_rooms": int(room_stats.get("available_rooms", 0)),
            "occupied_rooms": int(room_stats.get("occupied_rooms", 0)),
            "maintenance_rooms": int(room_stats.get("maintenance_rooms", 0)),
            "active_bookings": int(res_stats.get("active_bookings", 0)),
            "today_checkins": int(res_stats.get("today_checkins", 0)),
            "today_checkouts": int(res_stats.get("today_checkouts", 0)),
        }
        return True, metrics
    except mysql.connector.Error as err:
        return False, f"Database error fetching dashboard metrics: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def get_todays_schedule():
    """
    Fetches today's arrivals (status='Booked', check_in=CURDATE())
    and departures (status='Checked In', check_out=CURDATE())
    joined with guest and room details.

    Returns:
        tuple: (success: bool, schedule_or_error: list[dict] | str)
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                r.reservation_id,
                'Arrival (Check-In)' AS schedule_type,
                g.full_name AS guest_name,
                rm.room_number,
                rm.room_type,
                r.check_in,
                r.check_out,
                DATEDIFF(r.check_out, r.check_in) AS nights,
                r.status
            FROM reservations r
            JOIN guests g ON r.guest_id = g.guest_id
            JOIN rooms rm ON r.room_id = rm.room_id
            WHERE r.check_in = CURDATE() AND r.status = 'Booked'

            UNION ALL

            SELECT 
                r.reservation_id,
                'Departure (Check-Out)' AS schedule_type,
                g.full_name AS guest_name,
                rm.room_number,
                rm.room_type,
                r.check_in,
                r.check_out,
                DATEDIFF(r.check_out, r.check_in) AS nights,
                r.status
            FROM reservations r
            JOIN guests g ON r.guest_id = g.guest_id
            JOIN rooms rm ON r.room_id = rm.room_id
            WHERE r.check_out = CURDATE() AND r.status = 'Checked In'

            ORDER BY schedule_type ASC, room_number ASC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        # Format date strings and duration
        schedule = []
        for r in rows:
            cin_str = r["check_in"].strftime("%b %d, %Y") if hasattr(r["check_in"], "strftime") else str(r["check_in"])
            cout_str = r["check_out"].strftime("%b %d, %Y") if hasattr(r["check_out"], "strftime") else str(r["check_out"])
            nights = r["nights"]
            schedule.append({
                "reservation_id": r["reservation_id"],
                "schedule_type": r["schedule_type"],
                "guest_name": r["guest_name"],
                "room_number": r["room_number"],
                "room_type": r["room_type"],
                "dates": f"{cin_str} → {cout_str} ({nights}n)",
                "nights": nights,
                "status": r["status"]
            })

        return True, schedule
    except mysql.connector.Error as err:
        return False, f"Database error fetching today's schedule: {err.msg}"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
