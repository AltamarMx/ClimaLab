from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget
from utils.pv_calc import irradiance_poa, hsp_calc, hsp_visual, power_calc, pvgen_poaglobal_year, poa_visual_extrdays, power_visual_extrdays
from components.pv_calc_ui import modules_pv, assembly_options, inverters
import pandas as pd
import duckdb
from utils.config import latitude, longitude, db_name


lat, lon = latitude, longitude
con = duckdb.connect(db_name,read_only=True)
df_large = con.execute("SELECT * FROM lecturas").fetchdf()

df = df_large.pivot(index='date', columns='variable', values='value')
df.index = pd.to_datetime(df.index)
df = df.sort_index()
df = df.loc["2024"]
df.index = df.index.tz_localize('America/Mexico_City') # type: ignore # Asignación de zona horaria

def pv_calc_server(input, output, session):
    @reactive.calc
    def current_inputs():
        return {
            "surface_tilt": input.tilt(),
            "surface_azimuth": input.azimuth(),
            "selected_mod": input.model_pv(),
            "selected_asse": input.assembly(),
            "selected_inv": input.inverter_model()
        }

    def run_calcs(inputs):
        surface_tilt = inputs["surface_tilt"]
        surface_azimuth = inputs["surface_azimuth"]
        pdc0 = modules_pv[inputs["selected_mod"]]["pdc0"]
        gamma_pdc = modules_pv[inputs["selected_mod"]]["gamma_pdc"]
        assembly = assembly_options[inputs["selected_asse"]]
        inv_eff = inverters[inputs["selected_inv"]]

        irradiance = irradiance_poa(df, lat, lon, surface_tilt, surface_azimuth)
        ac_power, df_poa_power = power_calc(df, irradiance, assembly, pdc0, gamma_pdc, inv_eff)

        return {
            "irradiance": irradiance,
            "ac_power": ac_power,
            "df_poa_power": df_poa_power,
            "surface_tilt": surface_tilt,
            "surface_azimuth": surface_azimuth
        }

    def default_inputs():
        return {
            "surface_tilt": lat,
            "surface_azimuth": 180,
            "selected_mod": "Longi 620W Mono",
            "selected_asse": "Módulo monocristalino/policristalino en rack abierto",
            "selected_inv": "Huawei SUN2000 480V (98.8%)"
        }

    @reactive.calc
    def calcs():
        n_clicks = input.run_sim_pv()
        if n_clicks == 0:
            return run_calcs(default_inputs())
        with reactive.isolate():
            return run_calcs(current_inputs())
    
    @output
    @render_widget # type: ignore
    def graph_energy_month():
        ac_power = calcs()["ac_power"]
        irradiance = calcs()["irradiance"]        
        return pvgen_poaglobal_year(ac_power, irradiance)
    
    @output
    @render_widget # type: ignore
    def graph_irradiances():
        irradiance = calcs()["irradiance"]       
        return poa_visual_extrdays(irradiance)
    
    @output
    @render_widget # type: ignore
    def graph_ac_power():
        ac_power = calcs()["ac_power"]       
        return power_visual_extrdays(ac_power)

    @output
    @render_widget # type: ignore
    def graph_hsp():
        surface_tilt= calcs()["surface_tilt"]
        surface_azimuth= calcs()["surface_azimuth"]
        df_hsp = hsp_calc(df,lat,lon,surface_tilt, surface_azimuth)
        irradiance = calcs()["irradiance"]   
        return hsp_visual(df_hsp,irradiance)
    
    @output
    @render.table
    def table_hsp():
        surface_tilt= calcs()["surface_tilt"]
        surface_azimuth= calcs()["surface_azimuth"]
        return hsp_calc(df,lat,lon,surface_tilt, surface_azimuth)
    
    # Botón de descarga para datos POA
    @output
    @render.download(filename="datos_poa_potencia.csv", media_type="text/csv")
    def download_data_poa():
        df_poa_power = calcs()["df_poa_power"] 
        yield df_poa_power.to_csv(index=True)
        

    # Botón de descarga para tabla HSP
    @output
    @render.download(filename="tabla_hsp.csv",media_type="text/csv")
    def download_table_hsp():
        surface_tilt= calcs()["surface_tilt"]
        surface_azimuth= calcs()["surface_azimuth"]
        table = hsp_calc(df,lat,lon,surface_tilt, surface_azimuth)
        yield table.to_csv(index=True)
    
