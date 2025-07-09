# %%    
import pandas as pd
import duckdb

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly_resampler import FigureResampler

#%%
    # 1) Carga y pivoteo
con = duckdb.connect('./climalab.db')
q = f"""
SELECT *
    FROM lecturas
    ORDER BY date
"""
df = con.execute(q).fetchdf()
con.close()
df = df.pivot(index="date", columns="variable", values="value")

# 2) Arrays contiguos
x = np.ascontiguousarray(df.index.to_numpy())
y_tdb  = np.ascontiguousarray(df["tdb"].to_numpy())
y_rh   = np.ascontiguousarray(df["rh"].to_numpy())
y_patm = np.ascontiguousarray(df["p_atm"].to_numpy())
y_ghi  = np.ascontiguousarray(df["ghi"].to_numpy())
y_dni  = np.ascontiguousarray(df["dni"].to_numpy())
y_dhi  = np.ascontiguousarray(df["dhi"].to_numpy())

# 3) Subplots
specs = [
    [{"type": "xy"}, {"type": "polar", "rowspan": 4}],
    [{"type": "xy"}, None],
    [{"type": "xy"}, None],
    [{"type": "xy"}, None],
]
fig = make_subplots(
    rows=4, cols=2,
    shared_xaxes=True,
    column_widths=[0.75, 0.25],
    row_heights=[0.25]*4,
    specs=specs,
    horizontal_spacing=0.05,
    vertical_spacing=0.02,
)

# 4) Remuestreo
fr = FigureResampler(fig, default_n_shown_samples=max_samples)

# 5) Añadir trazas
fr.add_trace(go.Scatter(name="tdb [°C]"), hf_x=x, hf_y=y_tdb, row=1, col=1)
fr.add_trace(go.Scatter(name="rh [%]"), hf_x=x, hf_y=y_rh, row=2, col=1)\
    .update_yaxes(range=[0,100], row=2, col=1)
fr.add_trace(go.Scatter(name="p_atm [Pa]"), hf_x=x, hf_y=y_patm, row=3, col=1)
fr.add_trace(go.Scatter(name="ghi"), hf_x=x, hf_y=y_ghi, row=4, col=1)
fr.add_trace(go.Scatter(name="dni"), hf_x=x, hf_y=y_dni, row=4, col=1)
fr.add_trace(go.Scatter(name="dhi"), hf_x=x, hf_y=y_dhi, row=4, col=1)

# 6) Rosa de vientos
wind = df.dropna(subset=["wd","ws"])
wind_r     = np.ascontiguousarray(wind["ws"].to_numpy())
wind_theta = np.ascontiguousarray(wind["wd"].to_numpy())
fr.add_trace(
    go.Barpolar(r=wind_r, theta=wind_theta, name="Vientos", opacity=0.8),
    row=1, col=2
)

# 7) Ajustes
fr.update_layout(title_text="Lecturas meteorológicas", showlegend=True, height=800)
fr.update_polars(angularaxis=dict(direction="clockwise", rotation=90))
fr.update_xaxes(matches="x")
fr.show()
# %%
