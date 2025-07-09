from shiny import ui
from shinywidgets import output_widget

def panel_explorador():
    return ui.nav_panel(
        "Explorador",
        ui.input_date_range(
            "fechas",
            "Fechas:",
            start="2023-11-01",
            end="2025-12-31",
            min="2010-01-01",
            max="2025-12-31",
            language="es",
            separator="a",
        ),
        output_widget("plot_resampler"),
    )


def panel_estadistica():
    return ui.nav_panel(
        "Estadística",
        "Aquí irá tu contenido estadístico"    )
