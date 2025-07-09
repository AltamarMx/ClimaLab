import matplotlib.pyplot as plt

import duckdb
from utils.config import db_name







def graficado_Todo_matplotlib():

    fig, ax = plt.subplots()
    columnas = esolmet.columns
    for columna in columnas:
        ax.plot(esolmet[columna], label=columna)
    # ax.set_ylabel("Irradiancia [W/m2]")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2)
    ax.legend()
    return fig
