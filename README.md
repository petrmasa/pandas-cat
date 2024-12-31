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

For example, in dataset _Accidents_

attribute Hit Objects in can be used as:

- _unordered_: 0.0 10.0 7.0 11.0 4.0 2.0 8.0 1.0 9.0 6.0 5.0 12.0 nan
- _ordered_: 0.0 1.0 10.0 11.0 12.0 2.0 4.0 5.0 6.0 7.0 8.0 9.0 nan
- _as analyst wishes (package does)_: 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0 nan

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

# For longer demo report use this set of columns instead of the first one
df = df[['Driver_Age_Band','Driver_IMD','Sex','Journey','Hit_Objects_in','Hit_Objects_off','Casualties','Severity','Area','Vehicle_Age','Road_Type','Speed_limit','Light','Vehicle_Location','Vehicle_Type']]

# Generate a profile report with the default template
pandas_cat.profile(df=df, dataset_name="Accidents", opts={"auto_prepare": True})

# For an interactive report, set the template to "interactive"
pandas_cat.profile(df=df, dataset_name="Accidents", template="interactive", opts={"auto_prepare": True})

# For advanced customization, use additional options
pandas_cat.profile(
    df=df,
    dataset_name="Accidents",
    template="interactive",
    opts={
        "auto_prepare": True,
        "cat_limit": 15,  # Maximum categories for profiling
        "na_values": ["MyNA", "MyNull"],  # Custom missing values
        "na_ignore": ["NA"],  # Exclude specific values from missing detection
        "keep_default_na": True  # Use default missing values
    }
)

# To adjust the dataset only without generating a report
df = pandas_cat.prepare(df)
```

## Data and sample reports

Sample reports are here - [basic](https://petrmasa.com/pandas-cat/sample/report1.html) and [longer](https://petrmasa.com/pandas-cat/sample/report2.html).
Sample report of the new interactive template (credit goes to Jan Nejedly) is available [here](https://petrmasa.com/pandas-cat/sample/interactive.html).

The dataset is downloaded from the web (each time you run the code). If you want, you can download sample dataset [here](https://petrmasa.com/pandas-cat/data/accidents.zip) and store it locally.

## Credits

Petr Masa - Base package, basic data preparation

Jan Nejedly - Interactive report, handling missing values
