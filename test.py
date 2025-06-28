# %%

import plotly.graph_objects as go
from utils.data_processing import load_csv
import pandas as pd
from utils.config import variables
# %%


# 3. determinar qué variables graficar (descartar la columna TIMESTAMP)


# %%
f = 'data/Esolmet_CR6_IP_TableWEB_10min.csv'
df  = load_csv(f)


df = df.reset_index()  # ahora 'TIMESTAMP' es columna de tipo datetime
df["timestamp"] = df["TIMESTAMP"].dt.strftime("%Y-%m-%d %H:%M")

columns =  list(variables.values())
columns.remove('timestamp')
columns


# 4. construir figura
fig = go.Figure()
for var in columns:
    fig.add_trace(
        go.Scattergl(
            x = df.timestamp,
            y = df[var],
            mode = "markers",
            name = var,
            marker = dict(size=5),
        )
    )

# 5. configurar layout
fig.update_layout(
    hovermode = "x unified",
    showlegend = True,
    xaxis_title = "timestamp",
    yaxis_title = "Values",
)
fig.update_xaxes(
    showgrid = True,
    tickformat = "%Y-%m-%d %H:%M",
    tickmode = "auto",
)
fig.update_yaxes(showgrid = True)

# %%
