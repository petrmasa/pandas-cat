import pandas as pd
from pandas_cat import pandas_cat

# Read dataset. You can download it and set up a path to the local file.
df = pd.read_csv('./accidents.zip',
                 encoding='cp1250', sep='\t')

# Use only selected columns - longer version
df=df[['Driver_Age_Band','Driver_IMD','Sex','Journey','Hit_Objects_in','Hit_Objects_off','Casualties','Severity','Area','Vehicle_Age','Road_Type','Speed_limit','Light','Vehicle_Location','Vehicle_Type']]

df = pandas_cat.prepare(df)

s = ""                          
for column in df:
    s = f"Column {column}:"
    dfc = pd.get_dummies(df[column])
    for col2 in dfc:
        s += f"{col2} "
    print(s)

