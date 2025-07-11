import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
# from utils.config import load_settings
from pathlib import Path
import PySAM.Windpower as wp
import json
import calendar                     
from plotly.subplots import make_subplots
# from utils.config import load_settings
from utils.config import variables, latitude, longitude, gmt, name, site_id, data_tz, wind_speed_height, air_pressure_height, air_temperature_height
# variables, latitude, longitude, gmt, name, alias_map,  site_id, data_tz, wind_speed_height, air_temperature_height, air_pressure_height = load_settings()


alias_map = variables.copy()
variables = variables.keys()


def create_wind_rose_period_plotly(
    df,
    dir_col='WindDir',
    start=None,
    end=None,
    bins=16,
    title=None
):
    """
    genera una rosa de vientos interactiva (Plotly).
    """
    df_period = df.copy()
    if not isinstance(df_period.index, pd.DatetimeIndex):
        df_period.index = pd.to_datetime(df_period.index)
    if start is not None:
        start = pd.to_datetime(start)
    if end is not None:
        end = pd.to_datetime(end)
    if start is not None and end is not None:
        df_period = df_period.loc[start:end]
    if df_period.empty:
        min_d = df.index.min().strftime('%Y-%m-%d')
        max_d = df.index.max().strftime('%Y-%m-%d')
        raise ValueError(
            f"No hay datos en el rango seleccionado ({start.date()} a {end.date()}). "
            f"Rango disponible: {min_d} a {max_d}."
        )
    if title is None and start is not None and end is not None:
        title = f"Rosa de vientos ({start.date()} a {end.date()})"
    return create_wind_rose_plotly(
        df_period,
        dir_col=dir_col,
        bins=bins,
        title=title
    )

def create_wind_rose_by_speed(
    df,
    dir_col='wd',
    speed_col='ws',
    dir_bins=16,
    speed_bins=None,
    title='Rosa de vientos por velocidad'
):
    """
    Genera una rosa de vientos interactiva (Plotly) apilada por categorías de velocidad.

    Parámetros:
    - df: DataFrame con índice datetime y columnas de dirección y velocidad.
    - dir_col: nombre de la columna de dirección en grados.
    - speed_col: nombre de la columna de velocidad.
    - dir_bins: número de sectores de dirección.
    - speed_bins: lista de límites para categorizar velocidad. Ej: [0, 2, 4, 6, 8, np.inf].
    - title: título de la gráfica.
    """
    df2 = df.copy()
    if not isinstance(df2.index, pd.DatetimeIndex):
        df2.index = pd.to_datetime(df2.index)
    if speed_bins is None:
        max_speed = df2[speed_col].max()
        upper = np.ceil(max_speed / 1.5) * 1.5
        bins = np.arange(0, upper + 1e-6, 1.5)
        speed_bins = list(bins)
    speed_labels = []
    for i in range(len(speed_bins)-1):
        low, high = speed_bins[i], speed_bins[i+1]
        if i < len(speed_bins)-2:
            speed_labels.append(f"{low:.1f}–{high:.1f}")
        else:
            speed_labels.append(f">{low:.1f}")

    df2 = df2[[dir_col, speed_col]].dropna()
    
    df2['Velocidad'] = pd.cut(df2[speed_col], bins=speed_bins, labels=speed_labels, right=False)
    deg_bins = np.linspace(0, 360, dir_bins+1)
    deg_labels = [(deg_bins[i] + deg_bins[i+1]) / 2 for i in range(dir_bins)]
    df2['Direccion'] = pd.cut(df2[dir_col] % 360, bins=deg_bins, labels=deg_labels, right=False)
    df_counts = df2.groupby(['Direccion', 'Velocidad'],observed=True).size().reset_index(name='count')
    total = df_counts['count'].sum()
    df_counts['Frecuencia'] = df_counts['count'] / total * 100
    fig = px.bar_polar(
        df_counts,
        r='Frecuencia',
        theta='Direccion',
        color='Velocidad',
        title=title,
        template=None,
        category_orders={'Velocidad': speed_labels}
    )
    fig.update_traces(hovertemplate='Dirección: %{theta}°<br>Frecuencia: %{r:.1f}%')
    fig.update_layout(
        legend_title_text='Velocidad (m/s)'
    )
    return fig

def create_wind_rose_by_speed_period( #ESTA SI 
    df,
    dir_col='wd',
    speed_col='ws',
    start=None,
    end=None,
    dir_bins=16,
    speed_bins=None,
    title=None
):
    """
    Filtra por rango de fechas y genera una rosa interactiva apilada por velocidad.
    """
    dfp = df.copy()
    if not isinstance(dfp.index, pd.DatetimeIndex):
        dfp.index = pd.to_datetime(dfp.index)
    if start is not None:
        start = pd.to_datetime(start)
    if end is not None:
        end = pd.to_datetime(end)
    if start is not None and end is not None:
        dfp = dfp.loc[start:end]
    if dfp.empty:
        min_d = df.index.min().strftime('%Y-%m-%d')
        max_d = df.index.max().strftime('%Y-%m-%d')
        raise ValueError(
            f"No hay datos en el rango seleccionado ({start.date()} a {end.date()}). "
            f"Rango disponible: {min_d} a {max_d}."
        )
    if title is None and start is not None and end is not None:
        title = f"Rosa de vientos por velocidad ({start.date()} a {end.date()})"
    return create_wind_rose_by_speed(
        dfp,
        dir_col=dir_col,
        speed_col=speed_col,
        dir_bins=dir_bins,
        speed_bins=speed_bins,
        title=title
    )


