from shiny import reactive, render, ui
from shinywidgets import render_widget
from utils.sun_path import calcular_posicion_solar, figura_cartesiana, figura_estereografica


def sun_path_server(input, output, session):
    DAYS = [
        '2025-01-21', '2025-02-21', '2025-03-21',
        '2025-04-21', '2025-05-21', '2025-06-21', '2025-12-21'
    ]

    @reactive.calc
    def datos():
        usar_hora_solar = input.horario() == "solar"
        return calcular_posicion_solar(
            input.lat(),
            input.lon(),
            tz=input.timezone(),
            usar_hora_solar=usar_hora_solar,
            fechas=DAYS,
        )

    @output
    @render_widget
    def grafico_cartesiano():
        return figura_cartesiana(
            datos(),
            input.lat(),
            input.lon(),
            tz=input.timezone(),
            usar_hora_solar=input.horario() == "solar",
        )

    @output
    @render_widget
    def grafico_polar():
        return figura_estereografica(
            datos(),
            input.lat(),
            input.lon(),
            tz=input.timezone(),
            usar_hora_solar=input.horario() == "solar",
        )

    @output
    @render.ui
    def grafico_activo():
        if input.tipo_graf() == "Cartesiano":
            return ui.output_widget("grafico_cartesiano")
        else:
            return ui.output_widget("grafico_polar")

    @output
    @render.download(
        filename="trayectoria_solar.csv", media_type="text/csv"
    )
    def descargar_datos():
        yield datos().to_csv(index=True)
    
