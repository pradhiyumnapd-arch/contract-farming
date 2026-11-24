import sqlite3

conn = sqlite3.connect("instance/farming.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE farmer ADD COLUMN farm_area REAL")
cursor.execute("ALTER TABLE farmer ADD COLUMN soil_type TEXT")
cursor.execute("ALTER TABLE farmer ADD COLUMN soil_ph REAL")

conn.commit()
conn.close()

print("Database updated successfully!")