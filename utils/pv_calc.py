import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from datetime import timedelta
# Librerias de Pvlib
from pvlib.pvsystem import pvwatts_dc # Modelo PVWatts
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS, sapm_cell #Modelo para temperatura de celda
from pvlib.irradiance import get_total_irradiance # Modelo para calcular plane-of-array irradiance POA
from pvlib.location import Location # Para generar la posición solar para cada timestamp


# Calculo de irradiancia sobre plano inclinado
def irradiance_poa(df,lat,lon,surface_tilt,surface_azimuth):
    '''
    Calcula la irradiancia sobre un plano inclinado (plane of array -POA-) con pvlib

    Parámetros:
    - df: DataFrame con índice datetime que incluye variables como ghi, dni y dhi
    - lat, lon : latitud y longitud de la estación meteorológica para obtener la posición solar
    - surface_tilt: ángulo de inclinación del módulo FV [°]
    - surface_azimuth: ángulo de azimuth del módulo FV [°]

    solpos calcula la posición solar para cada timestamp

    Return: Devuelve la irradiancia global, directa y difusa sobre un plano inclinado 
    (poa_global, poa_direct, poa_diffuse) [W/m^2]
    '''
    location = Location(latitude=lat, longitude=lon)
    solpos = location.get_solarposition(df.index)
    irradiance = get_total_irradiance(
        surface_tilt = surface_tilt,
        surface_azimuth= surface_azimuth,
        dni = df.dni,
        ghi = df.ghi,
        dhi = df.dhi,
        solar_zenith = solpos['zenith'],
        solar_azimuth = solpos['azimuth']
        )
    return irradiance

# Cálculo de HSP
def hsp_calc(df,lat,lon,surface_tilt, surface_azimuth):
    '''
    Calcula la hora solar pico (HSP) de varios ángulos de inclinación del módulo FV

    Parámetros:
    - df: DataFrame con índice datetime que incluye variables como ghi, dni y dhi
    - lat, lon : latitud y longitud de la estación meteorológica para obtener la posición solar
    - surface_tilt: ángulo de inclinación del módulo FV [°]
    - surface_azimuth: ángulo de azimuth del módulo FV [°]

    solpos calcula la posición solar para cada timestamp

    Return: Devuelve las HSP promedio mensuales y promedio anual de los siguientes ángulos de inclinación
    (0°,lat°,lat-15°,lat+15°,90°)
    '''
    location = Location(latitude=lat, longitude=lon)
    solpos = location.get_solarposition(df.index)
    tilts= [0,surface_tilt,surface_tilt-15,surface_tilt+15,90]
    hsp_dict = {}
    months_index = []  
    for tilt in tilts:
        irradiance = get_total_irradiance(
            surface_tilt = tilt,
            surface_azimuth= surface_azimuth,
            dni = df.dni,
            ghi = df.ghi,
            dhi = df.dhi,
            solar_zenith = solpos['zenith'],
            solar_azimuth = solpos['azimuth'])

        ghi_hour = irradiance.poa_global.resample("h").mean() # type: ignore
        hsp_d = ghi_hour.resample("D").sum()/1000  
        hsp_avg_m = hsp_d.resample("ME").mean()

        # Guardar los nombres de meses desde el índice real
        if not months_index:
            months_index = [dt.strftime('%B') for dt in hsp_avg_m.index]

        hsp_dict[f"{tilt}°"] = [round(val, 2) for val in hsp_avg_m.values]

    df_hsp = pd.DataFrame.from_dict(hsp_dict, orient='index')
    df_hsp.columns = months_index  # usa nombres de meses como columnas
    df_hsp["Average"] = df_hsp.mean(axis=1).round(2)
    df_hsp.reset_index(inplace=True)
    df_hsp.rename(columns={"index": "Slope"}, inplace=True)

    return df_hsp

