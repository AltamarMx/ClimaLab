from shiny import ui

def panel_explorador():
    return ui.nav_panel(
        "Explorador",
        ui.input_date_range(
            "fechas",
            "Fechas:",
            start="2023-01-01",
            end="2023-12-31",
            min="2010-01-01",
            max="2025-12-31",
            language="es",
            separator="a",
        ),
        ui.output_plot("plot_explorer"),
        ui.div(
            ui.download_button(
                "dl_parquet",
                "Descargar Parquet",
                class_="btn btn-outline-primary me-2",
            ),
            ui.download_button(
                "dl_csv",
                "Descargar CSV",
                class_="btn btn-outline-primary",
            ),
            class_="mt-3",
        ),
    )


def panel_estadistica():
    return ui.nav_panel(
        "Estadística",
        "Aquí irá tu contenido estadístico"    )
