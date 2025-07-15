from shiny import ui
import duckdb
import pandas as pd
from utils.config import db_name
from utils.config import mean_year_name
from shinywidgets import output_widget


def panel_explorador():
    conn = duckdb.connect(database=db_name, read_only=True)
    min_date, max_date = conn.execute(
        "SELECT min(date), max(date) FROM lecturas"
    ).fetchone()
    conn.close()

    min_date_dt = pd.to_datetime(min_date)
    max_date_dt = pd.to_datetime(max_date)
    start_last_year_dt = max(
        max_date_dt - pd.DateOffset(days=120) + pd.Timedelta(days=1),
        min_date_dt,
    )
    
    # Texto informativo (puedes cambiar h6→p, span, etc.)
    info_rango = ui.h6(
        f"Datos disponibles de {min_date_dt.date()} al {max_date_dt.date()}",
        class_="text-muted mb-2 text-center"   # opcional: gris y peque-ño margen inferior
    )
    return ui.nav_panel(
        "Explorador",
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
        ui.hr(),
        info_rango,
        ui.hr(),
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
        output_widget("plot_mean_year"),
    )