# Visualización la definición de HSP 
def hsp_visual(df_hsp,irradiance):
    '''
    Grafica la HSP promedio anual en una curva de irradiancia global (G) sobre un plano inclinado
    de una fecha específica

    Parámetros:
    - df_hsp: DataFrame de las HSP promedio mensuales y anual de diferentes inclinaciones 
    - irradiance : irradiancia global sobre un plano inclinado [W/m^2]

    Return: Gráfico de la definición de HSP sobre una curva G de un día específico
    '''
    poa_global_hour = irradiance.poa_global.resample("h").mean() 
    avg_irradiance_by_hour = poa_global_hour.groupby(poa_global_hour.index.hour).mean().round(2)
    hours_label = [f"{h:02d}:00" for h in range(24)]
    
    hsp_year= df_hsp.Average.iloc[1]
    center_hour = avg_irradiance_by_hour.idxmax() #Tomé el max de irradiancia como valor central 
    start_hour = center_hour - hsp_year / 2
    end_hour = center_hour + hsp_year / 2
    
    # start_time = center_time - pd.Timedelta(hours=hsp_year / 2)
    # end_time = center_time + pd.Timedelta(hours=hsp_year / 2)

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=hours_label, y=avg_irradiance_by_hour.values, mode='lines', name='Día irradiancia promedio anual', line=dict(color='black')))

    fig.add_shape(type="line", x0=start_hour, x1=start_hour, y0=0, y1=1000,line=dict(color="red", dash="dash"), name="Inicio HSP") # type: ignore #Vertical
    fig.add_shape(type="line", x0=end_hour, x1=end_hour, y0=0, y1=1000,line=dict(color="red", dash="dash"), name="Fin HSP") # type: ignore #Vertical
    fig.add_shape(type="line", x0=start_hour, x1=end_hour, y0=1000, y1=1000,line=dict(color="red", dash="dot"), name="1000 W/m²") # type: ignore # Horizontal
    fig.add_shape(type="rect",x0=start_hour, x1=end_hour,y0=0, y1=1000,fillcolor="rgba(255,0,0,0.1)",line=dict(width=0),layer='below') # type: ignore # Sombreado

    fig.update_layout(
        title=f'Visualización de HSP promedio anual a la inclinación seleccionada del día promedio anual',
        xaxis_title='Hora del día',
        yaxis_title='Irradiancia (W/m^2)',
        legend=dict(x=1.02, y=1, xanchor='left'),
        margin=dict(r=100),
        template='plotly_white'
    )
    return fig

# Cálculos para potencia AC
def power_calc(df,irradiance,assembly,pdc0,gamma_pdc,inv_eff):
    '''
    Calcula la potencia AC generada por un módulo FV específico [W]

    Parámetros:
    - df: DataFrame con índice datetime que incluye variables como ghi, dni, dhi, tdb, ws
    - lat, lon : latitud y longitud de la estación meteorológica para obtener la posición solar
    - irradiance : irradiancia global sobre un plano inclinado [W/m^2]
    - assembly: tipo de montaje de los módulos de acuerdo según el modelo SAPM
    - pdc0: potencia nominal del módulo FV [W]
    - gamma_pdc: coeficiente de temperatura en potencia máxima 
    - inv_eff: eficiencia del inversor [0-1]

    -Se utiliza el modelo SAPM únicamente para calcular la temperatura de la celda
    -Se utiliza el modelo PVWatts para calcular la potencia DC

    Return: La potencia AC [W] en un DataFrame y un Dataframe de irradiancia POA junto con la potencia AC
    '''
    # Calcular temperatura del módulo
    temp_params = TEMPERATURE_MODEL_PARAMETERS['sapm'][assembly]
    poa_global = irradiance['poa_global'] # Irradiancia sobre el plano con ángulos incluidos
    module_temp = sapm_cell(
        poa_global=poa_global,
        temp_air=df['tdb'],
        wind_speed=df['ws'],
        **temp_params
    )# modelo SAPM para obtener temperatura de la celda únicamente
    dc_power = pvwatts_dc(poa_global, module_temp, pdc0=pdc0, gamma_pdc=gamma_pdc) # Potencia DC
    ac_power = dc_power * inv_eff # Potencia AC brinda la potencia en W en intervalos de 10min de un único módulo 
    df_poa_power = irradiance[["poa_global", "poa_direct", "poa_diffuse"]].copy()
    df_poa_power["ac_power"] = ac_power

    return ac_power, df_poa_power

