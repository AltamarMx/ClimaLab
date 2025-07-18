# %% 
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from utils.config import mean_year_name


# %%
df = pd.read_parquet(mean_year_name)
df.info()
# %%
df.index.month
# %%

# 1) Cálculo diario (igual que antes)
daily = df['tdb_mean'].resample('D').agg(['min','max','mean'])
daily['range'] = daily['max'] - daily['min']
daily.reset_index(inplace=True)
print(daily)
# %%
# 2) Figura única
fig = go.Figure()

# Barra “range” (min→max)
fig.add_trace(go.Bar(
    x=daily['index'],
    y=daily['range'],
    base=daily['min'],
    marker=dict(color='rgba(255,0,0,0.2)'),
    showlegend=False,
    hovertemplate='Min: %{base:.2f}°C<br>Max: %{base + y:.2f}°C<extra></extra>'
))

# Línea de promedio diario
fig.add_trace(go.Scatter(
    x=daily['index'],
    y=daily['mean'],
    mode='lines',
    line=dict(color='red', width=1),
    name='Promedio diario',
    hovertemplate='Promedio: %{y:.2f}°C<extra></extra>'
))

# 3) Layout con range slider
fig.update_layout(
    title='Dry bulb temperature: rango diario + promedio',
    xaxis=dict(
        title='Fecha',
        type='date',
        tickangle=45,
        rangeslider=dict(visible=True),
    ),
    yaxis=dict(title='Dry bulb temperature (°C)'),
    margin=dict(t=60, b=100),
    hovermode='x unified'
)

fig.show()

# %%
px.data.stocks().info()
# %%
