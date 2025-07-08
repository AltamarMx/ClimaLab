# %%
import pandas as pd
from utils.data_processing import load_csv
# %%
f = '../../Desktop/DATOS_ESOLMET_JESUS_QUIÑONES/2025/0129/Esolmet_CR6_IP_Table3_1min.dat'
df = load_csv(f)
# %%
df.info()
# %%
columns = df.columns 
# 1. Reset index to turn 'TIMESTAMP' into a column of type datetime
df = df.reset_index()

# 2. Format 'TIMESTAMP' as text strings for plotting
df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")

# 3. Select the list of variables to plot, excluding the formatted timestamp

# 4. Build the Plotly figure and add a Scattergl trace for each variable
fig = go.Figure()
for var in columns:
    fig.add_trace(
        go.Scattergl(
            x=df.timestamp,          # x-axis: formatted timestamp strings
            y=df[var],               # y-axis: variable values
            mode="markers",         # display markers only
            name=var,                # legend label for this trace
            marker=dict(size=5),     # marker size
        )
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
# %%
