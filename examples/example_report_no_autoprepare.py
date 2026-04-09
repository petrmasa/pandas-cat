import pandas as pd
from pandas_cat import pandas_cat

# Read dataset. You can download it and set up a path to the local file.
df = pd.read_csv('https://petrmasa.com/pandas-cat/data/accidents.zip',
                 encoding='cp1250', sep='\t')

# Use only selected columns
#df = df[['Driver_Age_Band', 'Driver_IMD', 'Sex', 'Journey']]
df=df[['Driver_Age_Band','Driver_IMD','Sex','Journey','Hit_Objects_in','Hit_Objects_off','Severity','Area','Vehicle_Age','Road_Type','Speed_limit','Light','Vehicle_Location','Vehicle_Type']]


# Generate a profile report with the default template
pandas_cat.profile(df=df, dataset_name="Accidents", out_html="accidents_short_no_auto_prepare.html", opts={"auto_prepare": False})