def create_wind_rose_plotly(df, dir_col='WindDir', bins=16, title='Rosa de vientos'):
    """
    Genera una rosa de vientos interactiva (Plotly) a partir de una columna de direcciones en grados,
    mostrando porcentajes.
    """
    values = df[dir_col].dropna().values
    if len(values) == 0:
        raise ValueError(f"La columna '{dir_col}' está vacía o no existe en el DataFrame.")
    angles = np.deg2rad(values)
    bin_edges = np.linspace(0, 2 * np.pi, bins + 1)
    counts, _ = np.histogram(angles, bins=bin_edges)
    total = counts.sum()
    percentages = counts / total * 100
    sector_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    theta_deg = np.rad2deg(sector_centers)

    df_wind = pd.DataFrame({'Frecuencia (%)': percentages, 'Dirección (°)': theta_deg})
    fig = px.bar_polar(
        df_wind,
        r='Frecuencia (%)',
        theta='Dirección (°)',
        color='Frecuencia (%)',
        title=title,
        template=None
    )
    fig.update_traces(hovertemplate='Dirección: %{theta:.0f}°<br>Frecuencia: %{r:.1f}%')
    fig.update_layout(legend_title_text='Frecuencia (%)')
    return fig

def create_seasonal_wind_roses_plotly(
    df,
    dir_col: str = "WindDir",
    bins: int = 16
):
    """
    Devuelve 4 graficas:
    Primavera (3-5), Verano (6-8), Otoño (9-11), Invierno (12,1,2).
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        
        df.index = pd.to_datetime(df.index)

    seasons = {
        "Primavera": [3, 4, 5],
        "Verano":    [6, 7, 8],
        "Otoño":     [9, 10, 11],
        "Invierno":  [12, 1, 2],
    }
    figs = {}
    for name, months in seasons.items():
        df_season = df[df.index.month.isin(months)]
        if df_season.empty:
            figs[name] = None
        else:
            figs[name] = create_wind_rose_plotly(
                df_season,
                dir_col=dir_col,
                bins=bins,
                title=f"Rosa de vientos — {name}"
            )
    return figs


def create_seasonal_wind_roses_by_speed_plotly(#ESTA SI 
    df,
    dir_col='wd',
    speed_col='ws',
    dir_bins=16,
    speed_bins=None
):
    """
    Genera un diccionario de rosas de viento interactivas (Plotly) apiladas por velocidad,
    una por cada estación: Primavera, Verano, Otoño e Invierno.

    Parámetros:
    - df: DataFrame con DatetimeIndex y columnas de dirección y velocidad.
    - dir_col: columna de dirección (grados).
    - speed_col: columna de velocidad (ws).
    - dir_bins: número de sectores direccionales.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    if speed_bins is None:
        speed_bins = [0, 2, 4, 6, 8, np.inf]
    speed_labels = [f"{speed_bins[i]}–{speed_bins[i+1]}" for i in range(len(speed_bins)-1)]
    seasons = {
        'Primavera': [3, 4, 5],
        'Verano':    [6, 7, 8],
        'Otoño':     [9, 10, 11],
        'Invierno':  [12, 1, 2]
    }
    figs = {}
    for name, months in seasons.items():
        df_season = df[df.index.month.isin(months)].copy()
        if df_season.empty:
            figs[name] = None
        else:
            figs[name] = create_wind_rose_by_speed_period(
                df_season,
                dir_col=dir_col,
                speed_col=speed_col,
                dir_bins=dir_bins,
                speed_bins=speed_bins,
                title=None
            )
            figs[name].update_traces(
                hovertemplate='Dirección: %{theta}°<br>Frecuencia: %{r:.1f}%'
            )
            figs[name].update_layout(
                legend_title_text='Velocidad (m/s)',
                polar=dict(angularaxis=dict(rotation=90, direction='clockwise'))
            )
    return figs

def create_typical_wind_heatmap(
    df,
    speed_col="ws",
    start: str | None = None,
    end:   str | None = None,
):
    df2 = df.copy()
    if not isinstance(df2.index, pd.DatetimeIndex):
        df2.index = pd.to_datetime(df2.index)
    if start:
        df2 = df2.loc[pd.to_datetime(start):]
    if end:
        df2 = df2.loc[:pd.to_datetime(end)]

    df2["Month"] = df2.index.month
    df2["Day"]   = df2.index.day
    df2["Hour"]  = df2.index.hour
