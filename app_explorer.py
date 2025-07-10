from shiny import App, ui, render
import shinyswatch
import duckdb
import io

from utils.config import name, db_name

from components.explorador import panel_explorador, panel_estadistica
from components.panels import (
    panel_documentacion,
    panel_trayectoriasolar,
    panel_fotovoltaica,
    panel_eolica,
    panel_confort,
)
from components.sun_path_server import sun_path_server

# from utils.data_processing import load_esolmet_data
from utils.plots import plot_explorer_matplotlib


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
    @render.plot
    def plot_explorer():
        fechas = input.fechas()
        if fechas is not None:
            return plot_explorer_matplotlib(fechas)
        return plot_explorer_matplotlib()

    def _query_df(fechas):
        con = duckdb.connect(db_name)
        q = f"""
        SELECT *
          FROM lecturas
         WHERE date >= TIMESTAMP '{fechas[0]}'
           AND date <= TIMESTAMP '{fechas[1]}'
         ORDER BY date
        """
        df = con.execute(q).fetchdf().pivot(index="date", columns="variable", values="value")
        con.close()
        return df

    @output
    @render.download(filename="ClimaLab.parquet", media_type="application/x-parquet")
    def dl_parquet():
        fechas = input.fechas()
        if fechas is None:
            return
        df = _query_df(fechas)
        with io.BytesIO() as buf:
            df.to_parquet(buf, index=True, engine="pyarrow")
            buf.seek(0)
            yield buf.getvalue()

    @output
    @render.download(filename="ClimaLab.csv", media_type="text/csv")
    def dl_csv():
        fechas = input.fechas()
        if fechas is None:
            return
        df = _query_df(fechas)
        with io.StringIO() as buf:
            df.to_csv(buf, index=True)
            buf.seek(0)
            yield buf.getvalue()

            
    sun_path_server(input, output, session)



app = App(app_ui, server)