# PV gen vs Irradiancia global sobre plano
def pvgen_poaglobal_year(ac_power, irradiance):
    '''
    Grafica la generación FV de un módulo y la irradiancia global sobre un plano de un módulo

    Parámetros:
    - ac_power: DataFrame con índice datetime de la potencia AC [W]
    - irradiance : irradiancia global sobre un plano inclinado [W/m^2]

    Return: Gráfico generación FV vs irradiancia sobre un plano por mes
    '''
    ac_power_hour = ac_power.resample("h").mean()/1000 # Energía de potencia AC en kWh
    energy_ac_monthly = ac_power_hour.resample("ME").sum()

    poa_global_hour = irradiance.poa_global.resample("h").mean()/1000 # Energía de irradiancia sobre módulo en kWh
    energy_poa_monthly = poa_global_hour.resample("ME").sum()

    energy_monthly_array = pd.DataFrame({"Generación FV": (energy_ac_monthly).round(2),
        "Irradiancia_POA":  (energy_poa_monthly).round(2)})
    months = energy_monthly_array.index.to_period('M').strftime('%b') # type: ignore

    fig = go.Figure([
        go.Bar(name='Generación FV', x=months, y=energy_monthly_array["Generación FV"],
            marker_color='rgb(26, 118, 255)'),
        go.Bar(name='Irradiancia POA', x=months, y=energy_monthly_array["Irradiancia_POA"],
            marker_color='rgb(55, 83, 109)')
    ])

    fig.update_layout(
        title='Energía mensual: Generación FV vs Irradiancia POA',
        xaxis_title='Mes',
        yaxis_title='Energía (kWh)',
        barmode='group',
        bargap=0.15,
        bargroupgap=0.1,
        legend=dict(
        #     x=1.1,  # Dentro del área de trazado
        #     y=1,
            xanchor='right',
            yanchor='top',
            bgcolor='rgba(0,0,0,0)',  # Fondo transparente
            bordercolor='rgba(0,0,0,0)'  # Sin borde
        ),
        margin=dict(r=30)
    )
    return fig

# 8. Visualización de ghi, dni, dhi contra ghi2, dni2, dhi2 del modelo POA
# #Esta función grafica con líneas sobre el eje x, comprobar con nueva base de datos
# def poa_visual_extrdays(irradiance):
#     '''
#     Grafica las irradiancias sobre un plano inclinado (POA) del día máximo y mínimo de energía anual por irradiancia

#     Parámetros:
#     - irradiance : irradiancia global sobre un plano inclinado [W/m^2]

#     Return: Gráfico irradiancias sobre un plano inclinado (POA) del día máximo y mínimo de energía del año
#     '''
#     # Obteniendo irradiance por día
#     poa_global_hour = irradiance.poa_global.resample("h").mean()
#     energy_poa_daily = poa_global_hour.resample("D").sum()
    
#     # Día con mayor y menor energía
#     max_irr_day = energy_poa_daily.idxmax()
#     min_irr_day = energy_poa_daily.idxmin()
       
#     # Fechas para graficar 
#     start_maxir = max_irr_day
#     end_maxir = start_maxir + timedelta(hours=24)
#     start_minir = min_irr_day
#     end_minir = start_minir + timedelta(hours=24)
    
#     # Del irradiance model POA sobre plano inclinado
#     poa_max = poa_global_hour.loc[start_maxir:end_maxir]
#     poa_min = poa_global_hour.loc[start_minir:end_minir]

#     hours_max = [t.strftime('%H:%M') for t in poa_max.index.time]
#     hours_min = [t.strftime('%H:%M') for t in poa_min.index.time]
#     hover_max = [f"{dt.strftime('%Y-%m-%d %H:%M')} - {val:.2f} W/m²" for dt, val in zip(poa_max.index, poa_max)]
#     hover_min = [f"{dt.strftime('%Y-%m-%d %H:%M')} - {val:.2f} W/m²" for dt, val in zip(poa_min.index, poa_min)]

