# %%
import pandas as pd
from utils.config import variables
import matplotlib.pyplot as plt
from utils.plots import plot_all
# %%
df = pd.read_parquet("./ClimaLab.parquet")
df.info()
# %%

columns = list(variables.values())
columns.remove("timestamp")

fig, ax = plt.subplots(len(df.columns),1,sharex=True)

ax = ax.flatten()
for i,column in enumerate(columns):
    ax[i].plot(df[column],label=column)


# %%
columns