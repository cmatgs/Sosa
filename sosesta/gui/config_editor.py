import tkinter as tk
from tkinter import ttk, messagebox
import ast  # sicherer als eval

def open_config_editor(parent_tab):
    cfg = parent_tab.app.config.config  # Muss Attribut-basiertes Objekt sein

    win = tk.Toplevel()
    win.title("Konfiguration bearbeiten")
    win.geometry("500x300")
    win.grab_set()

    entries = {}

    def add_row(label, attr_name):
        frame = ttk.Frame(win)
        frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(frame, text=label).pack(side="left")
        try:
            val = getattr(cfg, attr_name)
        except AttributeError:
            val = ""
        var = tk.StringVar(value=str(val))
        ent = ttk.Entry(frame, textvariable=var)
        ent.pack(side="right", fill="x", expand=True)
        entries[attr_name] = var

    fields = [
        ("Testdauer [h]", "test_duration"),
        ("PosSchwelle [V, V]", "redlab_pos_threshold"),
        ("NegSchwelle [V, V]", "redlab_neg_threshold"),
        ("Präsenzstrom [mA, mA]", "presence_current_threshold"),
        ("Versorgungsspannung [V, V]", "supply_voltage_threshold")
    ]

    for label, attr_name in fields:
        add_row(label, attr_name)

    def parse_value(text):
        try:
            return ast.literal_eval(text)
        except Exception:
            return text  # Als Fallback ein String

    def save():
        try:
            for attr, var in entries.items():
                val = parse_value(var.get())
                setattr(cfg, attr, val)
            parent_tab.config_label.config(
                text=(
                    f"Dauer: {cfg.test_duration} h    "
                    f"PosSchwelle: {cfg.redlab_pos_threshold} V    "
                    f"NegSchwelle: {cfg.redlab_neg_threshold} V    "
                    f"Präsenzstrom: {cfg.presence_current_threshold} mA    "
                    f"Versorgung: {cfg.supply_voltage_threshold} V"
                )
            )
            messagebox.showinfo("Gespeichert", "Änderungen übernommen.")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Fehler", f"Ungültiger Wert: {e}")

    ttk.Button(win, text="Speichern", command=save).pack(pady=10)
