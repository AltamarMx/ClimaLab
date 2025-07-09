from shiny import App, ui
from shinywidgets import render_plotly
import shinyswatch

from utils.config import name

from components.explorador import panel_explorador, panel_estadistica
from components.panels import (
    panel_documentacion,
    panel_trayectoriasolar,
    panel_fotovoltaica,
    panel_eolica,
    panel_confort,
)

# from utils.data_processing import load_esolmet_data
from utils.plots import graph_all_plotly_resampler, graph_all_matplotlib


app_ui = ui.page_fillable(
    ui.navset_card_tab(
        ui.nav_panel(
            name,
            ui.navset_card_tab(
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


    @output
    @render_plotly
    def plot_resampler():
        return graph_all_plotly_resampler(input.fechas())


app = App(app_ui, server)
