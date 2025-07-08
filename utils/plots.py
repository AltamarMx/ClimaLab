import pandas as pd
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
from .data_processing import load_csv, radiacion
from .config import variables



def plot_all_variables(df: pd.DataFrame) -> go.Figure:
    """
    Create a Plotly scatter plot for each numeric variable in the DataFrame.
    Uses ``plotly-resampler`` to dynamically downsample large datasets.

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

    # 2. Keep raw timestamps for high-frequency data
    timestamps = df["timestamp"]

    # 3. Select the list of variables to plot, excluding the formatted timestamp
    columns = list(variables.values())
    columns.remove('timestamp')

    # 4. Build the Plotly figure and add a Scattergl trace for each variable
    fig = FigureResampler(go.Figure())
    for var in columns:
        fig.add_trace(
            go.Scattergl(
                mode="markers",
                name=var,
                marker=dict(size=5),
            ),
            hf_x=timestamps,
            hf_y=df[var],
        )

    # 5. Configure layout: unified hover, axis titles, and legend
    fig.update_layout(
        hovermode="x unified",
        showlegend=True,
        xaxis_title="timestamp",
        yaxis_title="Values",
    )

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


def graficado_radiacion(path_archivo: str, rad_columns: list[str] = None) -> go.Figure:
    # 1. cargar datos y calcular radiación nocturna
    df = load_csv(path_archivo)
    df_rad = radiacion(df, rad_columns)

    # 2. preparar TIMESTAMP para graficar
    df_plot = df_rad.reset_index().rename(columns={'index': 'TIMESTAMP'})
    df_plot['TIMESTAMP'] = pd.to_datetime(df_plot['TIMESTAMP'], errors='coerce')
    df_plot = df_plot.dropna(subset=['TIMESTAMP'])
    df_plot['TIMESTAMP'] = df_plot['TIMESTAMP'].dt.strftime('%Y-%m-%d %H:%M')

    # 3. determinar columnas a graficar (excluyendo altura_solar)
    cols_to_plot = [col for col in df_plot.columns if col not in ['TIMESTAMP', 'altura_solar']]

    # 4. construir figura
    fig = go.Figure()
    for col in cols_to_plot:
        fig.add_trace(
            go.Scattergl(
                x=df_plot['TIMESTAMP'],
                y=df_plot[col],
                mode='markers',
                name=col,
                marker=dict(size=5),
            )
        )

    # 5. configurar layout
    fig.update_layout(
        showlegend=True,
        xaxis_title='TIMESTAMP',
        yaxis_title='Valores',
    )
    fig.update_xaxes(showgrid=True, tickformat='%Y-%m-%d %H:%M', tickmode='auto')
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


# def graficado_nulos(df):
#     na_counts = df.isna().sum()
#     cols_with_na = na_counts[na_counts > 0].index.tolist()
#     if not cols_with_na:
#         fig = plt.figure(figsize=(8, 4))
#         fig.suptitle("Sin valores nulos")
#         return fig

#     fig, ax = plt.subplots(
#         figsize=(
#             max(14, 0.6 * len(cols_with_na)),
#             8
#         )
#     )
#     msno.bar(
#         df[cols_with_na],
#         ax=ax,
#         fontsize=10,
#         sort="descending"
#     )

#     plt.setp(ax.get_xticklabels(), ha="right")
#     ax.grid(axis="y", alpha=0.3)
#     ax.set_ylabel("Proporción")

#     if len(fig.axes) > 1:
#         fig.axes[1].set_ylabel("Conteo")

#     return fig
