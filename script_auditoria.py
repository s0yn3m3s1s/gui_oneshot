# script_auditoria.py
import sys
import time
import os

iface = sys.argv[1]
bssid = sys.argv[2]

print(f"Interfaz: {iface}")
print(f"Objetivo: {bssid}")

os.system(f"python3 oneshot.py -i wlan1 -b {bssid} -K")

print("Auditoría finalizada")