# 1) Promedio diario típico
    daily = (
        df2
        .groupby(["Month", "Day"])[speed_col]
        .mean()
        .reset_index()
    )
    # 2) Desviación estándar diaria
    daily_std = (
        df2
        .groupby(["Month", "Day"])[speed_col]
        .std()
        .reset_index()
    )

    # 3) Filtrar 29-Feb en ambos
    mask_feb29 = (daily["Month"] == 2) & (daily["Day"] == 29)
    daily    = daily[~mask_feb29]
    daily_std = daily_std[~mask_feb29]

    # 4) Crear columna Date2001 en ambos
    daily["Date2001"] = pd.to_datetime({
        "year":  2001,
        "month": daily["Month"],
        "day":   daily["Day"]
    })
    daily_std["Date2001"] = pd.to_datetime({
        "year":  2001,
        "month": daily_std["Month"],
        "day":   daily_std["Day"]
    })

    # 5) Ordenar por esa fecha y extraer la Serie
    daily_avg = (
        daily
        .sort_values("Date2001")
        .set_index("Date2001")[speed_col]
    )
    daily_std = (
        daily_std
        .sort_values("Date2001")
        .set_index("Date2001")[speed_col]
    )


    hourly = (
        df2
        .groupby("Hour")[speed_col]
        .mean()
        .reset_index()
    )
    hourly_avg = hourly.set_index("Hour")[speed_col]
    hourly_std = df2.groupby(df2.index.hour)[speed_col].std()

    grp = (
        df2
        .groupby(["Month", "Day", "Hour"])[speed_col]
        .mean()
        .reset_index()
    )
    grp = grp[~((grp["Month"] == 2) & (grp["Day"] == 29))]
    grp["Date2001"] = pd.to_datetime(dict(
        year=2001,
        month=grp["Month"],
        day=grp["Day"]
    ))

    pivot = (
        grp
        .pivot(index="Hour", columns="Date2001", values=speed_col)
        .fillna(0.0)
    )

    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type":"scatter"}, None],
               [{"type":"heatmap"},{"type":"scatter"}]],
        row_heights=[0.2,0.8],
        column_widths=[0.9,0.1],
        shared_xaxes=True,
        shared_yaxes=True,
        vertical_spacing=0.001,
        horizontal_spacing=0.001,
    )
    # Banda superior (+1σ) – sin línea, solo hover y leyenda
    fig.add_trace(
        go.Scatter(
            x=daily_avg.index,
            y=daily_avg + daily_std,
            mode="lines",
            line=dict(width=0),
            name="+1σ",
            hoverinfo="y",
            hovertemplate="+1σ: %{y:.2f} m/s<extra></extra>"
        ),
        row=1, col=1
    )

    # Banda inferior (–1σ), rellena desde la traza anterior
    fig.add_trace(
        go.Scatter(
            x=daily_avg.index,
            y=daily_avg - daily_std,
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(0,100,200,0.2)",
            line=dict(width=0),
            name="-1σ",
            hoverinfo="y",
            hovertemplate="-1σ: %{y:.2f} m/s<extra></extra>"
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=daily_avg.index,
            y=daily_avg.values,
            mode="lines",
            name="Promedio diario típico",
            hovertemplate="Día: %{x|%b %d}<br>Vel: %{y:.2f} m/s<extra></extra>"

        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Heatmap(
            z=pivot.values,
            x=list(pivot.columns),
            y=list(pivot.index),
            colorscale="Viridis",
            colorbar=dict(
                title=dict(
                    text="Velocidad (m/s)",  # texto del título
                    side="bottom"           # posición debajo
                ),
                orientation='h',            # horizontal
                len=0.6,
                thickness=20,
                x=0.45,
                xanchor="center",
                y=-0.1,
                yanchor='top',
                ticklen=3,
            ),
            hovertemplate="Día: %{x|%b %d}<br>Hora: %{y}:00<br>Vel: %{z:.2f}<extra></extra>"
        ),
        row=2, col=1
    )
    
    fig.add_trace(
    go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale="Viridis",
        coloraxis="coloraxis",          # <— aquí le decimos que use el coloraxis “coloraxis”
        hovertemplate="Día: %{x|%b %d}<br>Hora: %{y}:00<br>Vel: %{z:.2f}<extra></extra>"
    ),
        row=2, col=1
    )

    # 2) en el layout:
    fig.update_layout(
        coloraxis=dict(
            colorbar=dict(
                title=dict(text="Velocidad (m/s)", side="bottom"),
                orientation="h",
                len=0.6,
                thickness=20,
                x=0.45,
                xanchor="center",
                y=-0.1,
                yanchor="top",
                ticklen=3,
            )
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    # Banda superior horaria (+1σ)
    fig.add_trace(
        go.Scatter(
            x=hourly_avg + hourly_std,
            y=hourly_avg.index,
            mode="lines",
            line=dict(width=0),
            name="+1σ",
            hoverinfo="x",
            hovertemplate="+1σ: %{x:.2f} m/s<extra></extra>"
        ),
        row=2, col=2
    )

    # Banda inferior horaria (–1σ)
    fig.add_trace(
        go.Scatter(
            x=hourly_avg - hourly_std,
            y=hourly_avg.index,
            mode="lines",
            fill="tonextx",
            fillcolor="rgba(0,100,200,0.2)",
            line=dict(width=0),
            name="-1σ",
            hoverinfo="x",
            hovertemplate="-1σ: %{x:.2f} m/s<extra></extra>"
        ),
        row=2, col=2
    )

    fig.add_trace(
        go.Scatter(
            x=hourly_avg.values,
            y=hourly_avg.index,
            mode="lines",
            orientation="h",
            name="Promedio horario típico",
            hovertemplate="Hora: %{y}:00<br>Vel: %{y:.2f} m/s<extra></extra>"

        ),
        row=2, col=2
    )

    fig.update_layout(
        margin=dict(t=30, b=40, l=60, r=40),
        height=600,
        showlegend=False,
    )
    fig.update_xaxes(
        row=2, col=1,
        type="date",
        tickformat="%b %d",
        title_text="Día del año",
    )

    fig.update_yaxes(
        row=2, col=1,
        tickmode="array",
        tickvals=list(range(0,24,2)),
        title_text="Hora del día",
        
    )
    fig.update_xaxes(
        row=1, col=1,
        showgrid=True,
        gridcolor="lightgrey"
    )
    fig.update_yaxes(
        title_text="Velocidad (m/s)", 
        row=1, col=1,
        showgrid=True, gridcolor="lightgrey",
    )
    fig.update_xaxes(
        title_text="Velocidad (m/s)",
        row=2, col=2,
        showgrid=True, gridcolor="lightgrey",
    )
    fig.update_yaxes(
        matches="y2", row=2, col=2,   
        showgrid=True,
        gridcolor="lightgrey")

    return fig


def create_seasonal_wind_heatmaps(
    df,
    speed_col: str = "ws",
    start: str | None = None,
    end:   str | None = None,
):
    """
    Igual que antes, pero cada estación sale con:
      • Serie diaria típica arriba
      • Heatmap estacional abajo-izquierda (colorbar horizontal debajo)
      • Serie horaria típica abajo-derecha
    """
    df2 = df.copy()
    if not isinstance(df2.index, pd.DatetimeIndex):
        df2.index = pd.to_datetime(df2.index)
    if start:
        df2 = df2.loc[pd.to_datetime(start):]
    if end:
        df2 = df2.loc[:pd.to_datetime(end)]

    df2["Month"] = df2.index.month
    df2["Day"]   = df2.index.day
    df2["Hour"]  = df2.index.hour

    season_months = {
        "Primavera": [3, 4, 5],
        "Verano":    [6, 7, 8],
        "Otoño":     [9, 10, 11],
        "Invierno":  [12, 1, 2],
    }

    figs = {}
    for season, meses in season_months.items():
        df_season = df2[df2["Month"].isin(meses)]
        if df_season.empty:
            fig = go.Figure()
            fig.add_annotation(
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                text=f"No hay datos para {season}",
                showarrow=False
            )
            figs[season] = fig
            continue

        daily = (
            df_season
            .groupby(["Month","Day"])[speed_col]
            .mean()
            .reset_index()
        )
        daily = daily[~((daily["Month"]==2)&(daily["Day"]==29))]
        daily["Date2001"] = pd.to_datetime(dict(
            year=2001,
            month=daily["Month"],
            day=daily["Day"]
        ))
        daily = daily.sort_values("Date2001")
        daily_avg = daily.set_index("Date2001")[speed_col]
        
        hourly_avg = (
            df_season
            .groupby("Hour")[speed_col]
            .mean()
        )
        daily_std = (
        df_season
        .groupby(["Month","Day"])[speed_col]
        .std()
        .reset_index()
    )
        daily_std = daily_std[~((daily_std["Month"]==2)&(daily_std["Day"]==29))]
        daily_std["Date2001"] = pd.to_datetime(dict(
            year=2001,
            month=daily_std["Month"],
            day=daily_std["Day"]
        ))
        daily_std = (
            daily_std
            .sort_values("Date2001")
            .set_index("Date2001")[speed_col]
        )

        hourly_std = df_season.groupby("Hour")[speed_col].std()

        grouped = (
            df_season
            .groupby(["Month","Day","Hour"])[speed_col]
            .mean()
            .reset_index()
        )
        grouped = grouped[~((grouped["Month"]==2)&(grouped["Day"]==29))]
        days_per_month = [calendar.monthrange(2001,m)[1] for m in meses]
        min_days = min(days_per_month)
        grouped = grouped[grouped["Day"] <= min_days]

        pivot = (
            grouped
            .groupby(["Day","Hour"])[speed_col]
            .mean()
            .reset_index()
            .pivot(index="Hour", columns="Day", values=speed_col)
            .fillna(0.0)
        )

        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{"type":"scatter"}, None],
                   [{"type":"heatmap"},{"type":"scatter"}]],
            row_heights=[0.2, 0.8],
            column_widths=[0.8, 0.2],
            shared_xaxes=True, shared_yaxes=True,
            vertical_spacing=0.02, horizontal_spacing=0.02,
        )
        fig.add_trace(
            go.Scatter(
                x=daily_avg.index,
                y=(daily_avg + daily_std).values,
                mode="lines",
                line=dict(width=0),
                name="+1σ",
                hoverinfo="y",
                hovertemplate="+1σ: %{y:.2f} m/s<extra></extra>"
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=daily_avg.index,
                y=(daily_avg - daily_std).values,
                mode="lines",
                fill="tonexty",
                fillcolor="rgba(0,100,200,0.2)",  
                line=dict(width=0),
                name="-1σ",
                hoverinfo="y",
                hovertemplate="-1σ: %{y:.2f} m/s<extra></extra>"
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=daily_avg.index,
                y=daily_avg.values,
                mode="lines",
                name="Promedio diario",
                hovertemplate="Día: %{x|%b %d}<br>Vel: %{y:.2f} m/s<extra></extra>"
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Heatmap(
                z=pivot.values,
                x=pivot.columns.astype(str),
                y=pivot.index,
                colorscale="Viridis",
                coloraxis="coloraxis",  
                hovertemplate="Día: %{x}<br>Hora: %{y}:00<br>Vel: %{z:.2f} m/s<extra></extra>"
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=(hourly_avg + hourly_std).values,
                y=hourly_avg.index,
                mode="lines",
                line=dict(width=0),
                name="+1σ",
                hoverinfo="x",
                hovertemplate="+1σ: %{x:.2f} m/s<extra></extra>"
            ),
            row=2, col=2
        )
        fig.add_trace(
            go.Scatter(
                x=(hourly_avg - hourly_std).values,
                y=hourly_avg.index,
                mode="lines",
                fill="tonextx",
                fillcolor="rgba(0,100,200,0.2)",  # mismo color+alpha
                line=dict(width=0),
                name="-1σ",
                hoverinfo="x",
                hovertemplate="-1σ: %{x:.2f} m/s<extra></extra>"
            ),
            row=2, col=2
        )
        fig.add_trace(
            go.Scatter(
                x=hourly_avg.values,
                y=hourly_avg.index,
                mode="lines",
                orientation="h",
                hovertemplate="Hora: %{y}:00<br>Vel: %{x:.2f} m/s<extra></extra>"
            ),
            row=2, col=2
        )
        fig.update_layout(
            height=550,
            margin=dict(t=30, b=40, l=60, r=20),
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",

            coloraxis_colorbar_title_text="Velocidad (m/s)",
            coloraxis_colorbar_title_side="bottom",
            coloraxis_colorbar_orientation="h",
            coloraxis_colorbar_len=0.6,
            coloraxis_colorbar_thickness=20,
            coloraxis_colorbar_x=0.5,
            coloraxis_colorbar_xanchor="center",
            coloraxis_colorbar_y=-0.15,
            coloraxis_colorbar_yanchor="top",
            coloraxis_colorbar_ticklen=3,
        )
        # 2) layout con coloraxis/colorbar bien anidado:
        fig.update_layout(
            height=550,
            margin=dict(t=30, b=40, l=60, r=20),
            showlegend=False,
            title_text=None,
            plot_bgcolor="white",
            paper_bgcolor="white",
            coloraxis=dict(
                colorbar=dict(
                    title=dict(text="Velocidad (m/s)", side="bottom"),
                    orientation="h",
                    x=0.35,
                    xanchor="center",
                    y=-0.1,
                    yanchor="top",
                    len=0.6,
                    thickness=20,
                    ticklen=3,
                )
            )
        )

        # 6) Ejes
        fig.update_xaxes(row=2, col=1, title_text="Día típico", tickmode="array",
                         tickvals=list(pivot.columns)[::5])  
        fig.update_yaxes(row=2, col=1, title_text="Hora del día",
                         tickmode="array", tickvals=list(range(0,24,2)))
        fig.update_xaxes(row=1, col=1, showgrid=True, gridcolor="lightgrey")
        fig.update_yaxes(row=1, col=1, showgrid=True, gridcolor="lightgrey")
        fig.update_xaxes(row=2, col=2, showgrid=True, gridcolor="lightgrey")
        fig.update_yaxes(row=2, col=2, showgrid=True, gridcolor="lightgrey")
        figs[season] = fig

    return figs
def make_sam_wind_csv(
    esolmet: pd.DataFrame,
    ini_path: str = "configuration.ini",
    output_csv: str = "wind_simulation/sam_wind.csv"
) -> Path:
    """
    Genera un CSV TMY (8760 h) compatible con PySAM usando la configuración
    en 'configuration.ini'. Devuelve la ruta al CSV terminado.
    """
    from utils.config import (
        variables,
        latitude,
        longitude,
        gmt,
        name,
        site_id,
        data_tz,
        wind_speed_height,
        air_temperature_height,
        air_pressure_height
    )
    
    alias = variables.copy()
    variables = variables.keys()

    needed_cols = ["ws", "wd", "tdb", "p_atm"]
    df2 = esolmet[needed_cols].copy()

    df2["ws"]    = pd.to_numeric(df2["ws"], errors="coerce")
    df2["wd"]      = pd.to_numeric(df2["wd"],   errors="coerce")
    df2["tdb"]    = pd.to_numeric(df2["tdb"], errors="coerce")
    df2["p_atm"] = pd.to_numeric(df2["p_atm"], errors="coerce")

    df_hourly = df2.resample("1h").agg({
        "ws":    ["mean", "std"],
        "wd":      "mean",
        "tdb":    "mean",
        "p_atm": "mean",
    })
    df_hourly.columns = ["ws", "ws_std", "wd", "tdb", "p_atm"]
    df_hourly = df_hourly.ffill()

    df_hourly.index.name = "fecha"

    df_hourly = df_hourly[~((df_hourly.index.month == 2) & (df_hourly.index.day == 29))]
    df_hourly = df_hourly.ffill()

    df_hourly["p_atm"] = df_hourly["p_atm"] * 100

    df_hourly = df_hourly.reset_index()

    df_hourly = df_hourly.rename(columns={
        "ws":       "wind_speed",
        "wd":       "wind_direction",
        "tdb":   "temperature",
        "p_atm": "pressure"
    })

    df_hourly["Month"] = df_hourly["fecha"].dt.month
    df_hourly["Day"]   = df_hourly["fecha"].dt.day
    df_hourly["Hour"]  = df_hourly["fecha"].dt.hour

    tmy = (
        df_hourly
        .groupby(["Month", "Day", "Hour"])[
            ["wind_speed", "wind_direction", "temperature", "pressure"]
        ]
        .mean()
        .reset_index()
    )
    tmy["Year"] = 2001  

    df_out = tmy[[
        "Year", "Month", "Day", "Hour",
        "wind_speed", "wind_direction", "temperature", "pressure"
    ]]

    header_varnames = [
        "Year", "Month", "Day", "Hour",
        f"wind speed at {int(wind_speed_height)}m (m/s)",
        f"wind direction at {int(wind_speed_height)}m (deg)",
        f"air temperature at {int(air_temperature_height)}m (C)",
        f"air pressure at {int(air_pressure_height)}m (Pa)"
    ]

    loc_row = (
        f"SiteID,{site_id}, Site Timezone,{data_tz},"
        f"Data Timezone,{data_tz},Longitude,{longitude},Latitude,{latitude}\n"
    )
    meta_row = ",".join(header_varnames) + "\n"

    out_path= Path(output_csv)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(loc_row)
        f.write(meta_row)
    df_out.to_csv(
        out_path,
        mode="a",
        index=False,
        header=False,
        sep=",",
    )

    return out_path

def run_wind_simulation(  #ESTA SI 
    esolmet_df,
    turbine_name: str,
    ini_path: str = "configuration.ini",
    wind_turbine_file: str = "wind_simulation/wind-turbines.json",
    wind_inputs_file: str = "wind_simulation/windpower-inputs.json",
    output_csv: str = "wind_simulation/sam_wind.csv",
) -> dict:
    """
    Crea el CSV TMY (vía make_sam_wind_csv), carga PySAM.Windpower,
    fija los parámetros y ejecuta la simulación para la turbina `turbine_name`.
    """

    try:
        csv_path = make_sam_wind_csv(
            esolmet_df,
            ini_path=ini_path,
            output_csv=output_csv,
        )
    except Exception as e:
        return {"error": f"Error al generar el CSV de viento: {e}"}

    wind = wp.new()

    try:
        with open(wind_inputs_file, "r", encoding="utf-8") as f:
            sam_data = json.load(f)
    except FileNotFoundError:
        return {"error": f"No se encontró el archivo '{wind_inputs_file}'"}

    for key, val in sam_data.items():
        if key != "wind_resource_filename":
            wind.value(key, val)

    wind.value("wind_resource_filename", str(csv_path))
    wind.value("wind_resource_shear", 0.14)
    wind.value("wind_farm_wake_model", 0)

    try:
        with open(wind_turbine_file, "r", encoding="utf-8") as f:
            turbine_list = json.load(f)
    except FileNotFoundError:
        return {"error": f"No se encontró el archivo '{wind_turbine_file}'"}

    selected_turbine = next((t for t in turbine_list if t["name"] == turbine_name), None)
    if selected_turbine is None:
        return {"error": f"No existe el modelo “{turbine_name}” en '{wind_turbine_file}'"}

    wind.value("wind_farm_xCoordinates", [0])
    wind.value("wind_farm_yCoordinates", [0])
    wind.value("wind_turbine_rotor_diameter", selected_turbine["rotor_diameter"])
    wind.value("wind_turbine_powercurve_windspeeds", selected_turbine["wind_speeds"])
    wind.value("wind_turbine_powercurve_powerout", selected_turbine["turbine_powers"])
    wind.value("wind_turbine_hub_ht", selected_turbine["hub_height"])

    farm_capacity = 1 * selected_turbine["rated_power"]
    wind.value("system_capacity", farm_capacity)

    try:
        wind.execute()
    except Exception as e:
        msg = str(e)
        if "closest wind speed measurement height" in msg:
            return {
                "error": "No podemos realizar la simulacion con esta turbina debido a las condiciones "
                         "de medición de viento en este sitio."
            }
        return { "error": f"PySAM Windpower execution error: {msg}" }


    annual_energy = getattr(wind.Outputs, "annual_energy", None)
    capacity_factor = getattr(wind.Outputs, "capacity_factor", None)
    wake_losses = getattr(wind.Outputs, "wake_losses", None)
    turb_losses = getattr(wind.Outputs, "turb_losses", None)
    monthly_energy = getattr(wind.Outputs, "monthly_energy", None)
    gen_hourly = wind.Outputs.gen


    if annual_energy is None or capacity_factor is None:
        return {"error": "No se pudieron leer los resultados de PySAM."}

    return {
        "Energia Anual (kWh)": annual_energy,
        "Factor de Capacidad": capacity_factor,
        "Perdida por estela (kWh)": wake_losses,
        "Perdida por turbina (kWh)": turb_losses,
        "Monthly Energy":  monthly_energy,
        "gen": gen_hourly,
 
    }
def create_monthly_energy_figure(monthly_array): #esta si
    """
    Dado un arreglo de 12 valores (energía mensual en kWh), construye
    y devuelve un Plotly.Figure con gráfico de barras:
      - Fondo blanco
      - Cuadrícula gris claro
      - Eje X: meses (Ene, Feb, …)
      - Eje Y: energía en kWh
    """
    if monthly_array is None or len(monthly_array) != 12:
        raise ValueError("El arreglo mensual debe tener exactamente 12 elementos.")
    
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
             "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    fig = go.Figure(
        data=[
            go.Bar(
                x=meses,
                y=monthly_array,
                marker_color="steelblue"
            )
        ]
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis_title="Mes",
        yaxis=dict(
            title_text="Energía (kWh)",
            showgrid=True,
            gridcolor="lightgrey",   
            zeroline=False
        ),
        margin=dict(t=40, b=40, l=40, r=20)
    )
    return fig

