import pandas as pd
from pandas_cat import pandas_cat

# Read dataset. You can download it and set up a path to the local file.
df = pd.read_csv('https://petrmasa.com/pandas-cat/data/accidents.zip',
                 encoding='cp1250', sep='\t')

df=df[['Driver_Age_Band','Driver_IMD','Sex','Journey','Hit_Objects_in','Hit_Objects_off','Severity','Area','Vehicle_Age','Road_Type','Speed_limit','Light','Vehicle_Location','Vehicle_Type']]

pandas_cat.profile(df=df, dataset_name="Accidents", template="interactive",out_html="accidents_interactive_report.html")
