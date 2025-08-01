"""
Hardware-Modul: Abstraktion für Sensoren, Relais, LED-Strip und DAQ.
"""
from .hardware_manager import HardwareManager
from .ina219 import INA219SensorManager
from .tca import init_i2c, TCA9548A
from .relays import RelayController
from .led_strip import LEDStripController
from .redlab import RedLabDAQ
from .sensors import SensorManager, SensorData

__all__ = [
    "HardwareManager",
    "INA219SensorManager",
    "init_i2c",
    "TCA9548A",
    "RelayController",
    "LEDStripController",
    "RedLabDAQ",
    "SensorManager",
    "SensorData",
]
