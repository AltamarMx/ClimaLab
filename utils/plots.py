import pandas as pd
import plotly.graph_objects as go
from windrose import WindroseAxes
from matplotlib.gridspec import GridSpec   
import numpy as np

from plotly.subplots import make_subplots

from utils.data_processing import load_csv, radiacion
from utils.config import variables
from utils.config import db_name

import missingno as msno
import matplotlib
import duckdb


matplotlib.use("Agg")
import matplotlib.pyplot as plt




import plotly.graph_objects as go
# from plotly_resampler import FigureWidgetResampler, register_plotly_resampler
# from plotly_resampler.aggregation import FuncAggregator

# Enable dynamic resampling when working in widget based environments
# register_plotly_resampler(mode="widget")


def graph_all_matplotlib(fechas, alias_dict=None,db_path=db_name):

    # 1) No es necesario usar alias; las columnas ya tienen nombres universales
    con = duckdb.connect(db_path)
    
    # 2) Carga y pivoteo
    query = f"""
    SELECT *
      FROM lecturas
     WHERE date >= TIMESTAMP '{fechas[0]}'
       AND date <= TIMESTAMP '{fechas[1]}'
     ORDER BY date
    """
    df = con.execute(query).fetchdf()
    df = df.pivot(index="date", columns="variable", values="value")

    # 3) Figure + GridSpec
    fig = plt.figure()
    # fig.set_constrained_layout(True)

    gs = GridSpec(
        nrows=4,
        ncols=2,
        width_ratios=[4, 1],
        height_ratios=[1, 1, 1, 1],
        #    wspace=0.1, hspace=0.1,
        figure=fig,
    )

    ax_tdb = fig.add_subplot(gs[0, 0])
    ax_rh = fig.add_subplot(gs[1, 0], sharex=ax_tdb)
    ax_p = fig.add_subplot(gs[2, 0], sharex=ax_tdb)
    ax_i = fig.add_subplot(gs[3, 0], sharex=ax_tdb)
    ax_wind = fig.add_subplot(gs[:, 1], projection="windrose")


    # Graficar temperatura
    ax_tdb.plot(df.index, df.tdb, label="tdb", c="k", alpha=0.8)
    ax_tdb.set_ylabel("Temperatura [°C]")
    ax_tdb.legend(loc="upper left")

    # Graficar presión
    ax_p.plot(df.p_atm, label="p_atm", alpha=0.8)
    ax_p.set_ylabel("Presión [Pa]")
    ax_p.legend(loc="upper left")

    # Graficar Is
    ax_i.plot(df.index, df.ghi, label="ghi")
    ax_i.plot(df.index, df.dni, label="dni")
    ax_i.plot(df.index, df.dhi, label="dhi")
    ax_i.set_ylabel("Irradiancia [W/m2]")
    ax_i.legend(loc="upper left")

    # Graficar humedad relativa hr
    ax_rh.plot(df.rh, label="rh")
    ax_rh.set_ylim(0, 100)
    ax_rh.set_ylabel("HR [%]")
    ax_rh.legend()

    # 5) Rosa de vientos
    ax_wind.bar(df.wd, df.ws, normed=True, opening=0.8, edgecolor="white")
    ax_wind.set_title("Rosa de Vientos")

    # 6) Formato de fecha en eje X
    fig.autofmt_xdate()

    return fig





