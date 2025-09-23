#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('leadville.db')
cursor = conn.cursor()

# Check table counts
cursor.execute('SELECT COUNT(*) FROM leagues')
leagues_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM stage_configs')
stages_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM target_configs')
targets_count = cursor.fetchone()[0]

# Get league names
cursor.execute('SELECT name FROM leagues')
league_names = cursor.fetchall()

print(f'Leagues: {leagues_count}')
print(f'Stages: {stages_count}')
print(f'Targets: {targets_count}')
print(f'League names: {league_names}')

conn.close()