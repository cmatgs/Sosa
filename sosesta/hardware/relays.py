import logging
import time
import RPi.GPIO as GPIO
from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class RelayController:
    """
    Steuerung von Relais über GPIO mit Index-Überprüfung, Debounce und sauberem Cleanup.
    Verfolgt zusätzlich intern den Status jedes Relais (an/aus).
    """
    def __init__(self, config: ConfigManager, debounce: float = 0.05):
        self.pins = config.config.relais_pins
        self.debounce = debounce
        self.states = [False] * len(self.pins)

        GPIO.setmode(GPIO.BCM)
        for pin in self.pins:
            try:
                GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
                logger.info(f"Relay-Pin {pin} als Ausgang initialisiert")
            except Exception as e:
                logger.error(f"Fehler beim Setup des Relay-Pins {pin}: {e}", exc_info=True)

    def toggle_relay(self, index: int, state: bool = None) -> None:
        if index < 0 or index >= len(self.pins):
            logger.error(f"Ungültiger Relay-Index: {index}")
            return
        pin = self.pins[index]
        try:
            current = GPIO.input(pin)
            if state is None:
                new_state = not current
            else:
                new_state = GPIO.HIGH if state else GPIO.LOW
            GPIO.output(pin, new_state)
            self.states[index] = (new_state == GPIO.HIGH)
            logger.debug(f"Relay {index} (Pin {pin}) auf {'ON' if new_state else 'OFF'} gesetzt")
        except Exception as e:
            logger.error(f"Fehler beim Schalten von Relay {index} (Pin {pin}): {e}", exc_info=True)

    def toggle_all(self, state: bool = None) -> None:
        for idx in range(len(self.pins)):
            self.toggle_relay(idx, state)
            time.sleep(self.debounce)
        logger.info("Alle Relais geschaltet")

    def turn_all_on(self) -> None:
        for idx, pin in enumerate(self.pins):
            try:
                GPIO.output(pin, GPIO.HIGH)
                self.states[idx] = True
                logger.debug(f"Relay {idx} (Pin {pin}) auf ON gesetzt")
                time.sleep(self.debounce)
            except Exception as e:
                logger.error(f"Fehler beim Einschalten von Relay {idx} (Pin {pin}): {e}", exc_info=True)
        logger.info("Alle Relais eingeschaltet")

    def get_state(self, index: int) -> bool:
        if 0 <= index < len(self.states):
            return self.states[index]
        logger.warning(f"get_state: Ungültiger Index {index}")
        return False

    def cleanup(self) -> None:
        for pin in self.pins:
            try:
                GPIO.output(pin, GPIO.LOW)
                GPIO.cleanup(pin)
                logger.info(f"GPIO-Pin {pin} aufgeräumt")
            except Exception as e:
                logger.warning(f"Fehler beim Cleanup von Pin {pin}: {e}", exc_info=True)
