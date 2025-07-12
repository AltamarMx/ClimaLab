from shiny import App, ui, render, reactive
from shinywidgets import render_widget
import duckdb
import pandas as pd

from utils.wind_rose import run_wind_simulation
from utils.wind_rose import (
    create_seasonal_wind_heatmaps,
    create_wind_rose_by_speed_period,
    create_wind_rose_by_speed_night,
    create_wind_rose_by_speed_day,
    create_seasonal_generation_figures,
    create_seasonal_wind_roses_by_speed_plotly,
    create_typical_wind_heatmap,
    create_monthly_energy_figure,
    create_generation_heatmap,
    create_seasonal_generation_figures,

)



from utils.config import ( variables, 
                          latitude, 
                          longitude, 
                          gmt, 
                          db_name, 
                          wind_speed_height, 
                          air_pressure_height, 
                          air_temperature_height, 
                          site_id, 
                          data_tz
)
alias_map = variables.copy()
variables = variables.keys()


# importamos
conn = duckdb.connect(database=db_name)

# Leemos la tabla 'lecturas' y hacemos el df
df_lect = conn.execute(
    "SELECT date, variable, value FROM lecturas"
).df()

# Pivotamos para obtener el DataFrame ancho índice = fecha, columnas = variable
esolmet = df_lect.pivot(index="date", columns="variable", values="value")
esolmet = esolmet.rename(columns=alias_map)
esolmet.index = pd.to_datetime(esolmet.index)
esolmet = esolmet.sort_index()
# print(">>> Columnas en esolmet:", list(esolmet.columns))

