import board
import busio
from adafruit_tca9548a import TCA9548A
import logging
import time

logger = logging.getLogger(__name__)

def init_i2c(retries: int = 3, delay: float = 0.1) -> TCA9548A:
    """
    Initialisiert den I2C-Bus und den TCA9548A-Multiplexer mit Retry-Logik.

    Args:
        retries (int): Anzahl der Versuche, den I2C-Bus zu sperren.
        delay (float): Wartezeit (Sekunden) zwischen den Versuchen.

    Returns:
        TCA9548A: Instanz des I2C-Multiplexers.

    Raises:
        RuntimeError: Wenn der I2C-Bus oder der Multiplexer nicht initialisiert werden kann.
    """
    logger.info("Initialisiere I2C-Bus und TCA9548A-Multiplexer")

    # I2C-Bus initialisieren
    i2c = _create_i2c_bus()

    # I2C-Bus sperren
    _try_lock_i2c(i2c, retries, delay)

    # Geräte scannen (Debug-Zweck)
    _scan_i2c_devices(i2c)

    # Multiplexer initialisieren
    tca = _create_multiplexer(i2c)

    # Bus freigeben
    _unlock_i2c(i2c)

    return tca

def _create_i2c_bus():
    try:
        return busio.I2C(board.SCL, board.SDA)
    except Exception as e:
        logger.error("I2C-Bus konnte nicht initialisiert werden", exc_info=True)
        raise RuntimeError("I2C-Bus Initialisierung fehlgeschlagen") from e

def _try_lock_i2c(i2c, retries, delay):
    for attempt in range(1, retries + 1):
        try:
            if i2c.try_lock():
                logger.debug(f"I2C-Bus gesperrt (Versuch {attempt})")
                return
        except Exception as e:
            logger.warning(f"I2C try_lock fehlgeschlagen (Versuch {attempt})", exc_info=True)
        time.sleep(delay)
    logger.error(f"Timeout: I2C-Bus konnte nach {retries} Versuchen nicht gesperrt werden")
    raise RuntimeError("I2C-Bus kann nicht gesperrt werden")

def _scan_i2c_devices(i2c):
    try:
        addresses = i2c.scan()
        if addresses:
            logger.debug(f"Gefundene I2C-Geräte: {[hex(addr) for addr in addresses]}")
        else:
            logger.warning("Keine I2C-Geräte gefunden. Verkabelung prüfen.")
    except Exception as e:
        logger.warning("Fehler beim Scannen der I2C-Geräte", exc_info=True)

def _create_multiplexer(i2c):
    try:
        tca = TCA9548A(i2c)
        logger.info("TCA9548A-Multiplexer erfolgreich initialisiert")
        return tca
    except Exception as e:
        logger.error("Multiplexer-Initialisierung fehlgeschlagen", exc_info=True)
        raise RuntimeError("Multiplexer-Initialisierung fehlgeschlagen") from e

def _unlock_i2c(i2c):
    try:
        i2c.unlock()
        logger.debug("I2C-Bus entsperrt")
    except Exception:
        logger.debug("I2C-Bus Unlock fehlgeschlagen, möglicherweise nicht gesperrt.")