def graph_all_plotly_resampler(fechas=None, db_path=db_name):
    """Return a Plotly figure with dynamic resampling enabled.

    Parameters
    ----------
    fechas : tuple[str, str] | None
        Optional start/end dates in ISO format ``YYYY-MM-DD``. When provided,
        only records within this interval are loaded from the database.
    db_path : str
        Path to the DuckDB database.
    """

    # 1) Load data and pivot into wide format
    con = duckdb.connect(db_path)

    if fechas is None:
        q = """
        SELECT *
          FROM lecturas
         ORDER BY date
        """
    else:
        q = f"""
        SELECT *
          FROM lecturas
         WHERE date >= TIMESTAMP '{fechas[0]}'
           AND date <= TIMESTAMP '{fechas[1]}'
         ORDER BY date
        """
    df = con.execute(q).fetchdf()
    con.close()
    df = df.pivot(index="date", columns="variable", values="value")

    # 2) Prepare timestamps for plotting
    df = df.reset_index()
    df["timestamp"] = df["date"]
    
    tdb = (
        df
        .resample("D", on="date")              # “D” = frecuencia diaria
        .agg(tdb_min=("tdb", "min"),           # columna nueva con el mínimo
            tdb_max=("tdb", "max"),
            tdb_mean=('tdb','mean')
            )           # columna nueva con el máximo
        .reset_index()                         # opcional, para volver a tener date como columna
    )
    
    hourly = (
        df
        .resample("h", on="date")
        .agg(
            dni_mean=("dni", "max"),
            dhi_mean=("dhi", "max"),
            ghi_mean=("ghi", "max"),
        )
        .reset_index()
    )


    # %% -------------------------------------------------------------------------
    # 4) Crear subplots: fila 1 = TDB, fila 2 = irradiancias
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        # subplot_titles=(
        #     "TDB diario (min–max + media)",
        #     "Irradiancias horario (DNI, DHI, GHI)",
        # )
    )

    # — TDB (fila 1) —
    # techo invisible
    fig.add_trace(
        go.Scatter(
            x=tdb["date"], y=tdb["tdb_max"],
            line=dict(width=0), showlegend=False, hoverinfo="skip"
        ),
        row=1, col=1
    )
    # banda min–max
    fig.add_trace(
        go.Scatter(
            x=tdb["date"], y=tdb["tdb_min"],
            fill="tonexty", fillcolor="rgba(255,0,0,0.2)",
            line=dict(width=0),
            hovertemplate="Min: %{y:.1f} °C<br>Max: %{customdata:.1f} °C",
            customdata=tdb["tdb_max"],
            showlegend=False
        ),
        row=1, col=1
    )
    # media diaria
    fig.add_trace(
        go.Scatter(
            x=tdb["date"], y=tdb["tdb_mean"],
            line=dict(color="red", width=2),
            name="TDB media",
            hovertemplate="Media: %{y:.1f} °C", 
            showlegend=False
        ),
        row=1, col=1
    )

    # — Irradiancias (fila 2) —
    fig.add_trace(
        go.Scatter(
            x=hourly["date"], y=hourly["dni_mean"],
            mode="lines", 
            name="DNI",
            hovertemplate="DNI: %{y:.1f} W/m²",
            showlegend=False
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=hourly["date"], y=hourly["dhi_mean"],
            mode="lines", 
            name="DHI",
            hovertemplate="DHI: %{y:.1f} W/m²",
            showlegend=False
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=hourly["date"], y=hourly["ghi_mean"],
            mode="lines", 
            name="GHI",
            hovertemplate="GHI: %{y:.1f} W/m²",
            showlegend=False
        ),
        row=2, col=1
    )

    # %% -------------------------------------------------------------------------
    # 5) Layout y controles de rango
    fig.update_layout(
        template="ggplot2",
        hovermode="x unified",
        xaxis=dict(
            autorange=True,
            rangeslider=dict(
                autorange=True,
            ),
            type="date"
    ),
        # margin=dict(t=60, b=40, l=60, r=10),
    )

    # Sólo al eje x de la fila 2 (inferior) le asignamos rangeselector + rangeslider
    fig.update_xaxes(
        rangeselector=dict(
            buttons=[
                dict(count=1,  label="1 m", step="month", stepmode="backward"),
                dict(count=6,  label="6 m", step="month", stepmode="backward"),
                # dict(count=1,  label="YTD", step="year",  stepmode="todate"),
                dict(count=1,  label="1 a", step="year",  stepmode="backward"),
                dict(step="all", label="Todo")
            ]
        ),
        # rangeslider=dict(visible=True),
        # type="date",
        row=1, col=1
    )


    # Etiquetas de ejes
    fig.update_yaxes(title_text="TDB (°C)", row=1, col=1)
    fig.update_yaxes(title_text="Irradiancia (W/m²)", row=2, col=1)
    fig.update_xaxes(title_text="Fecha", row=2, col=1)



    return fig

