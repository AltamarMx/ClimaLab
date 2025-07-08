from shiny import ui
from shinywidgets import output_widget
import faicons as fa  


def panel_estadistica():
    return ui.nav_panel(
        "Estadística",
        "Aquí irá tu contenido estadístico"
    )

def panel_trayectoriasolar():
    return ui.nav_panel(
        "SunPath",
        "Inserta aquí la figura de sunpath"
    )

def panel_fotovoltaica():
    return ui.nav_panel(
        "FotoVoltaica",
        "Inserta aquí la Produccion solar"
    )

def panel_confort():
    return ui.nav_panel(
        "Confort térmico",
        "Inserta aquí todo  sobre confort"
    )


def panel_eolica():
    return ui.nav_panel(
        "Eolica",
        "Inserta aquí la Produccion eólica"
    )
def panel_documentacion():
    return ui.nav_panel(
        "Documentación",
        "Inserta aquí la documentación"
    )


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
                    accept=['.csv','.dat']
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
                ui.output_plot("missingno_plot", width="80%", height='70%'),
                full_screen=True,
            ),
            col_widths=[3, 2, 7],
        ),
    )


def panel_clean_outliers():
    return ui.nav_panel(
        "Step 2",
        ui.layout_columns(
            ui.card(
                ui.card_header("Irradiance outliers"),
                ui.output_data_frame("df_radiacion"),
            ),
            ui.card(
                ui.card_header("Irradiance outliers visualization"),
                output_widget("plot_radiacion"),
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
                        class_="flex-grow-1"
                    ),
                    ui.div(
                        ui.input_action_button(
                            "btn_load",
                            "Import in database",
                            icon=fa.icon_svg("file-import"),
                            class_="btn btn-outline-success w-100 mb-2"
                        ),
                        ui.input_action_button(
                            "btn_delete",
                            "Delete database",
                            icon=fa.icon_svg("trash"),
                            class_="btn btn-outline-danger w-100"
                        ),
                        class_="d-flex flex-column align-items-end",
                        style="min-width: 200px;"
                    ),
                    class_="d-flex gap-3 align-items-start"
                )
            )
        )
    )


def panel_admin_database():
    return ui.nav_panel(
        "Admin database",
        ui.card(
            ui.card_header("Upload & Export"),
            ui.card_body(
                ui.layout_column_wrap(
                    ui.div(
                        class_="flex-grow-1"
                    ),
                    ui.div(
                        ui.download_button(
                            "export_database",   
                            "Export as Parquet",
                            icon=fa.icon_svg("file-export"),
                            class_="btn btn-outline-success w-100 mb-2",
                        ),
                        class_="d-flex flex-column align-items-end",
                        style="min-width: 200px;"
                    ),
                    class_="d-flex gap-3 align-items-start"
                )
            )
        )
    )