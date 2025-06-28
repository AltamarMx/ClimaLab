import pandas as pd
import numpy as np
from .validations import detect_radiation
from .config import (
    variables,
    latitude,
    longitude,
    gmt,
    name,
    min_year,
    variables_types,
    solar_constant,
)
from typing import Dict


names = variables.keys()
names

ALLOWED_VARS = list(variables.values())
MIN_YEAR = 2010

def load_csv(filepath: str) -> pd.DataFrame:
    """
    Read a raw logger CSV, apply basic cleaning, and return a tidy DataFrame.

    Parameters
    ----------
    filepath : str | pathlib.Path
        Path to the CSV file.

    Returns
    -------
    pandas.DataFrame
        DataFrame indexed by local timestamps and containing one
        column per meteorological variable.

    Notes
    -----
    * Timestamps are **local time** (no UTC conversion).
    * Relies on four module-level constants: ``names``, ``variables``,
      ``variable_types``, and ``min_year``.
    """

    # 1️  Read file — skip device-metadata rows, keep only desired columns,
    #     parse first column as DatetimeIndex (local time).
    df = pd.read_csv(
        filepath,
        skiprows=[0, 2, 3],    # rows with logger headers / units
        usecols=names,         # raw column names or positions
        parse_dates=True,
        index_col=0,
        dayfirst=False,
    )

    # 2️  Rename raw logger headers to canonical names (e.g. 'WS[m/s]' → 'ws').
    df.rename(columns=variables, inplace=True)

    # 3️  Drop records earlier than the minimum year allowed.
    df = df[df.index.year >= min_year]

    # 4️  Enforce expected dtypes (all numeric variables to float64, etc.).
    df = df.astype(variables_types, errors="raise")

    # 5️  Remove duplicate timestamps and duplicate full rows.
    df = df[~df.index.duplicated(keep="first")]
    df = df.drop_duplicates()

    # 6️  Ensure chronological order.
    df.sort_index(inplace=True)

    return df


def run_tests(df: pd.DataFrame ) -> dict:
    """
    Run a minimal data quality suite on *df* and return one Boolean per test.

    Tests performed
    ---------------
    • **No NaT**           there are no NaT values in any datetime column.  
    • **No duplicates**    the DataFrame contains no duplicate rows.  
    • **Column types**     every numeric column is float64 (except TIMESTAMP).

    Parameters
    ----------
    df : pandas.DataFrame
        The data to validate.
    filepath : str
        Path of the source file (currently only passed through; retained in
        case you later add extension or encoding checks).

    Returns
    -------
    dict
        ``{"No NaT": bool, "No duplicates": bool, "Column types": bool}``
        – *True* means the test passed.
    """

    # ------------------------------------------------------------------
    # Helper 1 – NaT detector
    # ------------------------------------------------------------------
    def _detect_nats(df_: pd.DataFrame) -> bool:
        """Return True if **no** NaT values are present in datetime columns."""
        dt_cols = df_.select_dtypes(include=["datetime64[ns]", "datetimetz"])
        return not dt_cols.isna().any().any()

    # ------------------------------------------------------------------
    # Helper 2 – duplicate-row detector
    # ------------------------------------------------------------------
    def _detect_duplicates(df_: pd.DataFrame) -> bool:
        """Return True if the DataFrame contains no duplicate rows."""
        return not df_.duplicated().any()

    # ------------------------------------------------------------------
    # Helper 3 – dtype checker
    # ------------------------------------------------------------------
    def _detect_dtype( data_: pd.DataFrame) -> bool:
        """
        Verify that every column in *expected* has the dtype specified there.
        Columns not mentioned in *expected* are ignored.
        """
        for col, exp in variables_types.items():
            if col not in data_.columns:
                raise KeyError(f"Column '{col}' is missing from the DataFrame.")
            if str(data_[col].dtype) != exp:
                return False
        return True


    nats_ok  = _detect_nats(df)
    dups_ok  = _detect_duplicates(df)
    dtype_ok = _detect_dtype(df)

    # ------------------------------------------------------------------
    # 3) Return aggregated result
    # ------------------------------------------------------------------
    return {
        "No NaT":        nats_ok,
        "No duplicates": dups_ok,
        "Column types":  dtype_ok,
    }



