import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import time
import os
import csv
import manuf

# =========================
# CONFIGURACIÓN
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
    log(f"[+] Fabricante: {fabricante}")

    def ejecutar_tool():
        try:
            comando = [
                "python3",
                "script_auditoria.py",
                INTERFAZ_MON,
                essid
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
# GUI MINIMAL 240x320
# =========================
ANCHO = 240
ALTO = 320

root = tk.Tk()
root.geometry("240x320")
root.overrideredirect(True)
root.configure(bg="#000000")
root.config(cursor="none")

def salir(event=None):
    root.destroy()

root.bind("<Control-Alt-q>", salir)

# ---------- ESTILO ----------
style = ttk.Style()
style.theme_use("default")

style.configure("Treeview",
                background="#111111",
                foreground="white",
                fieldbackground="#111111",
                rowheight=18,
                font=("Arial", 7))

style.map("Treeview",
          background=[("selected", "#333333")])

FUENTE_BTN = ("Arial", 8)
FUENTE_CONSOLA = ("Courier", 7)

# ---------- BOTONES ----------
frame_btn = tk.Frame(root, bg="#000000")
frame_btn.pack(fill="x")

def crear_boton(texto, comando):
    return tk.Button(frame_btn,
                     text=texto,
                     font=FUENTE_BTN,
                     height=1,
                     bg="#222222",
                     fg="white",
                     bd=0,
                     activebackground="#333333",
                     command=comando)

crear_boton("MON", modo_monitor).pack(fill="x", padx=3, pady=2)
crear_boton("STOP MON", detener_monitor).pack(fill="x", padx=3, pady=2)
crear_boton("SCAN", escanear_redes).pack(fill="x", padx=3, pady=2)
crear_boton("STOP SCAN", detener_scan).pack(fill="x", padx=3, pady=2)
crear_boton("AUDIT", prueba_autorizada).pack(fill="x", padx=3, pady=2)

# ---------- TABLA ----------
columnas = ("FAB", "ESSID")

redes_tree = ttk.Treeview(root,
                          columns=columnas,
                          show="headings",
                          height=6)

redes_tree.heading("FAB", text="FAB")
redes_tree.heading("ESSID", text="ESSID")

redes_tree.column("FAB", width=90, anchor="center")
redes_tree.column("ESSID", width=140, anchor="w")

redes_tree.pack(fill="x", padx=3, pady=4)

# ---------- CONSOLA ----------
salida_text = tk.Text(root,
                      height=5,
                      font=FUENTE_CONSOLA,
                      bg="#000000",
                      fg="#00ff00",
                      insertbackground="white",
                      bd=0)

salida_text.pack(fill="both", expand=True, padx=3, pady=3)

root.mainloop()

