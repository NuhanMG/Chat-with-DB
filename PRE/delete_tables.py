import sqlite3

# Connect to database
conn = sqlite3.connect('analysis.db')
cursor = conn.cursor()

# Show current tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables BEFORE cleanup:", tables)

# Drop tables
print("\nRemoving table...")
cursor.execute("DROP TABLE IF EXISTS matches") # replace test_orientation with the table you want to delete
conn.commit()

# Show tables after cleanup
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables AFTER cleanup:", tables)

conn.close()
print("\n✅ Cleanup complete!")
