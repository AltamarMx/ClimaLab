# %%
import pandas as pd
from utils.data_processing import load_csv
import missingno as msno

# %%
f = './ClimaLab.parquet'
df = pd.read_parquet(f)
min = df.index.min()
max = df.index.max()
# %%
msno.matrix(df,freq='BQ')


# %%
df.index
# %%
