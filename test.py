# %% 
import pandas as pd
import matplotlib.pyplot as plt
import duckdb 
from matplotlib.gridspec import GridSpec   



# %%

con = duckdb.connect('./climalab.db', read_only=True)

# 2)z Carga y pivoteo
query = f"""
SELECT *
FROM lecturas
ORDER BY date
"""
df = con.execute(query).fetchdf()
df = df.pivot(index="date", columns="variable", values="value")

# 2) (Opcional) Elimina el 29-Feb para evitar que años bisiestos distorsionen:
df = df[~((df.index.month == 2) & (df.index.day == 29))]


# %%

# 3) Genera las claves de agrupamiento
keys = [
    df.index.month,      # 1–12
    df.index.day,        # 1–31
    df.index.hour,       # 0–23
    df.index.minute      # 0–59
]

keys
# %%
yearly_typical = df.groupby(keys).mean()

yearly_typical
# %%

# 5) Reconstruye un índice datetime genérico (pongamos año 2000):
#    Convertimos el índice multinivel a DataFrame...
idx = yearly_typical.index.to_frame(index=False, name=['month','day','hour','minute'])
#    y creamos fechas eligiendo un año arbitrario:
typical_dates = pd.to_datetime({
    'year': 2000,
    'month': idx['month'],
    'day':   idx['day'],
    'hour':  idx['hour'],
    'minute':idx['minute']
})
# 6) Asigna ese nuevo índice y ordena
yearly_typical.index = typical_dates
yearly_typical = yearly_typical.sort_index()

# Ahora `yearly_typical` es un DataFrame con un año “promedio”:
print(yearly_typical.head())
# %%

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