def create_seasonal_generation_figures(gen_array): #ESTA SI 
    """
    Dado gen_array (lista o array de 8760 valores horarios de generación),
    construye un índice datetime para un año no bisiesto (2001) con frecuencia 'H', 
    filtra los 3 meses de cada estación (Primavera: 3,4,5; Verano: 6,7,8; Otoño: 9,10,11; Invierno: 12,1,2),
    y para cada estación agrupa por día del mes sumando las 24 h correspondientes para obtener
    un “mes típico” de 28–31 días.
    """

    index = pd.date_range("2001-01-01 00:00", periods=len(gen_array), freq="h")
    df = pd.DataFrame({"gen": gen_array}, index=index)

    season_months = {
        "Primavera": [3, 4, 5],
        "Verano":    [6, 7, 8],
        "Otoño":     [9, 10, 11],
        "Invierno":  [12, 1, 2],
    }

    figs = {}
    for season, meses in season_months.items():
        df_season = df[df.index.month.isin(meses)].copy()

        if df_season.empty:
            figs[season] = go.Figure().add_annotation(
                text=f"No hay datos para {season}",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )
            continue

        df_season["Día"]  = df_season.index.day
        df_season["Hora"] = df_season.index.hour

        daily_hourly = (
            df_season
            .groupby(["Día", "Hora"])["gen"]
            .sum()
            .reset_index()
        )

        daily = (
            daily_hourly
            .groupby("Día")["gen"]
            .sum()
            .reset_index(name="energy_kWh")
        )

        fig = go.Figure(
                    data=[
                        go.Bar(
                            x=daily["Día"].astype(int).astype(str),
                            y=daily["energy_kWh"],
                            name=season,
                            marker_color="steelblue",
                            hovertemplate="Día: %{x}<br>Energía: %{y:.0f} kWh<extra></extra>"
                        )
            ]
        )
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(
                title_text="Día del mes",
                showgrid=True,
                gridcolor="lightgrey",
                zeroline=False
            ),
            yaxis=dict(
                title_text="Energía (kWh)",
                showgrid=True,
                gridcolor="lightgrey",
                zeroline=False
            ),
            margin=dict(t=40, b=30, l=40, r=20),
        )
        figs[season] = fig

    return figs

