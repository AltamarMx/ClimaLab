from shiny import ui
from shinywidgets import output_widget

def panel_explorador():
    return ui.nav_panel(
        "Explorador",
        output_widget("plot_resampler"),
        ui.tags.script(
            """
            document.addEventListener('shiny:connected', () => {
              const plotDiv = document.querySelector('#plot_resampler .js-plotly-plot');
              if (!plotDiv) return;
              plotDiv.on('plotly_relayout', (e) => {
                const start = e['xaxis.range[0]'];
                const end = e['xaxis.range[1]'];
                if (start && end) {
                  Shiny.setInputValue('fechas', [start.slice(0, 10), end.slice(0, 10)], {priority: 'event'});
                }
              });
            });
            """
        ),
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