def export_data(filepath: str) -> pd.DataFrame:
    """
    Prepara DF en formato largo para carga en BD:
      - usa load_csv para obtener DataFrame limpio en forma ancha
      - convierte TIMESTAMP a string 'YYYY-MM-DD HH:MM:SS'
      - melt a ['fecha','variable','valor']
      - garantiza tipo float en 'valor'
    """
    # 1. cargar
    df = load_csv(filepath)

    # 2. resetear índice para tener TIMESTAMP como columna
    df = df.reset_index()

    # 3. convertir la fecha a string
    df['TIMESTAMP'] = df['TIMESTAMP'].dt.strftime('%Y-%m-%d %H:%M')

    # 4. transformar a formato largo
    long_df = df.melt(
        id_vars=['TIMESTAMP'],
        var_name='variable',
        value_name='valor'
    )
    long_df.columns = ['fecha', 'variable', 'valor']

    # 5. limpiar duplicados y asegurar tipo float
    long_df.drop_duplicates(subset=['fecha', 'variable'], inplace=True)
    long_df['valor'] = long_df['valor'].astype(float)

    return long_df


def radiacion(df: pd.DataFrame, rad_columns=None) -> pd.DataFrame:
    """
    Extrae datos de radiación durante la noche (altura solar ≤ 0):
      - calcula la altitud solar
      - devuelve sólo columnas de radiación y 'altura_solar'
    """
    # 1. calcular altura solar (agrega columnas auxiliares)
    df_radiacion = detect_radiation(df)

    # 2. renombrar columna a español
    df_radiacion.rename(columns={'solar_altitude': 'altura_solar'}, inplace=True)

    # 3. determinar columnas de radiación
    rad_cols = ["dni", "ghi", "dhi", "uv"]
    default_cols = [variables.get(c, c) for c in rad_cols]
    columnas = rad_columns or default_cols
    columnas = [c for c in columnas if c in df_radiacion.columns]
    if not columnas:
        raise KeyError("No se encontraron columnas de radiación válidas en el DataFrame.")

    # 4. filtrar registros nocturnos
    mask_noche = df_radiacion['altura_solar'] <= 0
    resultado = df_radiacion.loc[mask_noche, columnas + ['altura_solar']].copy()

    # 7. redondear altitud solar
    resultado['altura_solar'] = resultado['altura_solar'].round(2)

    return resultado


def clean_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Clean irradiance data using solar geometry and flag extreme values.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame indexed by timestamp and containing irradiance columns.

    Returns
    -------
    pandas.DataFrame
        The input DataFrame with extra columns ``solar_altitude`` and
        ``outlier``. Irradiance values during nighttime are set to ``NaN``.
    """

    # 1. compute solar altitude for each timestamp
    df = detect_radiation(df)

    # 2. set irradiance to NaN when the sun is below the horizon
    irr_cols = [c for c in ["dni", "ghi", "dhi"] if c in df.columns]
    if irr_cols:
        night = df["solar_altitude"] < 0
        df.loc[night, irr_cols] = np.nan

        # 3. mark outliers beyond the solar constant
        df["outlier"] = df[irr_cols].gt(solar_constant).any(axis=1)
    else:
        df["outlier"] = False

    return df


# def _df_nans(df: pd.DataFrame, filepath: str) -> pd.DataFrame:
#     # 1. Calcula offset según skiprows
#     csv_opts   = _detect_csv(filepath)
#     skip_count = len(csv_opts["skiprows"]) - 1
#     offset     = skip_count + 3  # +2 líneas de cabecera +1 para 1-based

#     # 2. Encuentra los NaN en columnas no datetime
#     non_dt = df.select_dtypes(exclude=["datetime64[ns]", "datetimetz"]).columns
#     mask   = df[non_dt].isna()
#     nans   = mask.stack()[lambda s: s]

#     # 3. Si no hay NaN, devuelve mensaje
#     if nans.empty:
#         return pd.DataFrame({"Info": ["No se encontró ningún NaN en las columnas de datos."]})

#     # 4. Reconstruye posiciones y aplica offset
#     loc = nans.reset_index()
#     loc.columns      = ["Fila_idx", "Columna", "is_nan"]
#     loc["fila_original"] = loc["Fila_idx"] + offset

#     # 5. Devuelve sólo fila y columna
#     return (
#         loc[["fila_original", "Columna"]]
#         .rename(columns={"fila_original": "Fila"})
#     )


# def _df_nats(df: pd.DataFrame) -> pd.DataFrame:
#     # 1. Encuentra NaT en columnas datetime
#     datetime_cols = df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns
#     mask          = df[datetime_cols].isna()
#     nats          = mask.stack()[lambda s: s]

#     # 2. Si no hay NaT, devuelve mensaje
#     if nats.empty:
#         return pd.DataFrame({"Info": ["No se encontró ningún NaT en la estampa temporal."]})

#     # 3. Reconstruye posiciones
#     loc = nats.reset_index()
#     loc.columns = ["Fila", "Columna", "is_nat"]

#     # 4. Devuelve sólo la fila original
#     return loc[["Fila"]]