def wind_power_server(input, output, session):
    
    
    @render_widget
    def wind_rose_period():
        start_date, end_date = input.wind_date_range()
        return create_wind_rose_period_plotly(
            esolmet,
            dir_col='wd',
            start=start_date,
            end=end_date
        )

    @render_widget
    def wind_rose_day():
        start, end = input.wind_period_range()
        return create_wind_rose_by_speed_day(
            esolmet,
            dir_col="wd",
            speed_col="ws",
            dir_bins=16,
            speed_bins=None,   
            start=start,
            end=end,
        )

    @render_widget
    def wind_rose_night():

        start, end = input.wind_period_range()
        return create_wind_rose_by_speed_night(
            esolmet,
            dir_col="wd",
            speed_col="ws",
            dir_bins=16,
            speed_bins=None,
            start=start,
            end=end,
        )


    @render_widget
    def wind_rose_speed_period():
        start_date, end_date = input.wind_date_range()
        return create_wind_rose_by_speed_period(
            esolmet, dir_col='wd', speed_col='ws',
            start=start_date, end=end_date
        )

    @render_widget
    def rose_spring():
        start_year, end_year = input.season_year_range()
        df = esolmet.loc[f"{start_year}-01-01": f"{end_year}-12-31"]
        figs = create_seasonal_wind_roses_by_speed_plotly(df)
        return figs["Primavera"]

    @render_widget
    def rose_summer():
        start_year, end_year = input.season_year_range()
        df = esolmet.loc[f"{start_year}-01-01": f"{end_year}-12-31"]
        figs = create_seasonal_wind_roses_by_speed_plotly(df)
        return figs["Verano"]

    @render_widget
    def rose_autumn():
        start_year, end_year = input.season_year_range()
        df = esolmet.loc[f"{start_year}-01-01": f"{end_year}-12-31"]
        figs = create_seasonal_wind_roses_by_speed_plotly(df)
        return figs["Otoño"]

    @render_widget
    def rose_winter():
        start_year, end_year = input.season_year_range()
        df = esolmet.loc[f"{start_year}-01-01": f"{end_year}-12-31"]
        figs = create_seasonal_wind_roses_by_speed_plotly(df)
        return figs["Invierno"]
    
    @output
    @render_widget
    def heatmap_wind_annual():
        start, end = input.heatmap_speed_range()
        return create_typical_wind_heatmap(esolmet, speed_col="ws", start=start, end=end)
    @output
    @render_widget
    def heatmap_wind_primavera():
        start, end = input.heatmap_speed_range()
        return create_seasonal_wind_heatmaps(esolmet, "ws", start=start, end=end)["Primavera"]
 

    @output
    @render_widget
    def heatmap_wind_verano():
        start, end = input.heatmap_speed_range()
        return create_seasonal_wind_heatmaps(esolmet, "ws", start=start, end=end)["Verano"]

    @output
    @render_widget
    def heatmap_wind_otono():
        start, end = input.heatmap_speed_range()
        return create_seasonal_wind_heatmaps(esolmet, "ws", start=start, end=end)["Otoño"]


    @output
    @render_widget
    def heatmap_wind_invierno():
        start, end = input.heatmap_speed_range()
        return create_seasonal_wind_heatmaps(esolmet, "ws", start=start, end=end)["Invierno"]


    @reactive.Calc
    def sim_results():
        n_clicks = input.run_sim()
        if n_clicks is None or n_clicks == 0:
            return None

        with reactive.isolate():
            modelo = input.turbine_model()

        return run_wind_simulation(
            esolmet_df=esolmet,
            turbine_name=modelo,
            wind_turbine_file="wind_simulation/wind-turbines.json",
            wind_inputs_file="wind_simulation/windpower-inputs.json",
            output_csv="wind_simulation/sam_wind.csv",
        )

    @output
    @render.table
    def prod_results_table():
        results = sim_results()
        if results is None:
            return None

        if "error" in results:
            return pd.DataFrame([{"Resultado": "Error", "Valor": results["error"]}])

        ae = results.get("Energia Anual (kWh)", None)
        cf = results.get("Factor de Capacidad", None)
        wl = results.get("Perdida por estela (kWh)", None)
        tl = results.get("Perdida por turbina (kWh)", None)


        ae_fmt = f"{ae:,.1f}" if ae is not None else "—"
        wl_fmt = f"{wl:,.1f}" if wl is not None else "—"
        tl_fmt = f"{tl:,.1f}" if tl is not None else "—"
        cf_fmt = f"{cf:.2f}"   if cf is not None else "—"

        df = pd.DataFrame({
            "Parametro": [
                "Energía anual (kWh)",
                "Factor de capacidad",
                "Pérdida por estela (kWh)",
                "Pérdida por turbina (kWh)",
            ],
            "Valor": [
                ae_fmt,
                cf_fmt,
                wl_fmt,
                tl_fmt,
            ],
        })
        return df
    
    @reactive.Effect
    @reactive.event(input.info_results)   #   <-- id del botón "ⓘ"
    def _show_results_help():
        ui.modal_show(
            ui.modal(
                ui.markdown(
    """
    **¿Qué significan estos indicadores?**

    * **Energía anual (kWh)**  
    Energía teórica producida en un año completo de operación.

    - **Factor de capacidad (%)**  
    El factor de capacidad indica el porcentaje de la energía real generada comparada con la que produciría si funcionara a potencia nominal todo el año.
        $$ 
            \\mathrm{FC} = \\frac{\\text{kWh producidos}}{\\text{Potencia nominal (kW)} \\times 8\,760} \\times 100
        $$

    * **Pérdida por estela**  
    Reducción de energía por la turbulencia creada entre turbinas.

    * **Pérdida por turbina**  
    Pérdidas internas: mantenimiento, ensuciamiento, paradas, etc.
    """
                ),
                title="Resultados",
                easy_close=True,
                footer=None,
                size="l",
            )
        )

    @output
    @render_widget
    def prod_monthly_plot():
        results = sim_results()
        if results is None:
            return None

        if "error" in results:
            return ui.tags.pre(results["error"])

        monthly = results.get("Monthly Energy")
        if monthly is None:
            return ui.tags.pre("No hay datos mensuales disponibles.")

        try:
            fig = create_monthly_energy_figure(monthly)
        except ValueError as e:
            return ui.tags.pre(str(e))

        return fig
    
    @reactive.Effect
    @reactive.event(input.info_monthly)
    def _show_monthly_help():
        ui.modal_show(
            ui.modal(
                # primero el contenido (posicional):
                ui.markdown(
                    """
                    **Energía mensual (kWh)**  
                    Esta gráfica muestra, para cada mes del año típico (enero–diciembre), la **energía total** que generaría la turbina, calculada como la suma de la producción horaria de ese mes.
                    """
                ),
                # y después los keywords:
                title="¿Qué representa esta gráfica?",
                easy_close=True,
                footer=None,
                size="m",
            )
        )


    @output
    @render.ui
    def seasonal_primavera():
        results = sim_results()
        if results is None:
            return None

        if "error" in results:
            return ui.tags.pre(results["error"])

        gen_array = results.get("gen")
        if gen_array is None:
            return ui.tags.pre("No hay datos horarios de generación.")

        figures = create_seasonal_generation_figures(gen_array)
        return figures["Primavera"]


    @output
    @render.ui
    def seasonal_verano():
        results = sim_results()
        if results is None:
            return None

        if "error" in results:
            return ui.tags.pre(results["error"])

        gen_array = results.get("gen")
        if gen_array is None:
            return ui.tags.pre("No hay datos horarios de generación.")

        figures = create_seasonal_generation_figures(gen_array)
        return figures["Verano"]


    @output
    @render.ui
    def seasonal_otono():
        results = sim_results()
        if results is None:
            return None

        if "error" in results:
            return ui.tags.pre(results["error"])

        gen_array = results.get("gen")
        if gen_array is None:
            return ui.tags.pre("No hay datos horarios de generación.")

        figures = create_seasonal_generation_figures(gen_array)
        return figures["Otoño"]


    @output
    @render.ui
    def seasonal_invierno():
        results = sim_results()
        if results is None:
            return None

        if "error" in results:
            return ui.tags.pre(results["error"])

        gen_array = results.get("gen")
        if gen_array is None:
            return ui.tags.pre("No hay datos horarios de generación.")

        figures = create_seasonal_generation_figures(gen_array)
        return figures["Invierno"]
    

    @reactive.Effect
    @reactive.event(input.info_seasonal_all)
    def _show_all_season_help():
        ui.modal_show(
            ui.modal(
                ui.markdown(
                    """
                    Cada una corresponde a una estación del año:
                    - **Primavera** (mar–may)  
                    - **Verano**    (jun–ago)  
                    - **Otoño**     (sep–nov)  
                    - **Invierno**  (dic–feb)  

                    Para cada día del “mes típico”, la altura de la barra es la **energía diaria** que produciría la turbina en esa estación.    
                    """
                ),
                title="Energía generada por estación",
                easy_close=True,
                footer=None,
                size="m",
            )
        )


    @output
    @render_widget
    def prod_heatmap():
        results = sim_results()
        if results is None:
            return None

        if "error" in results:
            return ui.tags.pre(results["error"])

        gen_array = results.get("gen")
        if gen_array is None:
            return ui.tags.pre("No hay datos horarios de generación.")

        fig = create_generation_heatmap(gen_array)
        return fig
    
    @reactive.Effect
    @reactive.event(input.info_heatmap_gen)
    def _show_heatmap_help():
        ui.modal_show(
            ui.modal(
                ui.markdown(
                    """ 
                    **¿Qué representa este heatmap?**
                    - **Eje horizontal**: día del año (Ene 1 – Dic 31).  
                    - **Eje vertical**: hora del día (0 – 23 h).  
                    - **Color**: energía generada en esa hora y día (kWh).

                    Cada celda es la **producción horaria media típica** para ese instante en un año, mostrando en qué horas y en qué épocas del año la turbina genera más o menos energía.
                    """
                ),
                title="Heatmap de generación anual",
                easy_close=True,
                footer=None,
                size="m",
            )
        )
