import os
import csv
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from gui.channel_widget import ChannelWidget

CHANNEL_COUNT = 8

class MainTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.channel_widgets = {}
        self.test_running = False
        self.test_start_time = None
        self.test_duration_secs = int(self.app.config.config.test_duration)
        self.csv_writers = {}
        self.csv_files = {}

        self._build_ui()
        self._update_loop()

    def _build_ui(self):
        self._build_config_display()
        self._build_channels()
        self._build_error_display()
        self._build_controls()

    def _build_config_display(self):
        cfg = self.app.config.config
        frame = ttk.LabelFrame(self, text="Aktuelle Konfiguration")
        frame.pack(fill="x", padx=10, pady=5)

        text = (
            f"Dauer: {cfg.test_duration} h    "
            f"PosSchwelle: {cfg.redlab_pos_threshold} V    "
            f"NegSchwelle: {cfg.redlab_neg_threshold} V    "
            f"Präsenzstrom: {cfg.presence_current_threshold} mA    "
            f"Versorgung: {cfg.supply_voltage_threshold} V"
        )
        self.config_label = ttk.Label(frame, text=text)
        self.config_label.pack(side="left", padx=10)

        self.edit_btn = ttk.Button(frame, text="⚙️ Schwellen bearbeiten", command=self._open_config_editor)
        self.edit_btn.pack(side="right", padx=10)

    def _build_channels(self):
        grid = ttk.Frame(self)
        grid.pack(padx=10, pady=10, fill="both", expand=True)

        for i in range(CHANNEL_COUNT):
            row, col = divmod(i, 4)
            widget = ChannelWidget(grid, channel=i, app=self.app)
            widget.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.channel_widgets[i] = widget

    def _build_error_display(self):
        self.error_frame = ttk.LabelFrame(self, text="Fehlerübersicht")
        self.error_frame.pack(fill="x", padx=10, pady=5)
        self.error_text = tk.Text(self.error_frame, height=2, state="disabled", background="#f8f8f8")
        self.error_text.pack(fill="x", padx=5, pady=5)

    def _build_controls(self):
        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", padx=10, pady=10)

        self.toggle_btn = ttk.Button(ctrl, text="🔁 Relais toggeln", command=self._toggle_relays)
        self.start_btn = ttk.Button(ctrl, text="▶️ Start Test", command=self._start_test)
        self.stop_btn = ttk.Button(ctrl, text="⏹ Stop Test", command=self._stop_test, state="disabled")
        self.archive_btn = ttk.Button(ctrl, text="📂 Archiv öffnen", command=self._open_archive_folder)
        self.timer_label = ttk.Label(ctrl, text="00:00:00")

        self.toggle_btn.pack(side="left", padx=5)
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn.pack(side="left", padx=5)
        self.archive_btn.pack(side="left", padx=5)
        self.timer_label.pack(side="right", padx=5)

    def _open_archive_folder(self):
        path = str(self.app.config.config.archive_path)
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", os.path.normpath(path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Fehler", f"Ordner konnte nicht geöffnet werden: {e}")

    def _toggle_relays(self):
        if not messagebox.askyesno("Sicherheitsabfrage", "Relais manuell toggeln? Nur bei Bedarf."):
            return
        self.app.hardware.relays.toggle_all()

    def _start_test(self):
        self.test_running = True
        self.test_start_time = datetime.now()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.toggle_btn.config(state="disabled")
        self.archive_btn.config(state="disabled")
        for w in self.channel_widgets.values():
            w.disable_serial_input()
        self.app.hardware.relays.turn_all_on()
        self._init_csv()

    def _stop_test(self):
        self.test_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.toggle_btn.config(state="normal")
        self.archive_btn.config(state="normal")
        for f in self.csv_files.values():
            f.close()

    def _update_loop(self):
        self.app.hardware.update_sensors()
        self._update_channels()
        self._update_errors()
        self._update_timer()
        if self.test_running:
            self._save_csv()
        self.after(self.app.config.config.update_interval, self._update_loop)

    def _update_channels(self):
        for i, w in self.channel_widgets.items():
            data = self.app.hardware.sensor_manager.sensors[i]
            w.update_from_data(data)

    def _update_errors(self):
        lines = []
        for i, s in self.app.hardware.sensor_manager.sensors.items():
            if not s.present:
                lines.append(f"Kanal {i+1}: Sensor nicht erkannt")
            elif not s.supply_ok:
                lines.append(f"Kanal {i+1}: Versorgungsspannung außerhalb Toleranz")
            elif not s.signal_ok:
                lines.append(f"Kanal {i+1}: RedLab-Signal ungültig")
        self.error_text.config(state="normal")
        self.error_text.delete("1.0", "end")
        self.error_text.insert("end", "\n".join(lines))
        self.error_text.config(state="disabled")

    def _update_timer(self):
        if not self.test_running or not self.test_start_time:
            self.timer_label.config(text="00:00:00")
            return
        elapsed = datetime.now() - self.test_start_time
        remaining = max(timedelta(seconds=self.test_duration_secs) - elapsed, timedelta(seconds=0))
        self.timer_label.config(text=str(remaining).split(".")[0])
        if remaining.total_seconds() <= 0:
            self._stop_test()

    def _init_csv(self):
        self.csv_files.clear()
        self.csv_writers.clear()
        base_path = self.app.config.config.archive_path
        os.makedirs(base_path, exist_ok=True)
        timestamp = self.test_start_time.strftime("%Y-%m-%d_%H%M%S")
        cfg = self.app.config.config.dict()

        for i in range(CHANNEL_COUNT):
            sn = self.app.serial_numbers[i] or f"Kanal{i+1}"
            folder = os.path.join(base_path, sn)
            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, f"{timestamp}_{sn}.csv")
            f = open(filepath, mode="w", newline="")
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["ConfigSnapshot:", cfg])
            writer.writerow(["Timestamp","Relay","RedLab [V]","Current [mA]","Bus [V]","Status","SN","Kanal","SupplyErrors","SignalErrors"])
            self.csv_files[i] = f
            self.csv_writers[i] = writer

    def _save_csv(self):
        now = datetime.now().isoformat()
        for i, data in self.app.hardware.sensor_manager.sensors.items():
            relay_state = "ON" if self.app.hardware.relays.get_state(i) else "OFF"
            row = [
                now, relay_state, 
                f"{data.redlab_signal:.2f}", 
                f"{data.current:.2f}",
                f"{data.bus_voltage:.2f}", 
                "OK" if data.signal_ok else "FEHLER",
                data.serial_number, str(i+1),
                str(data.supply_error_counter), 
                str(data.signal_error_counter)
            ]
            try:
                self.csv_writers[i].writerow(row)
            except Exception as e:
                print(f"CSV-Fehler Kanal {i+1}: {e}")

    def _open_config_editor(self):
        from gui.config_editor import open_config_editor
        open_config_editor(self)