#     fig = go.Figure()

#     fig.add_trace(go.Scatter(x=hours_max, y=poa_max, mode='lines', name=f'Día con máxima energía ({max_irr_day.date()})',line=dict(color='red'), hovertext=hover_max, hoverinfo="text"))
#     fig.add_trace(go.Scatter(x=hours_min, y=poa_min, mode='lines', name=f'Día con mínima energía ({min_irr_day.date()})', line=dict(color='blue'),hovertext=hover_min,hoverinfo="text"))
    
#     fig.update_layout(
#         title=f'Comparación de irradiancias (POA global) del día de máxima y mínima energía del año',
#         xaxis_title='Hora del día',
#         yaxis_title='Irradiancia (W/m2)',
#         legend=dict(x=1.02, y=1, xanchor='left'),
#         margin=dict(r=100),
#         template='plotly_white'
#     )

#     return fig

def poa_visual_extrdays(irradiance):
    '''
    Grafica las irradiancias sobre un plano inclinado (POA) del día máximo y mínimo anual de energía

    Parámetros:
    - irradiance : DataFrame con columna poa_global [W/m²]

    Return: Figura de Plotly con ambas curvas sobre el mismo eje horario
    '''
    # Energía diaria por poa_global
    poa_hourly = irradiance.poa_global.resample("h").mean()
    energy_daily = poa_hourly.resample("D").sum()

    # Fechas clave
    max_day = energy_daily.idxmax()
    min_day = energy_daily.idxmin()

    # Rango estándar de horas: 00:00 a 23:00
    hours = pd.date_range("00:00", "23:00", freq="h").time
    x_labels = [t.strftime('%H:%M') for t in hours]

    # Función para extraer y alinear los datos de un día
    def get_day_values(day):
        day_data = poa_hourly.loc[day:day + timedelta(hours=23)]
        # Reindexar por hora
        day_data = day_data.groupby(day_data.index.time).mean()
        aligned = pd.Series(day_data, index=hours)  
        return aligned

    poa_max = get_day_values(max_day)
    poa_min = get_day_values(min_day)

    # Hover info
    hover_max = [f"{max_day.date()} {t} - {v:.2f} W/m²" for t, v in zip(x_labels, poa_max)]
    hover_min = [f"{min_day.date()} {t} - {v:.2f} W/m²" for t, v in zip(x_labels, poa_min)]

    # Gráfico
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_labels, y=poa_max, name=f"Día con máxima energía ({max_day.date()})",
                             line=dict(color="red"), mode="lines", hovertext=hover_max, hoverinfo="text"))
    fig.add_trace(go.Scatter(x=x_labels, y=poa_min, name=f"Día con mínima energía ({min_day.date()})",
                             line=dict(color="blue"), mode="lines", hovertext=hover_min, hoverinfo="text"))

    fig.update_layout(
        title="Comparación de irradiancias (POA global) del día de máxima y mínima energía del año",
        xaxis_title="Hora del día",
        yaxis_title="Irradiancia (W/m²)",
        template="plotly_white",
        legend=dict(x=1.02, y=1, xanchor="left"),
        margin=dict(r=100)
    )

    return fig

# 9. Visualizacion de potencia en un día
# #Esta función grafica con líneas sobre el eje x, comprobar con nueva base de datos
# def power_visual_extrdays_1(ac_power):
#     '''
#     Grafica la potencia AC del día máximo y mínimo de energía anual por potencia

#     Parámetros:
#     - ac_power: DataFrame con índice datetime de la potencia AC [W]

#     Return: Gráfico de potencia AC del día máximo y mínimo de un año
#     '''
#     ac_power_hour = ac_power.resample("h").mean() 
#     ac_power_hour_daily = ac_power_hour.resample("D").sum()

#     max_power_day = ac_power_hour_daily.idxmax()
#     min_power_day = ac_power_hour_daily.idxmin()

