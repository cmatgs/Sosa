import logging
import time
from typing import Optional
from uldaq import (
    get_daq_device_inventory,
    DaqDevice,
    InterfaceType,
    AiInputMode,
    Range,
    AInFlag
)

logger = logging.getLogger(__name__)

class RedLabDAQ:
    """
    Verwalter für RedLab DAQ-Gerät mittels UL-DAQ Bibliothek.
    Bietet Connect/Read/Disconnect mit Fehlerbehandlung und optionalem Reconnect.
    """
    def __init__(self, reconnect_retries: int = 3, reconnect_delay: float = 0.5):
        self.daq_device: Optional[DaqDevice] = None
        self.ai_device = None
        self.reconnect_retries = reconnect_retries
        self.reconnect_delay = reconnect_delay

    def connect(self) -> None:
        """
        Stellt Verbindung zum ersten verfügbaren DAQ-Gerät her.

        Raises:
            RuntimeError: Wenn kein Gerät gefunden oder Verbindung fehlschlägt.
        """
        devices = get_daq_device_inventory(InterfaceType.USB)
        logger.debug(f"Gefundene DAQ-Geräte: {devices}")

        if not devices:
            logger.error("Kein RedLab DAQ-Gerät gefunden")
            raise RuntimeError("Kein RedLab DAQ-Gerät gefunden")

        for attempt in range(1, self.reconnect_retries + 1):
            try:
                self._try_connect_once(devices[0])
                logger.info(f"RedLab DAQ erfolgreich verbunden (Versuch {attempt})")
                return
            except Exception as e:
                logger.warning(f"Verbindungsversuch {attempt} fehlgeschlagen: {e}", exc_info=True)
                time.sleep(self.reconnect_delay)

        logger.error("RedLab DAQ konnte nicht verbunden werden")
        raise RuntimeError("RedLab DAQ-Verbindung fehlgeschlagen")

    def _try_connect_once(self, descriptor):
        self.daq_device = DaqDevice(descriptor)
        self.ai_device = self.daq_device.get_ai_device()
        self.daq_device.connect()

    def read(self, channel: int) -> Optional[float]:
        """
        Liest den analogen Wert (V) von einem spezifischen Kanal.
        Versucht bei fehlender Verbindung, einmal neu zu verbinden.

        Args:
            channel: Kanalnummer (0-basierend).

        Returns:
            Gemessene Spannung in Volt oder None bei Fehler.
        """
        if self.ai_device is None:
            logger.warning("AI-Gerät nicht verbunden – versuche Reconnect")
            try:
                self.connect()
            except RuntimeError:
                return None

        try:
            value = self.ai_device.a_in(
                channel,
                AiInputMode.SINGLE_ENDED,
                Range.BIP10VOLTS,
                AInFlag.DEFAULT
            )
            logger.debug(f"RedLab Kanal {channel}: {value:.3f} V")
            return value
        except Exception as e:
            logger.error(f"Fehler beim Lesen von RedLab-Kanal {channel}: {e}", exc_info=True)
            return None

    def is_connected(self) -> bool:
        return self.daq_device is not None and self.ai_device is not None

    def disconnect(self) -> None:
        """
        Trennt die Verbindung zum DAQ-Gerät.
        """
        if self.ai_device:
            try:
                self.ai_device.disconnect()
                logger.info("AI-Device getrennt")
            except Exception as e:
                logger.warning(f"Fehler beim Trennen des AI-Devices: {e}", exc_info=True)

        if self.daq_device:
            try:
                self.daq_device.disconnect()
                logger.info("DAQ-Gerät getrennt")
            except Exception as e:
                logger.warning(f"Fehler beim Trennen des DAQ-Geräts: {e}", exc_info=True)