def plot_all_variables(df: pd.DataFrame) -> go.Figure:
    """
    Create a Plotly scatter plot for each numeric variable in the DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with a DatetimeIndex named 'TIMESTAMP' and numeric columns to plot.

    Returns
    -------
    plotly.graph_objs._figure.Figure
        A Plotly figure containing a scatter trace for each variable.
    """

    # 1. Reset index to turn 'TIMESTAMP' into a column of type datetime
    df = df.reset_index()

    # 2. Format 'TIMESTAMP' as text strings for plotting
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")

    # 3. Select the list of variables to plot, excluding the formatted timestamp
    columns = list(variables.values())
    columns.remove("timestamp")

    # 4. Build the Plotly figure and add a Scattergl trace for each variable
    fig = go.Figure()
    for var in columns:
        fig.add_trace(
            go.Scattergl(
                x=df.timestamp,  # x-axis: formatted timestamp strings
                y=df[var],  # y-axis: variable values
                mode="markers",  # display markers only
                name=var,  # legend label for this trace
                marker=dict(size=5),  # marker size
            )
        )

    # # 5. Configure layout: unified hover, axis titles, and legend
    fig.update_layout(
        hovermode="x unified",
        showlegend=True,
        xaxis_title="timestamp",
        yaxis_title="Values",
    )

    # 3) Si usas Plotly Express, añade también:
    # fig.update_traces(hoverinfo='skip', hovertemplate=None)

    # 6. Configure x-axis: grid, tick format, and automatic ticks
    fig.update_xaxes(
        showgrid=True,
        tickformat="%Y-%m-%d %H:%M",
        tickmode="auto",
    )

    # 7. Configure y-axis to show grid lines
    fig.update_yaxes(showgrid=True)

    # 8. Return the completed figure
    return fig


def plot_missingno(df: pd.DataFrame):
    """ """
    fig, ax = plt.subplots(layout="constrained")
    fig = msno.matrix(df, ax=ax, fontsize=7, sparkline=False)

    # fig = msno.matrix(df,fontsize=7)

    return fig


def plot_all(df: pd.DataFrame, columns: list[str] | None = None):
    """Plot selected columns of *df* using Matplotlib."""

    if columns is None:
        columns = list(df.columns)

    fig, ax = plt.subplots()

    for column in columns:
        ax.plot(df[column], label=column)

    if columns:
        ax.legend()

    return fig


def graficado_radiacion(path_archivo: str, rad_columns: list[str] = None) -> go.Figure:
    # 1. cargar datos y calcular radiación nocturna
    df = load_csv(path_archivo)
    df_rad = radiacion(df, rad_columns)

    # 2. preparar TIMESTAMP para graficar
    df_plot = df_rad.reset_index().rename(columns={"index": "TIMESTAMP"})
    df_plot["TIMESTAMP"] = pd.to_datetime(df_plot["TIMESTAMP"], errors="coerce")
    df_plot = df_plot.dropna(subset=["TIMESTAMP"])
    df_plot["TIMESTAMP"] = df_plot["TIMESTAMP"].dt.strftime("%Y-%m-%d %H:%M")

    # 3. determinar columnas a graficar (excluyendo altura_solar)
    cols_to_plot = [
        col for col in df_plot.columns if col not in ["TIMESTAMP", "altura_solar"]
    ]

    # 4. construir figura
    fig = go.Figure()
    for col in cols_to_plot:
        fig.add_trace(
            go.Scattergl(
                x=df_plot["TIMESTAMP"],
                y=df_plot[col],
                mode="markers",
                name=col,
                marker=dict(size=5),
            )
        )

    # 5. configurar layout
    fig.update_layout(
        showlegend=True,
        xaxis_title="TIMESTAMP",
        yaxis_title="Valores",
    )
    fig.update_xaxes(showgrid=True, tickformat="%Y-%m-%d %H:%M", tickmode="auto")
    fig.update_yaxes(showgrid=True)

    return fig


