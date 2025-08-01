from pydantic import BaseModel
from typing import Optional, Dict, List, Tuple, Union

class ConfigSchema(BaseModel):
    test_duration: float = 1000.0
    redlab_pos_threshold: Tuple[float, float] = (2.0, 5.0)
    redlab_neg_threshold: Tuple[float, float] = (-5.0, -2.0)
    presence_current_threshold: Tuple[float, float] = (1.3, 1.6)
    supply_voltage_threshold: Tuple[float, float] = (4.2, 5.5)
    sensor_channels: List[int] = list(range(8))

    # Neue Felder für Hardware-Unterkonfigurationen:
    i2c: Dict[str, Union[int, float]] = {
        "retries": 3,
        "delay": 0.1
    }

    ina219: Dict[str, Union[str, int, float]] = {
        "calibration": "16V_400mA",
        "retries": 3,
        "retry_delay": 0.1
    }

    redlab: Dict[str, Union[int, float]] = {
        "reconnect_retries": 3,
        "reconnect_delay": 0.5
    }

    led: Dict[str, Union[int, bool]] = {
        "pin": 10,
        "channel": 0,
        "count": 8,
        "freq_hz": 800000,
        "dma": 10,
        "brightness": 255,
        "invert": False
    }

    relais_pins: List[int] = [14, 15, 18, 23]
    archive_path: str = "./archive"
    update_interval: int = 500
