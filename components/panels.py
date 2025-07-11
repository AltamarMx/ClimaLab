from shiny import ui
from shinywidgets import output_widget
import faicons as fa
from components.sun_path_ui import sun_path_ui 
from utils.config import db_name
import os
import pandas as pd
import duckdb



conn = duckdb.connect(database=db_name)
df_lect = conn.execute(
    "SELECT date, variable, value FROM lecturas"
).df()
df = df_lect.pivot(index="date", columns="variable", values="value")
df.index = pd.to_datetime(df.index)
df = df.sort_index()

def panel_estadistica():
    return ui.nav_panel("Estadística", "Aquí irá tu contenido estadístico")


def panel_trayectoriasolar():
    return ui.nav_panel(
        "SunPath",
        sun_path_ui
    )


def panel_fotovoltaica():
    return ui.nav_panel("FotoVoltaica", "Inserta aquí la Produccion solar")


def panel_confort():
    return ui.nav_panel("Confort térmico", "Inserta aquí todo  sobre confort")

def panel_eolica():
    min_year = df.index.year.min()# Calculamos maximos i minimos 
    max_year = df.index.year.max()
    min_date = str(df.index.min().date())
    max_date = str(df.index.max().date())
    return ui.nav_panel(
        "Eólica",
        ui.navset_tab(
            ui.nav_panel(
                "Rosas de Viento",
                ui.h3(" "),
                ui.input_date_range(
                    "wind_period_range",
                    "Selecciona periodo:",
                    start=min_date, end=max_date,
                    min=min_date,   max=max_date
                ),
          ui.row(
            ui.column(
              6,
              ui.h4("Rosa diurna", style="text-align:center;"),
              output_widget("wind_rose_day")
            ),
            ui.column(
              6,
              ui.h4("Rosa nocturna", style="text-align:center;"),
              output_widget("wind_rose_night")
            ),
          ),

                # Rosa por periodo
                ui.h3("Rosas de viento promedio anual"),
                ui.input_date_range(
                    "wind_date_range",
                    "Selecciona periodo:",
                    start=min_date,  # fecha de inicio por defecto
                    end=max_date,    # fecha de fin por defecto
                    min=min_date,    # límite mínimo seleccionable
                    max=max_date     # límite máximo seleccionable
                ),
                output_widget("wind_rose_speed_period"),

                ui.h3("Rosa de viento promedio estacional"),
                ui.input_slider(
                    "season_year_range",
                    "Selecciona rango de años:",
                    min=min_year,
                    max=max_year,
                    value=(min_year, max_year),
                    step=1
                ),

                ui.div(
                    ui.div(ui.h4("Primavera"), output_widget("rose_spring")),
                    ui.div(ui.h4("Verano"),    output_widget("rose_summer")),
                    ui.div(ui.h4("Otoño"),     output_widget("rose_autumn")),
                    ui.div(ui.h4("Invierno"),  output_widget("rose_winter")),
                    style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;"
                ),
            ),

            ui.nav_panel(
                "Heatmaps velocidad",
                ui.h3("Velocidad de viento anual y estacional"),
                ui.input_date_range(
                    "heatmap_speed_range",
                    "Selecciona periodo:",
                    start=min_date, end=max_date,
                    min=min_date,   max=max_date
                ),
                ui.row(
                    ui.column(
                        12,
                        ui.h4("Heatmap anual", class_="fs-2 mb-3"),
                        output_widget(
                            "heatmap_wind_annual",
                            width="100%",    
                            height="600px"
                        ),    
                    ),
                ),
                ui.row(
                    ui.column(6,
                        ui.h4("Primavera", style="text-align:center;"),
                        output_widget("heatmap_wind_primavera",
                            width="100%",    
                            height="400px")
                    ),
                    ui.column(6,
                        ui.h4("Verano", style="text-align:center;"),
                        output_widget("heatmap_wind_verano",
                            width="100%",    
                            height="400px")
                    ),
                ),
                ui.row(
                    ui.column(6,
                        ui.h4("Otoño", style="text-align:center;"),
                        output_widget("heatmap_wind_otono",
                            width="100%",    
                            height="400px")
                    ),
                    ui.column(6,
                        ui.h4("Invierno", style="text-align:center;"),
                        output_widget("heatmap_wind_invierno",
                            width="100%",    
                            height="400px")
                    ),
                ),
            ),

                        # NUEVA SUB-PESTAÑA
            ui.nav_panel(
                "Energía eólica",
                ui.h3("Generación de energía eólica", class_="mb-4"),
                ui.row(
                    ui.column(4,
                        ui.div(
                            ui.input_select("turbine_model",
                                "Selecciona modelo de turbina:",
 
                                choices=[
                                    "SkyStream 2.4kW",
                                    "GE 1.5MWsle",
                                    "Nordex S77 1.5MW",
                                    "Fuhrlander FL 1.5MW",
                                    "BergeyExcel 8.9kW-7 (Distributed)",
                                    "NREL2019COE 100kW-27.6(Distributed)",
                                    "VestasV29 225kW-29(Distributed)",
                                    "NREL2019COE 20kW-12.4(Distributed)",
                                    "VestasV47 660kW-47",
                                    "Ampair600 0.73kW-1.7"
                                ]
                            ),
                            class_="mb-3"
                        ),
                        ui.tags.style("""
                        /* para que el icono sea sólo trazo negro */
                        svg.feather-circle-info {
                            fill: none !important;
                            stroke: black !important;
                        }
                        """),

                        ui.div(
                        ui.input_task_button(
                            "run_sim",    # mismo input ID que usas en server
                            "Compute",    # etiqueta del botón
                            class_="mb-4" 
                        ),
                        class_="d-flex align-items-center"
                        ),

                            # Salidas de texto donde mostraremos los resultados
                        ui.div(
                            ui.h4("Resultados de la simulación", class_="d-inline"),
                            ui.input_action_button(
                                "info_results",          
                                label=None,
                                icon=fa.icon_svg("circle-info"),
                                class_="btn-link p-0",
                                style="background-color:transparent; border:none; box-shadow:none; padding:0;"
                            ),
                            class_="mb-2",
                            ),
                        ui.output_table("prod_results_table"),
                    ),
        
                    ui.column(8,
                    ui.div(
                        ui.h4("Energía mensual", class_="d-inline"),
                        ui.input_action_button(
                        "info_monthly",   # <-- nuevo ID
                        label=None,
                        icon=fa.icon_svg("circle-info"),
                        class_="btn-link p-0",
                        style="background-color:transparent; border:none; box-shadow:none; padding:0;"
                        ),
                        class_="mb-2"
                    ),
                    output_widget("prod_monthly_plot"),
                    ),
                ui.row(
                    ui.column(
                        12,
                        ui.h4("Energía generada por estación del año",class_="d-inline"),
                        ui.input_action_button(
                        "info_seasonal_all",   # <-- nuevo ID
                        label=None,
                        icon=fa.icon_svg("circle-info"),
                        class_="btn-link p-0",
                        style="background-color:transparent; border:none; box-shadow:none; padding:0;"
                        ),
                        class_="mb-2"
                    ),   # márgenes opcionales
                    )
                ),
                ui.row(
                    ui.column(3,
                        ui.h5("Primavera"),
                        ui.output_ui("seasonal_primavera")
                    ),
                    ui.column(3,
                        ui.h5("Verano"),
                        ui.output_ui("seasonal_verano")
                    ),
                    ui.column(3,
                        ui.h5("Otoño"),
                        ui.output_ui("seasonal_otono")
                    ),
                    ui.column(3,
                        ui.h5("Invierno"),
                        ui.output_ui("seasonal_invierno")
                    ),
                ),
                ui.row(
                    ui.column(
                        12,
                        ui.div(
                            # título + botón de ayuda
                            ui.h4("Energía generada horaria anual", class_="d-inline fs-2"),
                            ui.input_action_button(
                                "info_heatmap_gen",  # nuevo ID
                                label=None,
                                icon=fa.icon_svg("circle-info"),
                                class_="btn btn-link p-0 ms-2",
                                style="background:transparent; border:none; box-shadow:none;"
                            ),
                            class_="mb-2"
                        ),
                        output_widget(
                        "prod_heatmap",
                        width="100%",    # aquí forzamos 100% de la columna
                        height="600px"
                        ),
                    ),
                ),
            ),
        ),
    )


