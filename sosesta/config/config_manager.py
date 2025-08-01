from pathlib import Path
import json
import logging
from deepmerge import always_merger
from typing import Optional
from .constants import ConfigSchema

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = ConfigSchema()

class ConfigManager:
    """
    Lädt, validiert und speichert die Anwendungskonfiguration.

    Args:
        filepath: Pfad zur JSON-Konfigurationsdatei. Wenn sie nicht existiert,
                  werden die Default-Werte verwendet.
    """
    def __init__(self, filepath: Optional[Path] = None) -> None:
        self.filepath: Path = filepath or Path("config/config.json")
        self.config: ConfigSchema = DEFAULT_CONFIG
        self._load_config()

    def _load_config(self) -> None:
        """
        Intern: Liest die JSON-Datei ein, merged sie rekursiv mit den Defaults
        und validiert das Ergebnis anhand des Pydantic-Schemas.
        """
        if not self.filepath.exists():
            logger.warning("Konfigurationsdatei %s nicht gefunden, verwende Default-Werte", self.filepath)
            return
        try:
            raw = json.loads(self.filepath.read_text(encoding="utf-8"))
            merged = always_merger.merge(self.config.dict(), raw)
            self.config = ConfigSchema(**merged)
            logger.info("Konfiguration geladen und validiert von %s", self.filepath)
        except json.JSONDecodeError:
            logger.error("Konfigurationsdatei %s fehlerhaft formatiert, verwende Default-Werte", self.filepath)
        except Exception as e:
            logger.exception("Unerwarteter Fehler beim Laden der Konfiguration: %s", e)

    def save_config(self) -> None:
        """
        Speichert die aktuelle Konfiguration im JSON-Format zurück in die Datei.
        Erzeugt ggf. fehlende Verzeichnisse.
        """
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            text = self.config.json(indent=2, ensure_ascii=False)
            self.filepath.write_text(text, encoding="utf-8")
            logger.info("Konfiguration in %s gespeichert", self.filepath)
        except Exception as e:
            logger.exception("Fehler beim Speichern der Konfiguration: %s", e)
