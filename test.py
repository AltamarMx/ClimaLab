# %% 
import pandas as pd
import matplotlib.pyplot as plt
import duckdb 
from matplotlib.gridspec import GridSpec   
from windrose import WindroseAxes


# %%

con = duckdb.connect('./climalab.db', read_only=True)

# 2)z Carga y pivoteo
query = f"""
SELECT *
FROM lecturas
WHERE date >= TIMESTAMP '2024-01-01'
AND date <= TIMESTAMP '2024-06-01'
ORDER BY date
"""
df = con.execute(query).fetchdf()
df = df.pivot(index="date", columns="variable", values="value")
fecha_min = df.index.min()
fecha_max = df.index.max()
delta_dias = fecha_max - fecha_min
delta_dias
df
# %%
if delta_dias <= pd.Timedelta('120D'):
    pass
else:
    tdb = df.resample('D').tdb.agg(['max','min','mean'])
    rh = df.resample('D').rh.agg(['max','min','mean'])
    p_atm = df.resample('D').p_atm.agg(['max','min','mean'])


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
    ax_tdb.fill_between(
        tdb.index,
        tdb['min'],    # columna “min”
        tdb['max'],    # columna “max”
        alpha=0.3,
        color='k',
        label='tdb'
    )
    ax_tdb.plot(
        tdb.index,
        tdb['mean'],   # columna “mean”
        color='k',
        lw=1.5
    )
    

    ax_tdb.set_ylabel("Temperatura [°C]")
    ax_tdb.legend(loc="upper left")

    # Graficar hr
    
    ax_rh.fill_between(
        rh.index,
        rh['min'],    # columna “min”
        rh['max'],    # columna “max”
        alpha=0.3,
    )
    ax_rh.plot(
        rh.index,
        rh['mean'],   # columna “mean”
        color='k',
        lw=1.5,
    )
    ax_rh.set_ylabel('HR [%]')
    # ax_p.set_ylabel("Presión [Pa]")
    # ax_p.legend(loc="upper left")

    # Graficar Is
    # ax_i.plot(df.index, df.ghi, label="ghi")
    # ax_i.plot(df.index, df.dni, label="dni")
    # ax_i.plot(df.index, df.dhi, label="dhi")
    # ax_i.set_ylabel("Irradiancia [W/m2]")
    # ax_i.legend(loc="upper left")

    # Graficar humedad relativa hr
    # ax_rh.plot(df.rh, label="rh")
    # ax_rh.set_ylim(0, 100)
    # ax_rh.set_ylabel("HR [%]")
    # ax_rh.legend()

    # 5) Rosa de vientos
    # ax_wind.bar(df.wd, df.ws, normed=True, opening=0.8, edgecolor="white")
    # ax_wind.set_title("Rosa de Vientos")

    # 6) Formato de fecha en eje X
    # fig.autofmt_xdate()
    # fig.show()

# %%
tdb = df.resample('D').tdb.agg(['max','min','mean'])
tdb
# %%
