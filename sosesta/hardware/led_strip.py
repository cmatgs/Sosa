import logging
import time
from rpi_ws281x import PixelStrip, Color

logger = logging.getLogger(__name__)

# Farb-Presets
LED_COLORS = {
    'ok': Color(0, 255, 0),          # grün
    'warning': Color(255, 165, 0),   # orange
    'error': Color(255, 0, 0),       # rot
    'unknown': Color(64, 0, 128),    # violett/dunkelblau
    'off': Color(0, 0, 0),
}

class LEDStripController:
    """
    Steuerung eines WS281x-LED-Streifens mit Einzel-LED-Zugriff, Farbpreset-Logik und robustem Fehlerhandling.
    """
    def __init__(
        self,
        num_pixels: int,
        pin: int,
        channel: int = 0,
        freq_hz: int = 800000,
        dma: int = 10,
        brightness: int = 255,
        invert: bool = False
    ):
        self.num_pixels = num_pixels

        try:
            self.strip = PixelStrip(
                num_pixels,
                pin,
                freq_hz=freq_hz,
                dma=dma,
                invert=invert,
                brightness=brightness,
                channel=channel
            )
            self.strip.begin()
            logger.info(f"LED-Streifen initialisiert: {num_pixels} Pixel, Pin {pin}, Kanal {channel}")
        except Exception as e:
            logger.error(f"LED-Streifen Initialisierung fehlgeschlagen: {e}", exc_info=True)
            self.strip = None

    def set_color(self, index: int, status: str) -> None:
        """
        Setzt eine einzelne LED auf eine vordefinierte Statusfarbe.

        Args:
            index: LED-Index (0-basiert)
            status: Einer der Schlüssel in LED_COLORS ('ok', 'warning', 'error', 'unknown')
        """
        if not self.strip:
            logger.warning("LED-Streifen nicht initialisiert")
            return
        if not 0 <= index < self.num_pixels:
            logger.warning(f"Ungültiger LED-Index: {index}")
            return

        color = LED_COLORS.get(status, LED_COLORS['unknown'])
        self.strip.setPixelColor(index, color)

    def update(self) -> None:
        """
        Zeigt den aktuellen Zustand aller LEDs an (flush).
        """
        if not self.strip:
            logger.warning("LED-Streifen nicht initialisiert – update abgebrochen")
            return
        try:
            self.strip.show()
            logger.debug("LED-Streifen aktualisiert (show)")
        except Exception as e:
            logger.error(f"Fehler beim LED-Update: {e}", exc_info=True)

    def clear(self) -> None:
        """
        Schaltet alle LEDs aus.
        """
        if not self.strip:
            return
        try:
            for i in range(self.num_pixels):
                self.strip.setPixelColor(i, LED_COLORS['off'])
            self.strip.show()
            logger.info("LED-Streifen gelöscht (alle Pixel OFF)")
        except Exception as e:
            logger.error(f"Fehler beim Löschen des LED-Streifens: {e}", exc_info=True)

    def cleanup(self) -> None:
        """
        Cleanup: löscht den Streifen und setzt alle LEDs auf aus.
        """
        self.clear()
