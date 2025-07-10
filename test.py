# %% -------------------------------------------------------------------------
# 1. Imports, conexión y DataFrame base
import pandas as pd
import duckdb
import plotly.graph_objects as go


con = duckdb.connect("./climalab.db")
df = (
    con.execute("SELECT * FROM lecturas ORDER BY date")
       .fetchdf()
)
con.close()

df = (
    df.pivot(index="date", columns="variable", values="value")
      .reset_index()
)
df["date"] = pd.to_datetime(df["date"])            # por si no viene como datetime
df.info()

# %%
tdb_maxmin = (
    df
    .resample("D", on="date")              # “D” = frecuencia diaria
    .agg(tdb_min=("tdb", "min"),           # columna nueva con el mínimo
         tdb_max=("tdb", "max"))           # columna nueva con el máximo
    .reset_index()                         # opcional, para volver a tener date como columna
)

tdb_maxmin
# %%
