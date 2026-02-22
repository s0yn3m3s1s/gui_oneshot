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
INTERFAZ_MON = "wlan1"
INTERFAZ = "wlan1"

parser = manuf.MacParser()

scan_process = None
scan_activo = False

# =========================
# GUI CONFIG (TFT 2.8" 320x480)
# =========================
ANCHO = 320
ALTO = 480

root = tk.Tk()
root.title("WiFi Lab Tool")

# KIOSK REAL
root.attributes("-fullscreen", True)
root.overrideredirect(True)
root.config(cursor="none")
root.configure(bg="#111111")

def salir_kiosk(event=None):
    root.destroy()

root.bind("<Control-Alt-q>", salir_kiosk)

# =========================
# ESTILOS
# =========================
style = ttk.Style()
style.theme_use("default")

style.configure("Treeview",
                background="#222222",
                foreground="white",
                fieldbackground="#222222",
                rowheight=22,
                font=("Arial", 9))

style.map("Treeview",
          background=[("selected", "#4444aa")])

FUENTE_BTN = ("Arial", 10, "bold")
FUENTE_CONSOLA = ("Courier", 8)

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
                            essid = fila[13]

                            fabricante = parser.get_manuf(bssid)

                            redes_tree.insert(
                                "",
                                "end",
                                values=(fabricante, essid)
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

    log(f"[+] Iniciando prueba autorizada contra: {essid}")

    def ejecutar_tool():
        try:
            comando = [
                "python3",
                "script_auditoria.py",
                INTERFAZ_MON
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
# BOTONES VERTICALES TÁCTILES
# =========================
frame_botones = tk.Frame(root, bg="#111111")
frame_botones.pack(fill="x", pady=5)

botones = [
    ("Monitor", "#0044aa", modo_monitor),
    ("Stop Mon", "#aa0000", detener_monitor),
    ("Escanear", "#007700", escanear_redes),
    ("Stop Scan", "#aa7700", detener_scan),
    ("Auditar", "#333333", prueba_autorizada)
]

for texto, color, comando in botones:
    tk.Button(frame_botones,
              text=texto,
              font=FUENTE_BTN,
              height=2,
              bg=color,
              fg="white",
              bd=0,
              activebackground=color,
              command=comando).pack(fill="x", padx=10, pady=3)

# =========================
# TABLA (Fabricante | ESSID)
# =========================
columnas = ("Fabricante", "ESSID")

redes_tree = ttk.Treeview(root,
                          columns=columnas,
                          show="headings",
                          height=9)

redes_tree.heading("Fabricante", text="Fabricante")
redes_tree.heading("ESSID", text="ESSID")

redes_tree.column("Fabricante", width=140, anchor="center")
redes_tree.column("ESSID", width=160, anchor="w")

redes_tree.pack(fill="both", expand=True, padx=5, pady=5)

# =========================
# CONSOLA ESTILO TERMINAL
# =========================
salida_text = tk.Text(root,
                      height=6,
                      font=FUENTE_CONSOLA,
                      bg="black",
                      fg="lime",
                      insertbackground="white")

salida_text.pack(fill="x", padx=5, pady=5)

root.mainloop()
