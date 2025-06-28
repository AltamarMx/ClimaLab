import numpy as np

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
longitude = -100
gmt = -6
name = 'ClimaLab'
min_year = 2001

# Solar constant in W/m² used for irradiance quality checks
solar_constant = 1361