def plot_cleaned_radiation(df: pd.DataFrame) -> go.Figure:
    """Plot irradiance data highlighting detected outliers per variable."""

    df_plot = df.reset_index()
    # df_plot = df.copy()
    df_plot["timestamp"] = df_plot["timestamp"].dt.strftime("%Y-%m-%d %H:%M")

    fig = go.Figure()
    irr_cols = [c for c in ["dni", "ghi", "dhi"] if c in df_plot.columns]

    colors = {"dni": "#1f77b4", "ghi": "#2ca02c", "dhi": "#ff7f0e"}
    for col in irr_cols:
        flag = df_plot.get(f"{col}_outlier", pd.Series(False, index=df_plot.index))
        fig.add_trace(
            go.Scattergl(
                x=df_plot.loc[~flag, "timestamp"],
                y=df_plot.loc[~flag, col],
                mode="markers",
                name=col,
                marker=dict(size=5, color=colors.get(col, "blue")),
            )
        )
        fig.add_trace(
            go.Scattergl(
                x=df_plot.loc[flag, "timestamp"],
                y=df_plot.loc[flag, col],
                mode="markers",
                name=f"{col} outlier",
                marker=dict(size=7, color="red", symbol="x"),
            )
        )

    fig.update_layout(
        hovermode="x unified",
        showlegend=True,
        xaxis_title="timestamp",
        yaxis_title="Irradiance [W/m²]",
    )
    fig.update_xaxes(showgrid=True, tickformat="%Y-%m-%d %H:%M", tickmode="auto")
    fig.update_yaxes(showgrid=True)

    return fig




def plot_explorer_matplotlib(fechas, alias_dict=None):

    # 1) No es necesario usar alias; las columnas ya tienen nombres universales
    con = duckdb.connect(db_name)

    # 2) Carga y pivoteo
    query = f"""
    SELECT *
      FROM lecturas
     WHERE fecha >= TIMESTAMP '{fechas[0]}'
       AND fecha <= TIMESTAMP '{fechas[1]}'
     ORDER BY fecha
    """
    df = con.execute(query).fetchdf()
    df = df.pivot(index="fecha", columns="variable", values="valor")

    # 3) Figure + GridSpec
    fig = plt.figure()
    # fig.set_constrained_layout(True)

    gs = GridSpec(
        nrows=4,
        ncols=2,
        width_ratios=[4, 1],
        height_ratios=[1, 1, 1, 1],
        #    wspace=0.1, hspace=0.1,
        figure=fig,
    )

    ax_tdb = fig.add_subplot(gs[0, 0])
    ax_rh = fig.add_subplot(gs[1, 0], sharex=ax_tdb)
    ax_p = fig.add_subplot(gs[2, 0], sharex=ax_tdb)
    ax_i = fig.add_subplot(gs[3, 0], sharex=ax_tdb)
    ax_wind = fig.add_subplot(gs[:, 1], projection="windrose")


    # Graficar temperatura
    ax_tdb.plot(df.index, df.tdb, label="tdb", c="k", alpha=0.8)
    ax_tdb.set_ylabel("Temperatura [°C]")
    ax_tdb.legend(loc="upper left")

    # Graficar presión
    ax_p.plot(df.p_atm, label="p_atm", alpha=0.8)
    ax_p.set_ylabel("Presión [Pa]")
    ax_p.legend(loc="upper left")

    # Graficar Is
    ax_i.plot(df.index, df.ghi, label="ghi")
    ax_i.plot(df.index, df.dni, label="dni")
    ax_i.plot(df.index, df.dhi, label="dhi")
    ax_i.set_ylabel("Irradiancia [W/m2]")
    ax_i.legend(loc="upper left")

    # Graficar humedad relativa hr
    ax_rh.plot(df.rh, label="rh")
    ax_rh.set_ylim(0, 100)
    ax_rh.set_ylabel("HR [%]")
    ax_rh.legend()

    # 5) Rosa de vientos
    ax_wind.bar(df.wd, df.ws, normed=True, opening=0.8, edgecolor="white")
    ax_wind.set_title("Rosa de Vientos")

    # 6) Formato de fecha en eje X
    fig.autofmt_xdate()

    return fig
