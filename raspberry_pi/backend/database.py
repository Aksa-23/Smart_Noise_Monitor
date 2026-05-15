import sqlite3

DB_NAME = "noise_monitor.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS noise_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        avg_db REAL,
        peak_db REAL,
        status TEXT,
        mode TEXT,
        event_marker INTEGER,
        muted INTEGER,
        timestamp TEXT,
        device_id TEXT,
        device_ip TEXT,
        location TEXT,
        threshold_db REAL,
        buzzer TEXT,
        event_type TEXT
    )
    """)

    new_columns = {
        "device_id": "TEXT",
        "device_ip": "TEXT",
        "location": "TEXT",
        "threshold_db": "REAL",
        "buzzer": "TEXT",
        "event_type": "TEXT",
    }

    for column_name, column_type in new_columns.items():
        try:
            cursor.execute(f"ALTER TABLE noise_readings ADD COLUMN {column_name} {column_type}")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()

    print("Database initialized successfully")


def insert_reading(avg_db,
                   peak_db,
                   status,
                   event_type,
                   mode,
                   event_marker,
                   muted,
                   timestamp,
                   device_id=None,
                   device_ip=None,
                   location=None,
                   threshold_db=None,
                   buzzer=None):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO noise_readings
    (avg_db, peak_db, status, mode, event_marker, muted, timestamp,
     device_id, device_ip, location, threshold_db, buzzer, event_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        avg_db,
        peak_db,
        status,
        event_type,
        mode,
        event_marker,
        muted,
        timestamp,
        device_id,
        device_ip,
        location,
        threshold_db,
        buzzer
    ))

    conn.commit()
    conn.close()

    print("Data inserted successfully")


def get_latest_readings(limit=10):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM noise_readings
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    conn.close()

    return rows


def get_latest_reading():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM noise_readings
    ORDER BY id DESC
    LIMIT 1
    """)

    row = cursor.fetchone()

    conn.close()

    return row


if __name__ == "__main__":

    init_db()

    # insert_reading(
    #     avg_db=65.2,
    #     peak_db=71.4,
    #     status="NORMAL",
    #     mode="Study",
    #     event_marker=False,
    #     muted=False,
    #     timestamp="2026-05-06 20:00:00",
    #     device_id="rpi-008",
    #     device_ip="unknown",
    #     location="Sheltered campus area",
    #     threshold_db=70,
    #     buzzer="OFF"
    # )
    #
    # data = get_latest_readings()
    #
    # print(data)