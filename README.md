# pandas-cat

<img alt="PyPI - License" src="https://img.shields.io/pypi/l/pandas-cat">
<img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/pandas-cat">
<img alt="PyPI - Wheel" src="https://img.shields.io/pypi/wheel/pandas-cat">
<img alt="PyPI - Status" src="https://img.shields.io/pypi/status/pandas-cat">
<img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/pandas-cat">

## The pandas-cat is a Pandas's categorical utils library.

pandas-cat is abbreviation of PANDAS-CATegorical utils. This package provides 

* *automatic ordering for ordinal variables* - a lightweigth module for converting string categories to ordered ones if possible (based on numbers inside texts, like "Over 25"
* *advanced missing value detection* - detection of typical missing data encoding (typical = detect encodings that we have manually identified in more than 100+ datasets)
* *categorical data profiling* - profile for categorical attributes

## The pandas-cat in more detail

### Ordinal data ordering

This package tries to convert strings to ordered categories. For example (`Vehicle_Age` in Accidents dataset),

```
ORIGINAL (unordered)                                           : 1 6 5 4 9 14 >20 10 8 15 12 11 16-20 3 13 2 7   
ALPHABETICALLY ORDERED (strings do not allow numeric ordering) : >20 1 10 11 12 13 14 15 16-20 2 3 4 5 6 7 8 9 
AS ANALYST WISHES (package does)                               : 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16-20 >20
```

Typical issues are (numbers are nor numbers):

- categories are intervals (like 75-100, 101-200)
- have category with some additional information (e.g. Over 75, 60+, <18, Under 16)
- have n/a or other string category explicitly coded sorted in data


### Missing detection and replacement

Missing values are typically encoded in many ways (`N/A`, `#N/A`, `NA`, `invalid`, `NO INFO`, `NOT RATED`, `NOT GIVEN`, `NOT DEFINED`, `undefined`, ...). We have manually went through more than 100 datasets with missing values and detected typical encoding of missing values and added to this library as an automatic missing detection and replacement. 

The build-in list can be easily extended (by adding next strings as parameters). Also, when some string should be preserved, package can be instructed to keep it.

### Profiling 

The package creates (html) profile of the categorical dataset. It supports both ordinal (ordered) categories as well as nominal ones. Currently, there are two templates available

* **standard** - standard template with embedded charts
* **interactive** - interactive template with dynamically generated charts

The report contains:

* **an overview** - basic information about the dataset, consumption in the memory and category names
* **profiles**  - profiles of attributes - charts with frequencies of categories (all, not first TOP n as typical for universal profiling packages)
* **correlations** - correlations between attributes and values


## Installation and using the package

You can install the package using

`pip install pandas-cat`

To load your dataset into a Pandas DataFrame, you can use the `read_csv()` method for CSV files or the `read_excel()` method for Excel files. Both methods support a parameter called `keep_default_na`, which you can set to `False`. This prevents Pandas from detecting missing values, as `pandas-cat` offers a much more comprehensive detection system, including all the values Pandas detects. For faster report generation, you can select specific columns for analysis by filtering them directly in Pandas.

### Sample Code

```python
import pandas as pd
from pandas_cat import pandas_cat

# Read dataset. You can download it and set up a path to the local file.
df = pd.read_csv('https://petrmasa.com/pandas-cat/data/accidents.zip',
                 encoding='cp1250', sep='\t')

# Use only selected columns
df = df[['Driver_Age_Band', 'Driver_IMD', 'Sex', 'Journey']]

# Generate a profile report with the default template
pandas_cat.profile(df=df, dataset_name="Accidents", opts={"auto_prepare": True})

```

For longer demo report use this set of columns instead of the first one
```python
df = df[['Driver_Age_Band','Driver_IMD','Sex','Journey','Hit_Objects_in','Hit_Objects_off','Casualties','Severity','Area','Vehicle_Age','Road_Type','Speed_limit','Light','Vehicle_Location','Vehicle_Type']]
```

To generate interactive report, set the template to `interactive`
```python
pandas_cat.profile(df=df, dataset_name="Accidents", template="interactive", opts={"auto_prepare": True})
```


For advanced customization, use additional options
```python
pandas_cat.profile(
    df=df,
    dataset_name="Accidents",
    template="interactive",
    opts={
        "auto_prepare": True,
        "cat_limit": 60,  # Maximum categories for profiling
        "na_values": ["MyNA", "MyNull"],  # Custom missing values
        "na_ignore": ["NA"],  # Exclude specific values from missing detection
        "keep_default_na": True  # Use default missing values build-in list
    }
)
```
To adjust the dataset only without generating a report
```python
df = pandas_cat.prepare(df)
```

## Data and sample reports

Sample reports are here 

* [basic](https://petrmasa.com/pandas-cat/sample/report1.html) 
* [longer](https://petrmasa.com/pandas-cat/sample/report2.html)
* [interactive](https://petrmasa.com/pandas-cat/sample/interactive.html)

The dataset is downloaded from the web (each time you run the code). If you want, you can download sample dataset [here](https://petrmasa.com/pandas-cat/data/accidents.zip) and store it locally.

## Credits

Petr Masa - Base package, basic data preparation

Jan Nejedly - Interactive report, handling missing values
