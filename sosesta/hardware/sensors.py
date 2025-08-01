import logging
from dataclasses import dataclass, field
from typing import List, Dict
from hardware.ina219 import INA219SensorManager
from hardware.redlab import RedLabDAQ
from hardware.relays import RelayController
from hardware.led_strip import LEDStripController

logger = logging.getLogger(__name__)

@dataclass
class SensorData:
    channel: int
    # INA219 Messwerte
    bus_voltage: float = 0.0  # Versorgungsspannung in V
    current: float = 0.0      # Stromaufnahme in mA
    power: float = 0.0        # Leistung in mW
    # Redlab-Sensorstatus
    redlab_signal: float = 0.0  # Redlab-Signal in V

    # Statusinformationen
    present: bool = False     # Sensor-Präsenz
    supply_ok: bool = False   # Versorgung ok
    supply_error_counter: int = 0  # Zähler für Versorgungsspannungsfehler
    signal_ok: bool = False   # Redlab-Signal ok
    signal_error_counter: int = 0  # Zähler für Redlab-Signalfehler

    # Zusätzliche Informationen
    serial_number: str = field(default="")  # Seriennummer aus Dashboardeingabefeld

class SensorManager:
    def __init__(self, channels: List[int], ina_manager: INA219SensorManager, redlab_manager: RedLabDAQ, relay_controller: RelayController, led_controller: LEDStripController, dashboard):
        self.channels = channels
        self.ina_manager = ina_manager
        self.redlab_manager = redlab_manager
        self.relay_controller = relay_controller
        self.led_controller = led_controller
        self.dashboard = dashboard
        self.config = dashboard.config.config  # für Zugriff auf Thresholds
        self.sensors: Dict[int, SensorData] = {ch: SensorData(channel=ch) for ch in channels}

    def update_sensor(self, channel: int) -> None:
        """
        Liest Messwerte von INA219 und RedLab, prüft Status, zählt Fehler und aktualisiert LED.
        """
        sensor = self.sensors[channel]
        try:
            relay_state = self.relay_controller.get_state(channel)

            # INA219 Messwerte lesen
            bus_v, current, power = self.ina_manager.read(channel)
            sensor.bus_voltage = bus_v if bus_v is not None else 0.0
            sensor.current = current if current is not None else 0.0
            sensor.power = power if power is not None else 0.0

            # RedLab-Signal lesen
            redlab_signal = self.redlab_manager.read(channel)
            sensor.redlab_signal = redlab_signal if redlab_signal is not None else 0.0

            # Thresholds entpacken
            pos_min, pos_max = getattr(self.config, "redlab_pos_threshold", (2.0, 4.0))
            neg_min, neg_max = getattr(self.config, "redlab_neg_threshold", (-4.0, -2.0))
            pres_min, pres_max = getattr(self.config, "getpresence_current_threshold", (1.3, 1.6))
            v_min, v_max = getattr(self.config, "getsupply_voltage_threshold", (4.2, 5.5))

            # Signalprüfung abhängig vom Relaiszustand
            if relay_state:
                sensor.signal_ok = pos_min < sensor.redlab_signal < pos_max
            else:
                sensor.signal_ok = neg_min < sensor.redlab_signal < neg_max

            if not sensor.signal_ok:
                sensor.signal_error_counter += 1

            # Präsenzprüfung über Stromaufnahme im Leerlaufbereich
            sensor.present = pres_min <= sensor.current <= pres_max

            # Versorgungsspannung prüfen
            sensor.supply_ok = v_min <= sensor.bus_voltage <= v_max
            if not sensor.supply_ok:
                sensor.supply_error_counter += 1

            # Seriennummer übernehmen
            sensor.serial_number = self.dashboard.serial_numbers.get(channel, "")

            # LED-Status setzen
            if not sensor.present or not sensor.supply_ok:
                status = "unknown"
            elif sensor.signal_ok:
                status = "ok"
            elif sensor.redlab_signal != 0:
                status = "warning"
            else:
                status = "error"

            self.led_controller.set_color(channel, status)

            logger.debug(f"Sensor {channel} aktualisiert: {sensor}")
        except Exception:
            logger.error(f"Fehler beim Aktualisieren von Sensor {channel}", exc_info=True)

    def update_all(self) -> None:
        """
        Bulk-Update: alle Sensoren nacheinander aktualisieren.
        """
        logger.info("Starte Bulk-Update aller Sensoren")
        for ch in self.channels:
            self.update_sensor(ch)
        self.led_controller.update()
        logger.info("Bulk-Update abgeschlossen")

    def get_all_data(self) -> List[SensorData]:
        """
        Gibt die aktuelle Liste aller SensorData-Objekte zurück.
        """
        return list(self.sensors.values())
