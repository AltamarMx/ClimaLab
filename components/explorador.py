from shiny import ui

def panel_explorador():
    return ui.nav_panel(
        "Explorador",
        ui.input_date_range(
            "fechas",
            "Fechas:",
            start="2023-01-01",
            end="2025-12-31",
            min="2010-01-01",
            max="2030-12-31",
            language="es",
            separator="a",
        ),
        ui.output_plot("plot_explorer"),
        ui.div(
            ui.download_button(
                "dl_parquet",
                "Download parquet",
                # class_="btn btn-outline-primary",
            ),
            ui.download_button(
                "dl_csv",
                "Download csv",
                # class_="btn btn-outline-primary",
            ),
            class_="d-flex justify-content-center gap-1 "
        ),
    )


def panel_estadistica():
    return ui.nav_panel(
        "Estadística",
        "Aquí irá tu contenido estadístico"    )
