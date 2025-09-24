import asyncio
from bleak import BleakScanner

async def scan():
    print('Scanning for BLE devices...')
    devices = await BleakScanner.discover(timeout=10.0)
    print(f'Found {len(devices)} devices:')
    for d in devices:
        name = d.name or 'Unknown'
        print(f'{d.address}: {name}')
        # Look for SpecialPie-like names
        if any(keyword in name.upper() for keyword in ['SPECIAL', 'PIE', 'TIMER', 'SP']):
            print(f'  *** Possible SpecialPie device! ***')

if __name__ == '__main__':
    asyncio.run(scan())
