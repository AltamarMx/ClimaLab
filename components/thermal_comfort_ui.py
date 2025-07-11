from shiny import ui
import pandas as pd
import duckdb
from utils.config import db_name

con = duckdb.connect(db_name)
df = con.execute("SELECT * FROM lecturas").fetchdf()
con.close()

df_ancho = df.pivot(index='date', columns='variable', values='value')
df_ancho.index = pd.to_datetime(df_ancho.index)


# Rellenar fechas default al cargar panel
fecha_min = df_ancho.index.min().date()
fecha_max = df_ancho.index.max().date()




def panel_confort():
    return ui.nav_panel(
        "Confort térmico",
        ui.tags.head(
            ui.tags.meta(name="viewport", content="width=device-width, initial-scale=1"),
            ui.tags.style("""
                .responsive-container, .ddh-container, 
                .heatmap-container, .utci-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                    margin-bottom: 20px;
                }
                .controls-card, .ddh-controls, 
                .heatmap-controls, .utci-controls {
                    flex: 1 1 400px;
                    min-width: 300px;
                }
                .plot-card, .ddh-plot, 
                .heatmap-plot, .utci-plot {
                    flex: 2 1 600px;
                    min-height: 500px;
                }
                @media (max-width: 1200px) {
                    .responsive-container, .ddh-container, 
                    .heatmap-container, .utci-container {
                        flex-direction: column;
                    }
                }
            """)
        ),
        ui.div(
            {"class": "responsive-container"},
            ui.card(
                {"class": "controls-card"},
                ui.h4("Configuración del gráfico de confort"),
                ui.input_checkbox_group(
                    "lineas", 
                    "Mostrar líneas:", 
                    choices={
                        "tdb": "Temperatura del aire promedio diario",
                        "tmp_cmf": "Temperatura de confort ASHRAE 55",                    
                        "ASHRAE_80": "Zona de confort ASHRAE 55 (80%)",
                        "ASHRAE_90": "Zona de confort ASHRAE 55 (90%)",
                        "temp_neutralidad_Morillon": "Temperatura de confort Morillón",
                        "Morillon": "Zona de confort Morillón"
                    },
                    selected=["tdb", "ASHRAE_80"],
                    width="100%"
                ),
                ui.popover(
                    ui.input_action_button("btn_info_confort_1", "ℹ️ Ayuda"),  # trigger
                    '''Para utilizar este gráfico, en la parte superior selecciona o deselecciona las filas según lo necesites; en el panel 
                    derecho podrás ver el comportamiento histórico de las filas elegidas, incluyendo la temperatura media diaria, 
                    las temperaturas de confort según los modelos ASHRAE 55 o Morillón, y los límites de sus respectivas zonas de 
                    confort. Con tu cursor puedes hacer zoom sobre alguna temporada en particular. ASHRAE 55 propone dos zonas: 
                    una donde el 80%/ de los ocupantes se siente en confort térmico y otra donde lo está el 90%/.''',
                    title="¿Cómo utilizar este gráfico?",
                    id="popover_info_confort_1",
                    placement="down"
                )                           
            ),
            ui.card(
                {"class": "plot-card"},
                ui.output_ui("plotly_plot")
            )
        ),
        ui.div(
            {"class": "ddh-container"},
            ui.card(
                {"class": "ddh-controls"},
                ui.h4("Configuración de grados‑hora de disconfort (DDH)"),
                ui.input_date_range("rango_1_ddh", "Rango de fechas 1", start=fecha_min, end=fecha_min + pd.DateOffset(months=1)),
                ui.input_date_range("rango_2_ddh", "Rango de fechas 2", start=fecha_max -  pd.DateOffset(months=1), end=fecha_max),
                ui.input_radio_buttons("modelo_ddh", "Selecciona un modelo", {"Morillon": "Morillón", "ASHRAE_55": "ASHRAE 55"}),
                ui.popover(
                    ui.input_action_button("btn_info_confort_2", "ℹ️ Ayuda"),
                    '''Para interactuar con este gráfico, primero selecciona dos rangos de fechas que desees 
                    comparar y, posteriormente, elige el modelo a utilizar: ASHRAE 55 calcula la temperatura de 
                    confort para cada día, mientras que Morillón calcula una única temperatura anual. En el panel 
                    derecho, se mostrarán cuatro barras: las rojas representan la suma de los grados-hora de disconfort 
                    cálido, mientras que las barras azules indican el disconfort frío para los periodos seleccionados.''',
                    title="¿Cómo utilizar este gráfico?",
                    id="popover_info_confort_2",
                    placement="down"
                )               
            ),
            ui.card(
                {"class": "ddh-plot"},
                ui.output_ui("ddh_plot")
            )
        ),
        ui.div(
            {"class": "heatmap-container"},
            ui.card(
                {"class": "heatmap-controls"},
                ui.h4("Configuración del heat map"),
                ui.input_slider("years_heatmap", "Selecciona el rango de años:", min=int(str(fecha_min).split('-')[0]), max=int(str(fecha_max).split('-')[0]), value=(2023, 2024)),

                ui.popover(
                    ui.input_action_button("btn_info_confort_3", "ℹ️ Ayuda"), 
                    '''Para utilizar este heat map, primero selecciona el rango de años que deseas analizar; en función de esta elección, se 
                    calcularán los promedios mensuales por hora y se determinará la temperatura de confort correspondiente. En el panel derecho, se mostrará el heat map donde 
                    el color azul indica las horas con disconfort térmico por frío, el blanco representa las horas de confort y el rojo señala 
                    las horas con disconfort térmico por calor, todo ello basado en los promedios por hora de cada mes para los años seleccionados.''',
                    title="¿Cómo utilizar este gráfico?",
                    id="popover_info_confort_3",
                    placement="down"
                )

            ),
            ui.card(
                {"class": "heatmap-plot"},
                ui.output_plot("heatmap_plot")
            )
        ),
        ui.div(
            {"class": "utci-container"},
            ui.card(
                {"class": "utci-controls"},
                ui.h4("Configuración del UTCI"),
                ui.input_date_range("rango_1_utci", "Rango de fechas 1", start=fecha_min, end=fecha_min + pd.DateOffset(months=1)),
                ui.input_date_range("rango_2_utci", "Rango de fechas 2", start=fecha_max -  pd.DateOffset(months=1), end=fecha_max),
                ui.popover(
                    ui.input_action_button("btn_info_confort_4", "ℹ️ Ayuda "), 
                    '''Para utilizar este gráfico, primero selecciona los rangos de fechas que te
                      interesen; luego, en el panel derecho podrás ver la suma de las horas dentro 
                      de ese periodo en las que las condiciones de temperatura, velocidad del viento 
                      y humedad relativa provocan alguna categoría de estrés térmico, que va desde 
                      frío extremo, pasando por condiciones neutrales (sin estrés), hasta calor extremo.
                      Nota: ext. significa extremo, mod significa moderado''',
                    title="¿Cómo utilizar este gráfico?",
                    id="popover_info_confort_4",
                    placement="down"
                )                     
            ),
            ui.card(
                {"class": "utci-plot"},
                ui.output_plot("utci_plot")
            )
        )
    )
