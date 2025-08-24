import serial.tools.list_ports
import winreg

def list_serial_ports():
    """List all available serial ports including Bluetooth and Arduino"""
    results = []
    friendly = {}

    # Look up Bluetooth device names from the registry
    base = r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
        for i in range(winreg.QueryInfoKey(key)[0]):
            mac = winreg.EnumKey(key, i)
            sub = winreg.OpenKey(key, mac)
            try:
                raw, _ = winreg.QueryValueEx(sub, 'Name')
                name = raw.decode() if isinstance(raw, bytes) else raw
                friendly[mac.lower()] = name
            except FileNotFoundError:
                pass
    except FileNotFoundError:
        pass

    # Scan all serial ports
    for p in serial.tools.list_ports.comports():
        hwid = p.hwid or ''
        desc = p.description or ''
        
        # Check if it's a Bluetooth device
        if 'BTHENUM' in hwid:
            # Extract MAC fragment from HWID
            frag = hwid.split('&')[-1].split('_')[0].lower()
            if int(frag, 16) == 0:
                continue

            # Match user-friendly name from registry
            name = friendly.get(frag, desc)

            # Only return HC-05/HC-06
            if 'ROBOAIHUB' in name.upper() or 'HC-05' in name.upper():
                results.append((p.device, f"{p.device} - {name} (Bluetooth)"))
        # Check if it's an Arduino
        elif 'USB' in hwid and ('Arduino Uno' in desc or 'CH340' in desc):
            results.append((p.device, f"{p.device} - {desc} (USB)"))
    
    return results