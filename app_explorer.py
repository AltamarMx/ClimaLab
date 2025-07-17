from shiny import App, ui, render
import shinyswatch
import duckdb
import io

from utils.config import name, db_name

from components.explorador import panel_descarga, panel_explorador, panel_estadistica
from components.panels import (
    panel_documentacion,
    panel_trayectoriasolar,
    panel_fotovoltaica,
    panel_eolica,
)
from components.thermal_comfort_ui import panel_confort
from components.sun_path_server import sun_path_server
from components.thermal_comfort_ui import panel_confort
from components.pv_calc_ui import pv_calc_ui
from components.thermal_comfort_server import thermal_comfort_server
from components.explorer_server import explorer_server
from components.wind_power_server import wind_power_server  
from components.pv_calc_server import pv_calc_server

# from utils.data_processing import load_esolmet_data


app_ui = ui.page_fillable(
    ui.navset_card_tab(
        ui.nav_panel(
            name,
            ui.navset_card_tab(
                panel_descarga(),
                panel_explorador(),
                panel_estadistica(),
                id="climalab_subtabs"
            ),
        ),
        ui.nav_panel(
            "Tools",
            ui.navset_card_tab(
                panel_trayectoriasolar(),
                panel_fotovoltaica(),
                panel_eolica(),
                panel_confort(),
                id="herramientas",
            ),
        ),
    ),
    theme=shinyswatch.theme.spacelab,
)


def server(input, output, session):

    explorer_server(input,output,session)
    sun_path_server(input, output, session)
    pv_calc_server(input, output, session)
    thermal_comfort_server(input, output, session)
    wind_power_server(input, output, session)




app = App(app_ui, server,debug=False)