def create_generation_heatmap(gen_array):
    """
    Dado gen_array (lista o array de 8760 valores horarios de generación),
    construye un índice datetime para un año no bisiesto (2001) con frecuencia 'H',
    luego pinta un heatmap donde:
      - eje x = cada día del año (formato "Ene 01", "Ene 02", ... "Dic 31")
      - eje y = horas del día (0 – 23)

    """

    index = pd.date_range("2001-01-01 00:00", periods=len(gen_array), freq="h")

    df = pd.DataFrame({"gen": gen_array}, index=index)

    df["Date"] = df.index.date
    df["Hour"] = df.index.hour

    pivot = df.pivot(index="Hour", columns="Date", values="gen")

    x_labels = [pd.to_datetime(d).strftime("%b %d") for d in pivot.columns]

    y_vals = pivot.index.tolist()            # [0, 1, 2, ..., 23]
    z_vals = pivot.values                    

    fig = go.Figure(
        data=go.Heatmap(
            x=x_labels,
            y=y_vals,
            z=z_vals,
            colorscale="jet",
            colorbar=dict(
                title=dict(
                    text="Energía(kWh)",
                    side="right"      
                ),
                thickness=18,         
                len=0.85,             
                yanchor="middle",     
                y=0.5                 
            ),
            hovertemplate="Día del año: %{x}<br>Hora: %{y}:00<br>Gen: %{z:.2f} kWh<extra></extra>",
        )
    )

    fig.update_layout(
        xaxis=dict(
            title="Día",
            tickmode="array",
            tickvals=[x_labels[i] for i in range(0, len(x_labels), 20)],
            tickangle=0,
        ),
        yaxis=dict(
            title="Hora",
            tickmode="array",
            tickvals=list(range(0, 24)),
        ),
        margin=dict(t=50, b=120, l=60, r=40),
        height=500,
    )

    return fig
