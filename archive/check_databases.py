#!/usr/bin/env python3

import sqlite3

print("=== db/bridge.db ===")
try:
    conn = sqlite3.connect("db/bridge.db")
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type= ' table ' ")
    tables = cursor.fetchall()
    print(f"Tables: {[t[0] for t in tables]}")
    
    # Check bridges table
    try:
        cursor.execute("SELECT * FROM bridges")
        bridges = cursor.fetchall()
        print(f"Bridges: {bridges}")
    except:
        print("No bridges table or data")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")

print()
print("=== leadville.db ===")
try:
    conn = sqlite3.connect("leadville.db")
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type= ' table ' ")
    tables = cursor.fetchall()
    print(f"Tables: {[t[0] for t in tables]}")
    
    # Check bridges table
    try:  
        cursor.execute("SELECT * FROM bridges")
        bridges = cursor.fetchall()
        print(f"Bridges: {bridges}")
    except:
        print("No bridges table or data")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
