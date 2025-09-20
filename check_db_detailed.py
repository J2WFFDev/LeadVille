#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('leadville.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check leagues table structure
print("\nLeagues table structure:")
cursor.execute("PRAGMA table_info(leagues);")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Show actual league data
print("\nLeague data:")
cursor.execute("SELECT * FROM leagues;")
leagues = cursor.fetchall()
for league in leagues:
    print(f"  {league}")

conn.close()