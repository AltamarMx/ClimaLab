# %%
import pandas as pd
import duckdb
from utils.config import mean_year

# %%
con = duckdb.connect('./climalab.db', read_only=True)
query = "SELECT * FROM lecturas ORDER BY date"
df = con.execute(query).fetchdf().pivot(index="date", columns="variable", values="value")

# 2) Quitar 29-feb
df = df[~((df.index.month == 2) & (df.index.day == 29))]
# %%
# 3) Definir las claves de agrupamiento al minuto
keys = [
    df.index.month,      # 1–12
    df.index.day,        # 1–31
    df.index.hour,       # 0–23
    df.index.minute      # 0–59
]

# 4) Agregar media, mínimo y máximo sobre cada grupo
#    Esto te deja un DataFrame con columnas multi-nivel: (variable, aggfunc)
stats = df.groupby(keys).agg(['mean', 'min', 'max'])
stats.columns = ["_".join(col) for col in stats.columns]

stats
# %%
# 5) Aplanar nombres de columnas: p.ej. ghi_mean, ghi_min, ghi_max, dhi_mean, …


# 6) Reconstruir tu índice “año típico” tal como antes
idx = stats.index.to_frame(index=False, name=['month','day','hour','minute'])
typical_dates = pd.to_datetime({
    'year': mean_year,       # año definido en config
    'month': idx['month'],
    'day':   idx['day'],
    'hour':  idx['hour'],
    'minute':idx['minute']
})
stats.index = typical_dates
stats = stats.sort_index()
stats.to_parquet('./database/mean-year.parquet')
# %%


# Ahora `stats` tiene:
#   • stats['ghi_mean'] → promedio anual al minuto  
#   • stats['ghi_min']  → el valor mínimo observado para cada (mes, día, hora, minuto)  
#   • stats['ghi_max']  → el valor máximo observado para cada (mes, día, hora, minuto)  

# 7) Ejemplo de plot con envelope
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12,3))
ax.fill_between(stats.index,
                stats['tdb_min'],
                stats['tdb_max'],
                color='C0', alpha=0.3,
                label='GHI min–max anual')
ax.plot(
        stats['tdb_mean'] ,
        color='C0',
        label='GHI promedio anual')
ax.set_ylabel('GHI [W/m²]')
ax.legend()
plt.show()

# %%
