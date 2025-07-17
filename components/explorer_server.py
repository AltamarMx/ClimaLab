
from shiny import App, ui, render
import shinyswatch
import duckdb
import io
from utils.config import db_name
from utils.plots import plot_explorer_matplotlib, plot_mean_year_plotly
from shinywidgets import render_plotly
from shinywidgets import output_widget, render_widget  



def explorer_server(input, output, session):
    @output
    @render.plot
    def plot_explorer():
        fechas = input.fechas()
        if fechas is not None:
            return plot_explorer_matplotlib(fechas)
        return plot_explorer_matplotlib()

    def _query_df(fechas):
        con = duckdb.connect(db_name,read_only=True)
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
        fechas = input.fechas_descarga()
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
        fechas = input.fechas_descarga()
        if fechas is None:
            return
        df = _query_df(fechas)
        with io.StringIO() as buf:
            df.to_csv(buf, index=True)
            buf.seek(0)
            yield buf.getvalue()
    
    @output
    @render_plotly
    def plot_mean_year():
        return plot_mean_year_plotly()

