import pandas as pd
from pandas_cat import pandas_cat

# Read dataset. You can download it and set up a path to the local file.
df = pd.read_csv('https://petrmasa.com/pandas-cat/data/accidents.zip',
                 encoding='cp1250', sep='\t')

# Use only selected columns
df = df[['Driver_Age_Band', 'Driver_IMD', 'Sex', 'Journey']]


# Generate a profile report with the default template
pandas_cat.profile(df=df, dataset_name="Accidents", out_html="accidents_short.html", opts={"auto_prepare": True})

