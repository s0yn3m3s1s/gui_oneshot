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
# LOG SEGURO
# =========================
def log(msg):
    salida_text.after(0, lambda: (
        salida_text.insert(tk.END, msg + "\n"),
        salida_text.see(tk.END)
    ))

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

def detener_monitor():
    def run():
        log("[+] Deteniendo modo monitor...")
        ejecutar_comando(["airmon-ng", "stop", INTERFAZ_MON])
    threading.Thread(target=run, daemon=True).start()

# =========================
# ESCANEAR REDES
# =========================
def escanear_redes():
    global scan_process, scan_activo

    scan_activo = True
    redes_tree.delete(*redes_tree.get_children())

    if os.path.exists("scan-01.csv"):
        os.remove("scan-01.csv")

    log("[+] Iniciando escaneo...")

    scan_process = subprocess.Popen([
        "airodump-ng",
        INTERFAZ_MON,
        "--write", "scan",
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
                    nuevas_redes = []
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
                            essid = fila[13]

                            fabricante = parser.get_manuf(bssid)

                            nuevas_redes.append(
                                (fabricante, essid, canal, power)
                            )

                    actualizar_tabla(nuevas_redes)

            except:
                pass

    threading.Thread(target=leer_csv, daemon=True).start()

def actualizar_tabla(redes):
    def update():
        redes_tree.delete(*redes_tree.get_children())
        for red in redes:
            redes_tree.insert("", "end", values=red)
    root.after(0, update)

# =========================
# DETENER ESCANEO
# =========================
def detener_scan():
    global scan_process, scan_activo

    scan_activo = False

    if scan_process:
        scan_process.terminate()
        scan_process = None

    log("[+] Escaneo detenido")

# =========================
# PRUEBA AUTORIZADA
# =========================
def prueba_autorizada():
    seleccion = redes_tree.focus()

    if not seleccion:
        messagebox.showwarning("Aviso", "Selecciona una red")
        return

    valores = redes_tree.item(seleccion, "values")

    fabricante = valores[0]
    essid = valores[1]

    log(f"[+] Iniciando prueba contra: {essid}")
    log(f"[+] Fabricante: {fabricante}")

    def ejecutar_tool():
        try:
            proceso = subprocess.Popen(
                ["python3", "script_auditoria.py", INTERFAZ_MON],
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
# GUI 480x320 TFT
# =========================
ANCHO = 480
ALTO = 320

root = tk.Tk()
root.title("WiFi Lab Tool")
root.geometry(f"{ANCHO}x{ALTO}")
root.resizable(False, False)
root.configure(bg="#111111")

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview",
                background="#222222",
                foreground="white",
                fieldbackground="#222222",
                rowheight=18)
style.map("Treeview", background=[("selected", "#4444aa")])

FUENTE_BTN = ("Arial", 9, "bold")
FUENTE_CONSOLA = ("Courier", 7)

# -------- BOTONES --------
frame_top = tk.Frame(root, bg="#111111")
frame_top.pack(fill="x", pady=2)

tk.Button(frame_top, text="Monitor", font=FUENTE_BTN,
          height=2, bg="#0044aa", fg="white",
          command=modo_monitor).grid(row=0, column=0, sticky="ew")

tk.Button(frame_top, text="Stop Mon", font=FUENTE_BTN,
          height=2, bg="#aa0000", fg="white",
          command=detener_monitor).grid(row=0, column=1, sticky="ew")

tk.Button(frame_top, text="Escanear", font=FUENTE_BTN,
          height=2, bg="#007700", fg="white",
          command=escanear_redes).grid(row=1, column=0, sticky="ew")

tk.Button(frame_top, text="Stop Scan", font=FUENTE_BTN,
          height=2, bg="#aa7700", fg="white",
          command=detener_scan).grid(row=1, column=1, sticky="ew")

tk.Button(frame_top, text="Auditar", font=FUENTE_BTN,
          height=2, bg="#333333", fg="white",
          command=prueba_autorizada).grid(row=2, column=0, columnspan=2, sticky="ew")

frame_top.columnconfigure(0, weight=1)
frame_top.columnconfigure(1, weight=1)

# -------- TABLA --------
columnas = ("Fabricante", "ESSID", "Canal", "Señal")

redes_tree = ttk.Treeview(root, columns=columnas,
                          show="headings", height=5)

redes_tree.column("Fabricante", width=140)
redes_tree.column("ESSID", width=140)
redes_tree.column("Canal", width=60)
redes_tree.column("Señal", width=60)

for col in columnas:
    redes_tree.heading(col, text=col)

redes_tree.pack(fill="x", padx=5, pady=3)

# -------- CONSOLA --------
salida_text = tk.Text(root, height=6,
                      font=FUENTE_CONSOLA,
                      bg="black", fg="lime")
salida_text.pack(fill="both", expand=True, padx=5, pady=3)

root.mainloop()