def _build_rose(#ESTA SI
    df: pd.DataFrame,
    dir_col: str,
    speed_col: str,
    dir_bins: int = 16,
    speed_bins=None,
    title: str = None
):
    """
    Función interna que genera la rosa de vientos (Plotly bar_polar)
    a partir de un DataFrame ya filtrado (sin NaNs), etiquetado y recategorizado.
    - df: DataFrame con índice datetime y columnas `dir_col` y `speed_col`.
    - dir_col: nombre de la columna de dirección (en grados 0–360).
    - speed_col: nombre de la columna de velocidad (en m/s).
    - dir_bins: número de sectores para la dirección (default 16).

    """

    df2 = df.copy()

    if not isinstance(df2.index, pd.DatetimeIndex):
        df2.index = pd.to_datetime(df2.index)

    if speed_bins is None:
        max_speed = df2[speed_col].max()
        upper = np.ceil(max_speed / 1.5) * 1.5
        bins = np.arange(0, upper + 1e-6, 1.5)
        speed_bins = list(bins)

    speed_labels = []
    for i in range(len(speed_bins) - 1):
        low, high = speed_bins[i], speed_bins[i + 1]
        if i < len(speed_bins) - 2:
            speed_labels.append(f"{low:.1f}–{high:.1f}")
        else:
            speed_labels.append(f">{low:.1f}")

    df2 = df2[[dir_col, speed_col]].dropna()

    df2["Velocidad"] = pd.cut(
        df2[speed_col],
        bins=speed_bins,
        labels=speed_labels,
        right=False
    )

    deg_bins = np.linspace(0, 360, dir_bins + 1)
    deg_labels = [(deg_bins[i] + deg_bins[i + 1]) / 2 for i in range(dir_bins)]
    df2["Direccion"] = pd.cut(
        df2[dir_col] % 360,
        bins=deg_bins,
        labels=deg_labels,
        right=False
    )

    df_counts = df2.groupby(["Direccion", "Velocidad"]).size().reset_index(name="count")
    total = df_counts["count"].sum()
    df_counts["Frecuencia"] = df_counts["count"] / total * 100

    fig = px.bar_polar(
        df_counts,
        r="Frecuencia",
        theta="Direccion",
        color="Velocidad",
        title=title,
        template=None,
        category_orders={"Velocidad": speed_labels}
    )
    fig.update_traces(hovertemplate="Dirección: %{theta}°<br>Frecuencia: %{r:.1f}%")
    fig.update_layout(legend_title_text="Velocidad (m/s)")

    return fig



