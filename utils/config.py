import numpy as np
from pathlib import Path

variables = {
    "TIMESTAMP":"timestamp",
    "I_dir_Avg": "dni",
    "I_glo_Avg": "ghi",
    "I_dif_Avg": "dhi",
    "I_uv_Avg": "uv",
    "AirTC_Avg": "tdb",
    "RH": "rh",
    "WS_ms_Avg": "ws",
    "WindDir": "wd",
    "CS106_PB_Avg": "p_atm",
    "Rain_mm_Tot": "rain_acc"
    }

variables_types = {
    "dni":  "float64",
    "ghi":  "float64",
    "dhi":  "float64",
    "uv":   "float64",
    "tdb":  "float64",
    "rh":   "float64",
    "ws":   "float64",
    "wd":   "float64",
    "p_atm": "float64",
    "rain_acc": "float64",
} 

latitude = 18.5
longitude = -99
gmt = -6
name = 'ClimaLab'
min_year = 2001
mean_year = 2025


# Solar constant in W/m² used for irradiance quality checks
solar_constant = 1361

# Drop outliers before saving in database 
drop_outliers = True

# Resolve project root so paths work regardless of the current working
# directory.  ``config.py`` lives inside ``utils/`` therefore the root is the
# parent directory of this file.
_ROOT = Path(__file__).resolve().parent.parent

# Database name
db_name = str(_ROOT / 'ClimaLab.db')
mean_year_name = str(_ROOT / 'database' / 'mean-year.parquet')
site_id = 2226728
data_tz = -6 
# — Alturas de medición (en metros) para cada variable —
wind_speed_height       = 50 
air_temperature_height  = 50
air_pressure_height     = 50
