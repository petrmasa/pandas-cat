# pandas-cat

<img alt="PyPI - License" src="https://img.shields.io/pypi/l/pandas-cat">
<img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/pandas-cat">
<img alt="PyPI - Wheel" src="https://img.shields.io/pypi/wheel/pandas-cat">
<img alt="PyPI - Status" src="https://img.shields.io/pypi/status/pandas-cat">
<img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/pandas-cat">


## The pandas-cat is a Pandas's categorical profiling library. 

pandas-cat is abbreviation of PANDAS-CATegorical profiling. This package provides profile for categorical attributes as well as (optional) adjustments of data set, e.g. estimating whether variable is numeric and order categories with respect to numbers etc.

## The pandas-cat in more detail

The package creates (html) profile of the categorical dataset. It supports both ordinal (ordered) categories as well as nominal ones. Moreover, it overcomes typical issues with categorical, mainly ordered data that are typically available, like that categories are de facto numbers, or numbers with some enhancement and should be treated as ordered.	

For example, in dataset *Accidents* 

attribute Hit Objects in can be used as: 
- *unordered*: 0.0 10.0 7.0 11.0 4.0 2.0 8.0 1.0 9.0 6.0 5.0 12.0 nan 
- *ordered*: 0.0 1.0 10.0 11.0 12.0 2.0 4.0 5.0 6.0 7.0 8.0 9.0 nan 
- *as analyst wishes (package does)*: 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0 nan 

Typical issues are (numbers are nor numbers):
- categories are intervals (like 75-100, 101-200)
- have category with some additional information (e.g. Over 75, 60+, <18, Under 16)
- have n/a category explicitly coded sorted in data


Therefore this library provides profiling as well as somehow automatic data preparation.


Currently, there are two methods in place:

- `profile` -- profiles a dataset, categories and their correlations
- `prepare` -- prepares a dataset, tries to understand label names (if they are numbers) and sort them


## Installation

You can install the package using 

`pip install pandas-cat`

## Usage

The usage of this package is simple. Sample code follows (it uses dataset [Accidents](https://petrmasa.com/pandas-cat/data/accidents.zip) based on [Kaggle dataset](https://www.kaggle.com/code/ambaniverma/uk-traffic-accidents))

```
import pandas as pd
from pandas_cat import pandas_cat

#read dataset. You can download it and setup path to local file.
df = pd.read_csv ('https://petrmasa.com/pandas-cat/data/accidents.zip', encoding='cp1250', sep='\t')

#use only selected columns
df=df[['Driver_Age_Band','Driver_IMD','Sex','Journey']]

#longer demo report uses this set of columns instead of the first one
#df=df[['Driver_Age_Band','Driver_IMD','Sex','Journey','Hit_Objects_in','Hit_Objects_off','Casualties','Severity','Area','Vehicle_Age','Road_Type','Speed_limit','Light','Vehicle_Location','Vehicle_Type']]


#for profiling, use following code
pandas_cat.profile(df=df,dataset_name="Accidents",opts={"auto_prepare":True})

#for just adjusting dataset, use following code

df = pandas_cat.prepare(df)
```

## Data and sample reports

Sample reports are here - [basic](https://petrmasa.com/pandas-cat/sample/report1.html) and [longer](https://petrmasa.com/pandas-cat/sample/report2.html). Note that these reports have been generated with code above.

The dataset is downloaded from the web (each time you run the code). If you want, you can download sample dataset [here](https://petrmasa.com/pandas-cat/data/accidents.zip) and store it locally.



