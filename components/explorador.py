from shiny import ui
import duckdb
import pandas as pd
from utils.config import db_name

def panel_explorador():
    conn = duckdb.connect(database=db_name, read_only=True)
    min_date, max_date = conn.execute(
        "SELECT min(date), max(date) FROM lecturas"
    ).fetchone()
    conn.close()

    min_date_dt = pd.to_datetime(min_date)
    max_date_dt = pd.to_datetime(max_date)
    start_last_year_dt = max(
        max_date_dt - pd.DateOffset(years=1) + pd.Timedelta(days=1),
        min_date_dt,
    )

    return ui.nav_panel(
        "Explorador con pull",
        ui.input_date_range(
            "fechas",
            "Fechas:",
            start=str(start_last_year_dt.date()),
            end=str(max_date_dt.date()),
            min=str(min_date_dt.date()),
            max=str(max_date_dt.date()),
            language="es",
            separator="a",
        ),
        ui.output_plot("plot_explorer"),
        ui.div(
            ui.download_button(
                "dl_parquet",
                "Download parquet",
            ),
            ui.download_button(
                "dl_csv",
                "Download csv",
            ),
            class_="d-flex justify-content-center gap-1 "
        ),
    )


def panel_estadistica():
    return ui.nav_panel(
        "Estadística",
        "Aquí irá tu contenido estadístico"    )