def create_wind_rose_by_speed_day(
    df,
    dir_col="wd",
    speed_col="ws",
    *,                     # fuerza que todo lo que venga a partir de aquí sea keyword-only
    start: str | None = None,
    end:   str | None = None,
    dir_bins: int = 16,
    speed_bins = None,
    title: str | None = None,
):
    """
    Filtra por rango y genera la rosa de viento diurna (06:00–18:00).
    """
    df2 = df.copy()
    if not isinstance(df2.index, pd.DatetimeIndex):
        df2.index = pd.to_datetime(df2.index)

    if start:
        df2 = df2.loc[pd.to_datetime(start) : ]
    if end:
        df2 = df2.loc[ : pd.to_datetime(end)]

    df_day = df2.between_time("06:00", "17:59")

    title = title or f" 06:00-17:59 ({start} — {end})"

    return create_wind_rose_by_speed(
        df_day,
        dir_col=dir_col,
        speed_col=speed_col,
        dir_bins=dir_bins,
        speed_bins=speed_bins,
        title=title,
    )



def create_wind_rose_by_speed_night(
    df,
    dir_col="wd",
    speed_col="ws",
    *,
    start: str | None = None,
    end:   str | None = None,
    dir_bins: int = 16,
    speed_bins = None,
    title: str | None = None,
):
    """
    Filtra por rango y genera la rosa de viento nocturna (18:00–06:00).
    """
    df2 = df.copy()
    if not isinstance(df2.index, pd.DatetimeIndex):
        df2.index = pd.to_datetime(df2.index)

    if start:
        df2 = df2.loc[pd.to_datetime(start) : ]
    if end:
        df2 = df2.loc[ : pd.to_datetime(end)]

    noche1 = df2.between_time("18:00", "23:59")
    noche2 = df2.between_time("00:00", "05:59")
    df_night = pd.concat([noche1, noche2])

    title = title or f"18:00-05:59 ({start} — {end})"
    return create_wind_rose_by_speed(
        df_night,
        dir_col=dir_col,
        speed_col=speed_col,
        dir_bins=dir_bins,
        speed_bins=speed_bins,
        title=title,
    )
