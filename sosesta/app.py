#!/usr/bin/env python3
import tkinter as tk

from config.config_manager import ConfigManager
from hardware.hardware_manager import HardwareManager
from gui.main_tab import MainTab


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sonnenscheinsensor Prüfstand")

        # Fensterrahmen entfernen und Bildschirmgröße setzen
        self.overrideredirect(True)
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.geometry(f"{self.screen_width}x{self.screen_height}+0+0")

        # Tastaturfokus setzen und Escape binden
        self.focus_force()
        self.bind_all("<Escape>", self.exit_fullscreen)

        # Config & Hardware
        self.config = ConfigManager()
        self.serial_numbers = {i: "" for i in range(8)}
        self.hardware = HardwareManager(self.config, self)

        # MainTab direkt anzeigen
        self.main_tab = MainTab(self, self)
        self.main_tab.pack(fill="both", expand=True)

    def exit_fullscreen(self, event=None):
        self.overrideredirect(False)
        self.geometry("1200x800")  # Standardgröße nach Verlassen


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
