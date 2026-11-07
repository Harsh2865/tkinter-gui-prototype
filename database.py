
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

if __name__ == "__main__":
    try:
        connection = get_connection()
        cursor = connection.cursor()

        print("MySQL connected successfully!")

        cursor.execute("SHOW TABLES")

        for table in cursor.fetchall():
            print(table[0])

    except mysql.connector.Error as error:
        print("Database connection failed:", error)

    finally:
        if "cursor" in locals():
            cursor.close()
        if "connection" in locals() and connection.is_connected():
            connection.close()
