import logging
import time
from typing import Optional, Tuple, Dict
import adafruit_ina219

logger = logging.getLogger(__name__)

class INA219SensorManager:
    """
    Verwalter mehrerer INA219-Sensoren über einen TCA9548A-Multiplexer
    mit konfigurierbarer Kalibrierung und Retry-Logik.

    Args:
        multiplexer: Instanz des TCA9548A-Multiplexers.
        calibration: Kalibrierungsprofil ('16V_400mA' oder '32V_2A').
        retries: Anzahl Leseversuche pro Kanal.
        retry_delay: Wartezeit (Sekunden) zwischen den Versuchen.
    """
    def __init__(
        self,
        multiplexer,
        calibration: str = '16V_400mA',
        retries: int = 3,
        retry_delay: float = 0.1
    ):
        self.tca = multiplexer
        self.calibration = calibration
        self.retries = retries
        self.retry_delay = retry_delay
        self.sensors: Dict[int, adafruit_ina219.INA219] = {}

    def _apply_calibration(self, sensor: adafruit_ina219.INA219) -> None:
        if self.calibration == '16V_400mA':
            sensor.set_calibration_16V_400mA()
        elif self.calibration == '32V_2A':
            sensor.set_calibration_32V_2A()
        else:
            logger.warning(f"Unbekanntes Kalibrierungsprofil '{self.calibration}', verwende 16V_400mA")
            sensor.set_calibration_16V_400mA()

    def _init_sensor(self, channel: int) -> None:
        try:
            mux = self.tca[channel]
            sensor = adafruit_ina219.INA219(mux)
            self._apply_calibration(sensor)
            self.sensors[channel] = sensor
            logger.info(f"INA219 Kanal {channel} initialisiert mit Profil {self.calibration}")
        except Exception as e:
            logger.error(f"Fehler bei Initialisierung von INA219 Kanal {channel}: {e}", exc_info=True)
            raise

    def read(self, channel: int) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Liest Spannung (V), Strom (mA) und Leistung (mW) vom gegebenen Multiplexer-Kanal.
        Führt bei Fehlern bis zu 'retries' Versuche durch.

        Returns:
            Tuple[bus_voltage, current, power] oder (None, None, None) bei dauerhaften Fehlern.
        """
        for attempt in range(1, self.retries + 1):
            try:
                # Prüfen ob Kanal existiert
                if channel not in range(8):
                    logger.error(f"Ungültiger INA219-Kanal {channel}")
                    return None, None, None

                mux = self.tca[channel]
                if not mux:
                    logger.warning(f"Multiplexer-Kanal {channel} nicht erreichbar (Versuch {attempt})")
                    time.sleep(self.retry_delay)
                    continue

                # Sensor ggf. initialisieren
                if channel not in self.sensors:
                    self._init_sensor(channel)

                sensor = self.sensors[channel]
                bus_v = sensor.bus_voltage
                cur = sensor.current
                pwr = sensor.power

                logger.debug(
                    f"INA219 Kanal {channel}: bus={bus_v:.3f} V, current={cur:.3f} mA, power={pwr:.3f} mW"
                )
                return bus_v, cur, pwr

            except Exception as e:
                logger.warning(f"Fehler beim Lesen INA219 Kanal {channel}, Versuch {attempt}: {e}", exc_info=True)
                time.sleep(self.retry_delay)

        logger.error(f"INA219 Kanal {channel} konnte nach {self.retries} Versuchen nicht gelesen werden")
        return None, None, None
