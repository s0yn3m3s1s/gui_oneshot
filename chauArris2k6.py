import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import csv
import time
import os
from manuf import manuf

# =========================
# CONFIG
# =========================
INTERFAZ = "wlan1"
INTERFAZ_MON = "wlan1"

parser = manuf.MacParser()

scan_process = None
scan_activo = False

# =========================
# LOG CONSOLA
# =========================
def log(msg):
    salida_text.insert(tk.END, msg + "\n")
    salida_text.see(tk.END)


# =========================
# EJECUTAR COMANDOS
# =========================
def ejecutar_comando(cmd):

    try:
        proceso = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for linea in proceso.stdout:
            log(linea.strip())

    except Exception as e:
        log(f"Error: {e}")


# =========================
# MODO MONITOR
# =========================
def modo_monitor():

    def run():
        log("[+] Activando modo monitor...")
        ejecutar_comando(["airmon-ng", "start", INTERFAZ])

    threading.Thread(target=run, daemon=True).start()


# =========================
# DETENER MONITOR
# =========================
def detener_monitor():

    def run():
        log("[+] Deteniendo modo monitor...")
        ejecutar_comando(["airmon-ng", "stop", INTERFAZ_MON])

    threading.Thread(target=run, daemon=True).start()


# =========================
# ESCANEAR REDES
# =========================
def escanear_redes():

    global scan_process
    global scan_activo

    scan_activo = True

    redes_tree.delete(*redes_tree.get_children())

    archivo = "scan"

    if os.path.exists("scan-01.csv"):
        os.remove("scan-01.csv")

    log("[+] Iniciando escaneo...")

    scan_process = subprocess.Popen([
        "airodump-ng",
        INTERFAZ_MON,
        "--write", archivo,
        "--output-format", "csv"
    ])

    def leer_csv():

        while scan_activo:

            time.sleep(2)

            if not os.path.exists("scan-01.csv"):
                continue

            try:
                with open("scan-01.csv", newline='', encoding="utf-8") as f:

                    reader = csv.reader(f)

                    redes_tree.delete(*redes_tree.get_children())

                    leyendo = False

                    for fila in reader:

                        if len(fila) > 0 and fila[0] == "BSSID":
                            leyendo = True
                            continue

                        if leyendo and fila[0] == "":
                            break

                        if leyendo and len(fila) > 13:

                            bssid = fila[0]
                            canal = fila[3]
                            power = fila[8]
                            enc = fila[5]
                            essid = fila[13]

                            fabricante = parser.get_manuf(bssid)

                            redes_tree.insert(
                                "",
                                "end",
                                values=(bssid, fabricante, canal, power, enc, essid)
                            )

            except:
                pass

    threading.Thread(target=leer_csv, daemon=True).start()


# =========================
# DETENER ESCANEO
# =========================
def detener_scan():

    global scan_process
    global scan_activo

    scan_activo = False

    if scan_process:
        scan_process.terminate()
        scan_process = None

    log("[+] Escaneo detenido")


# =========================
# PRUEBA AUTORIZADA (HOOK)
# =========================
def prueba_autorizada():

    seleccion = redes_tree.focus()

    if not seleccion:
        messagebox.showwarning("Aviso", "Selecciona una red")
        return

    valores = redes_tree.item(seleccion, "values")

    bssid = valores[0]
    essid = valores[2]

    log(f"[+] Iniciando prueba autorizada contra: {essid}")
    log(f"[+] BSSID: {bssid}")

    # Cerrar cualquier ventana modal activa
    try:
        root.focus()
    except:
        pass

    # Ejecutar herramienta externa
    def ejecutar_tool():

        try:
            comando = [
                "python3",
                "script_auditoria.py",
                INTERFAZ_MON,
                bssid
            ]

            proceso = subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for linea in proceso.stdout:
                log(linea.strip())

            log("[+] Proceso finalizado")

        except Exception as e:
            log(f"Error: {e}")

    threading.Thread(target=ejecutar_tool, daemon=True).start()



# =========================
# GUI
# =========================
root = tk.Tk()
root.title("WiFi Lab Tool - Raspberry Pi")
root.geometry("950x550")

# -------- BOTONES --------
frame_botones = tk.Frame(root)
frame_botones.pack(pady=5)

tk.Button(frame_botones, text="Modo Monitor",
          command=modo_monitor).pack(side="left", padx=5)

tk.Button(frame_botones, text="Detener Monitor",
          command=detener_monitor).pack(side="left", padx=5)

tk.Button(frame_botones, text="Escanear Redes",
          command=escanear_redes).pack(side="left", padx=5)

tk.Button(frame_botones, text="Detener Scan",
          command=detener_scan).pack(side="left", padx=5)

tk.Button(frame_botones, text="Prueba Autorizada",
          command=prueba_autorizada).pack(side="left", padx=5)


# -------- TABLA --------
columnas = ("BSSID", "Fabricante", "Canal", "Señal", "Cifrado", "ESSID")

redes_tree = ttk.Treeview(root, columns=columnas, show="headings")

for col in columnas:
    redes_tree.heading(col, text=col)

redes_tree.pack(fill="x", padx=10, pady=5)


# -------- CONSOLA --------
salida_text = tk.Text(root, height=15)
salida_text.pack(fill="both", expand=True, padx=10, pady=5)

root.mainloop()