#     start_maxpow = max_power_day
#     end_maxpow = start_maxpow + timedelta(days=1)
#     start_minpow = min_power_day
#     end_minpow = start_minpow + timedelta(days=1)

#     ac_power_maxday = ac_power.resample("h").mean().loc[start_maxpow:end_maxpow]
#     ac_power_minday = ac_power.resample("h").mean().loc[start_minpow:end_minpow]

#     hours_max = [t.strftime('%H:%M') for t in ac_power_maxday.index.time]
#     hours_min = [t.strftime('%H:%M') for t in ac_power_minday.index.time]
#     hover_max = [f"{dt.strftime('%Y-%m-%d %H:%M')} - {val:.2f} W" for dt, val in zip(ac_power_maxday.index, ac_power_maxday)]
#     hover_min = [f"{dt.strftime('%Y-%m-%d %H:%M')} - {val:.2f} W" for dt, val in zip(ac_power_minday.index, ac_power_minday)]

#     fig = go.Figure()

#     fig.add_trace(go.Scatter(x=hours_max, y=ac_power_maxday.values, mode='lines', name=f'Día con máxima energía ({max_power_day.date()})',line=dict(color='red'), hovertext=hover_max, hoverinfo="text"))
#     fig.add_trace(go.Scatter(x=hours_min, y=ac_power_minday.values, mode='lines', name=f'Día con mínima energía ({min_power_day.date()})',line=dict(color='blue'), hovertext=hover_min, hoverinfo="text"))
    
#     fig.update_layout(
#         title='Comparación de potencia AC del día de máxima y mínima energía del año',
#         xaxis_title='Hora del día',
#         yaxis_title='Potencia AC [W]',
#         xaxis=dict(showgrid=True),
#         yaxis=dict(showgrid=True),
#         template='plotly_white'
#     )

#     return fig

def power_visual_extrdays(ac_power):
    '''
    Grafica la potencia AC del día con máxima y mínima energía anual

    Parámetros:
    - ac_power: Serie o DataFrame con índice datetime y valores de potencia AC [W]

    Return: Gráfico de Plotly con curvas comparativas del día con mayor y menor energía
    '''
    # Promedio horario y energía diaria
    ac_power_hour = ac_power.resample("h").mean()
    ac_power_day = ac_power_hour.resample("D").sum()

    # Días clave
    max_day = ac_power_day.idxmax()
    min_day = ac_power_day.idxmin()

    # Rango horario unificado
    hours = pd.date_range("00:00", "23:00", freq="h").time
    x_labels = [t.strftime('%H:%M') for t in hours]

    # Función para alinear un día a las 24 horas
    def get_day_power(day):
        day_data = ac_power_hour.loc[day:day + timedelta(hours=23)]
        grouped = day_data.groupby(day_data.index.time).mean()
        aligned = pd.Series(grouped, index=hours)
        return aligned

    power_max = get_day_power(max_day)
    power_min = get_day_power(min_day)

    # Hover info
    hover_max = [f"{max_day.date()} {t} - {v:.2f} W" for t, v in zip(x_labels, power_max)]
    hover_min = [f"{min_day.date()} {t} - {v:.2f} W" for t, v in zip(x_labels, power_min)]

    # Gráfico
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_labels, y=power_max, name=f"Día con máxima energía ({max_day.date()})",
                             line=dict(color="red"), mode="lines", hovertext=hover_max, hoverinfo="text"))
    fig.add_trace(go.Scatter(x=x_labels, y=power_min, name=f"Día con mínima energía ({min_day.date()})",
                             line=dict(color="blue"), mode="lines", hovertext=hover_min, hoverinfo="text"))

    fig.update_layout(
        title='Comparación de potencia AC del día de máxima y mínima energía del año',
        xaxis_title='Hora del día',
        yaxis_title='Potencia AC [W]',
        template='plotly_white',
        legend=dict(x=1.02, y=1, xanchor='left'),
        margin=dict(r=100)
    )

    return fig
