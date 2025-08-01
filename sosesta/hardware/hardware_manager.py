import logging
from config.config_manager import ConfigManager
from hardware.tca import init_i2c
from hardware.ina219 import INA219SensorManager
from hardware.redlab import RedLabDAQ
from hardware.relays import RelayController
from hardware.led_strip import LEDStripController
from hardware.sensors import SensorManager

logger = logging.getLogger(__name__)

class HardwareManager:
    """
    Zentrale Klasse für alle Hardware-Komponenten mit robustem Fehlerhandling und zentraler Konfiguration.
    """
    def __init__(self, config: ConfigManager, app):
        """
        Args:
            config: ConfigManager mit allen Hardware-Parametern.
            app: Haupt-Anwendungsobjekt (für Dashboard, serial_numbers).
        """
        self.config = config
        self.app = app
        self.relays = RelayController(config)

        try:
            self._initialize_hardware()
            channels = self.config.config.sensor_channels
            self.sensor_manager = SensorManager(
                channels=channels,
                ina_manager=self.ina219,
                redlab_manager=self.redlab,
                relay_controller=self.relays,
                led_controller=self.led_strip,
                dashboard=self.app
            )
            self.update_sensors(initial=True)
            logger.info("HardwareManager erfolgreich initialisiert")
        except Exception as e:
            logger.error(f"HardwareManager-Initialisierung fehlgeschlagen: {e}", exc_info=True)
            raise

    def _initialize_hardware(self):
        """
        Initialisiert I2C, Multiplexer, INA219, RedLab und LED-Streifen mit Konfigurationsparametern.
        """
        i2c_cfg = self.config.config.i2c
        self.tca = init_i2c(
            retries=i2c_cfg["retries"],
            delay=i2c_cfg["delay"]
        )

        ina_cfg = self.config.config.ina219
        self.ina219 = INA219SensorManager(
            multiplexer=self.tca,
            calibration=ina_cfg["calibration"],
            retries=ina_cfg["retries"],
            retry_delay=ina_cfg["retry_delay"]
        )

        red_cfg = self.config.config.redlab
        self.redlab = RedLabDAQ(
            reconnect_retries=red_cfg["reconnect_retries"],
            reconnect_delay=red_cfg["reconnect_delay"]
        )
        self.redlab.connect()

        led_cfg = self.config.config.led
        self.led_strip = LEDStripController(
            num_pixels=led_cfg["count"],
            pin=led_cfg["pin"],
            channel=led_cfg["channel"],
            freq_hz=led_cfg["freq_hz"],
            dma=led_cfg["dma"],
            brightness=led_cfg["brightness"],
            invert=led_cfg["invert"]
        )

        logger.info("I2C, Multiplexer, INA219, RedLab und LED-Streifen initialisiert")

    def update_sensors(self, initial: bool = False) -> None:
        """
        Bulk-Update aller Sensorwerte und Aktualisierung von self.sensor_data.
        """
        self.sensor_manager.update_all()
        self.sensor_data = self.sensor_manager.get_all_data()
        level = logging.INFO if initial else logging.DEBUG
        logger.log(level, "Sensor-Daten aktualisiert")

    def read_ina(self, channel: int):
        """Liest einmalig von INA219 auf dem gegebenen Kanal."""
        return self.ina219.read(channel)

    def read_redlab(self, channel: int):
        """Liest einmalig von RedLab DAQ auf dem gegebenen Kanal."""
        return self.redlab.read(channel)

    def cleanup(self) -> None:
        """Trennt alle Verbindungen und räumt Ressourcen für alle Hardware-Komponenten auf."""
        try:
            self.redlab.disconnect()
        except Exception as e:
            logger.warning(f"Fehler beim Trennen von RedLab DAQ: {e}", exc_info=True)

        try:
            self.relays.cleanup()
        except Exception as e:
            logger.warning(f"Fehler beim Cleanup der Relais: {e}", exc_info=True)

        try:
            self.led_strip.clear()
        except Exception as e:
            logger.warning(f"Fehler beim Löschen des LED-Streifens: {e}", exc_info=True)

        logger.info("Hardware-Ressourcen freigegeben")