def panel_documentacion():
    return ui.nav_panel("Documentación", "Inserta aquí la documentación")


def panel_upload_file():
    return ui.nav_panel(
        "Step 1",
        ui.layout_columns(
            ui.card(
                ui.card_header("File"),
                ui.input_file(
                    "file",
                    "Select file",
                    button_label="Browse",
                    placeholder="FILE",
                    accept=[".csv", ".dat"],
                ),
                ui.output_ui("upload_status"),
                ui.output_table("table_tests"),
            ),
            ui.card(
                ui.card_header("Types"),
                ui.output_data_frame("df_types"),
            ),
            ui.card(
                ui.card_header("EDA"),
                ui.output_plot("missingno_plot_imported", width="80%", height="70%"),
                full_screen=True,
            ),
            col_widths=[3, 2, 7],
        ),
        ui.card(
            ui.card_header("All data"),
            ui.output_ui("column_selector"),
            ui.output_plot("plot_all_matplotlib"),
            full_screen=True,
        ),
    )


def panel_clean_outliers():
    return ui.nav_panel(
        "Step 2",
        ui.layout_columns(
            ui.card(
                ui.card_header("Irradiance outliers"),
                ui.output_data_frame("df_irradiance"),
            ),
            ui.card(
                ui.card_header("Data without outliers"),
                ui.output_plot("missingno_plot_outliers"),
                full_screen=True,
            ),
            col_widths=[5, 7],
        ),
    )


def panel_load_database():
    return ui.nav_panel(
        "Step 3",
        ui.card(
            ui.card_header("Upload & Export"),
            ui.card_body(
                ui.layout_column_wrap(
                    ui.div(
                        ui.output_ui("load_status"),
                        ui.output_ui("delete_status"),
                        class_="flex-grow-1",
                    ),
                    ui.div(
                        ui.input_action_button(
                            "btn_load",
                            "Import in database",
                            icon=fa.icon_svg("file-import"),
                            class_="btn btn-outline-success w-100 mb-2",
                        ),
                        ui.input_action_button(
                            "btn_delete",
                            "Delete database",
                            icon=fa.icon_svg("trash"),
                            class_="btn btn-outline-danger w-100",
                        ),
                        class_="d-flex flex-column align-items-end",
                        style="min-width: 200px;",
                    ),
                    class_="d-flex gap-3 align-items-start",
                )
            ),
        ),
    )


def panel_admin_database():
    return ui.nav_panel(
        "Export database",
        ui.card(
            ui.card_header("Upload & Export"),
            ui.card_body(
                ui.layout_column_wrap(
                    ui.div(class_="flex-grow-1"),
                    ui.div(
                        ui.download_button(
                            "export_database",
                            "Export as Parquet",
                            icon=fa.icon_svg("file-export"),
                            class_="btn btn-outline-success w-100 mb-2",
                        ),
                        class_="d-flex flex-column align-items-end",
                        style="min-width: 200px;",
                    ),
                    class_="d-flex gap-3 align-items-start",
                )            ),
        ),
    )
