


import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import csv
import os
import time
import manuf

# =========================
# CONFIG
# =========================
INTERFAZ = "wlan0"
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
        log("[+] Activando monitor...")
        ejecutar_comando(["sudo", "airmon-ng", "start", INTERFAZ])
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

    log("[+] Escaneando...")

    scan_process = subprocess.Popen([
        "sudo",
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
                            essid = fila[13]
                            fabricante = parser.get_manuf(bssid)

                            redes_tree.insert(
                                "",
                                "end",
                                values=(fabricante, essid, bssid)
                            )

            except:
                pass

    threading.Thread(target=leer_csv, daemon=True).start()


# =========================
# DETENER SCAN
# =========================
def detener_scan():
    global scan_process
    global scan_activo

    scan_activo = False

    if scan_process:
        scan_process.terminate()
        scan_process = None

    log("[+] Scan detenido")


# =========================
# PRUEBA AUTORIZADA (ATACAR)
# =========================
def prueba_autorizada():

    seleccion = redes_tree.focus()

    if not seleccion:
        messagebox.showwarning("Aviso", "Selecciona una red")
        return

    valores = redes_tree.item(seleccion, "values")

    fabricante = valores[0]
    essid = valores[1]
    bssid = valores[2]

    log(f"[+] Iniciando prueba contra: {essid}")
    log(f"[+] BSSID: {bssid}")

    def ejecutar_tool():
        try:
            comando = [
                "sudo",
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
root.title("WiFi Lab")
root.geometry("240x320")
root.configure(bg="#111111")
root.resizable(False, False)

# -------- BOTONES --------
frame_botones = tk.Frame(root, bg="#111111")
frame_botones.pack(fill="x", pady=2)

btn_style = {
    "font": ("Helvetica", 7, "bold"),
    "height": 1,
    "width": 10,
    "bd": 0
}

tk.Button(frame_botones, text="MON",
          bg="#00BCD4", fg="white",
          command=modo_monitor, **btn_style).pack(pady=1)

tk.Button(frame_botones, text="SCAN",
          bg="#4CAF50", fg="white",
          command=escanear_redes, **btn_style).pack(pady=1)

tk.Button(frame_botones, text="STOP",
          bg="#F44336", fg="white",
          command=detener_scan, **btn_style).pack(pady=1)

tk.Button(frame_botones, text="ATACAR",
          bg="#FF9800", fg="white",
          command=prueba_autorizada, **btn_style).pack(pady=1)

# -------- TABLA PEQUEÑA --------
frame_tabla = tk.Frame(root)
frame_tabla.pack(fill="x", pady=2)

columnas = ("Fabricante", "ESSID", "BSSID")

redes_tree = ttk.Treeview(
    frame_tabla,
    columns=columnas,
    show="headings",
    height=4
)

redes_tree.heading("Fabricante", text="FAB")
redes_tree.heading("ESSID", text="ESSID")
redes_tree.heading("BSSID", text="")  # Oculto

redes_tree.column("Fabricante", width=85)
redes_tree.column("ESSID", width=135)
redes_tree.column("BSSID", width=0, stretch=False)

redes_tree.pack(fill="x")

# -------- LOGS (MITAD INFERIOR) --------
frame_logs = tk.Frame(root)
frame_logs.pack(fill="both", expand=True)

salida_text = tk.Text(
    frame_logs,
    bg="black",
    fg="lime",
    font=("Courier", 7)
)

salida_text.pack(fill="both", expand=True)

root.mainloop()
