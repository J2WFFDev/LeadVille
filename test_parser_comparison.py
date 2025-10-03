import sys
sys.path.insert(0, '/home/jrwest/projects/LeadVille')

from src.impact_bridge.ble.parsers.verbose import parse_bt50_frame

# Real frame from database
frame_hex = '5561040009000900170017001000bb085b007a006800000003000000'
frame_bytes = bytes.fromhex(frame_hex)

print(f'Testing frame: {frame_hex}')
print(f'Frame length: {len(frame_bytes)} bytes')
print()

print('=' * 60)
print('TEST: parse_bt50_frame (canonical parser)')
print('=' * 60)
result2 = parse_bt50_frame(frame_bytes, write_db=False)
if result2:
    print(f"Result: {result2}")
    print(f"Velocity: vx={result2['vx']}, vy={result2['vy']}, vz={result2['vz']}")
    magnitude = (result2['vx']**2 + result2['vy']**2 + result2['vz']**2) ** 0.5
    print(f"Magnitude: {magnitude:.1f}")
else:
    print(f"Result: {result2}")
print()

if result2:
    mag2 = (result2['vx']**2 + result2['vy']**2 + result2['vz']**2) ** 0.5
    print(f"parse_bt50_frame magnitude: {mag2:.1f}")
    if mag2 < 100:
        print("  ✅ CORRECT - This gives proper velocity values!")

print()
print('NOTE: parse_5561 has been retired; use parse_bt50_frame for all workflows.')
