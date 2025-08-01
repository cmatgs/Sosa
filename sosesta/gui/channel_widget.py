import tkinter as tk
from tkinter import ttk

class ChannelWidget(ttk.LabelFrame):
    def __init__(self, master, channel: int, app):
        super().__init__(master, text=f"Kanal {channel+1}")
        self.channel = channel
        self.app = app

        self.led_canvas = tk.Canvas(self, width=20, height=20)
        self.led_circle = self.led_canvas.create_oval(2, 2, 18, 18, fill="gray")
        self.led_canvas.pack(anchor="w", pady=2)

        self.current_lbl = ttk.Label(self, text="Strom: 0.00 mA")
        self.voltage_lbl = ttk.Label(self, text="Spannung: 0.00 V")
        self.redlab_lbl = ttk.Label(self, text="RedLab: 0.00 V")
        self.relay_lbl = ttk.Label(self, text="Relais: OFF")
        self.status_lbl = ttk.Label(self, text="Status: --", foreground="gray")

        for lbl in [self.current_lbl, self.voltage_lbl, self.redlab_lbl, self.relay_lbl, self.status_lbl]:
            lbl.pack(anchor="w")

        ttk.Label(self, text="Seriennummer:").pack(anchor="w")
        self.sn_entry = ttk.Entry(self)
        self.sn_entry.pack(fill="x")
        self._was_present = False

    def update_from_data(self, data):
        # Grunddaten anzeigen
        self.current_lbl.config(text=f"Strom: {data.current:.2f} mA")
        self.voltage_lbl.config(text=f"Spannung: {data.bus_voltage:.2f} V")
        self.redlab_lbl.config(text=f"RedLab: {data.redlab_signal:.2f} V")
        self.relay_lbl.config(text=f"Relais: {'ON' if self.app.hardware.relays.get_state(data.channel) else 'OFF'}")

        # Zustandslogik – klare Reihenfolge
        if not data.present:
            status = "Kein Sensor erkannt"
            color = "gray"
        elif not data.supply_ok:
            status = "Versorgung fehlerhaft"
            color = "purple"
        elif data.signal_ok:
            status = "OK"
            color = "green"
        elif data.redlab_signal != 0:
            status = "Warnung"
            color = "orange"
        else:
            status = "Fehler"
            color = "red"

        # Statusanzeige
        self.status_lbl.config(text=f"Status: {status}", foreground=color)
        self.led_canvas.itemconfig(self.led_circle, fill=color)

        # Seriennummer einmalig bei Erkennung übernehmen und sperren
        if data.present and not self._was_present:
            self.app.serial_numbers[data.channel] = self.sn_entry.get()
            self.sn_entry.config(state="disabled")

        # Merker aktualisieren
        self._was_present = data.present


    def disable_serial_input(self):
        self.sn_entry.config(state="disabled")
