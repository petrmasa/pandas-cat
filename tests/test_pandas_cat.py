import os
import sys
import pandas as pd
import pytest
import tkinter
from pandas_cat import pandas_cat


def make_df():
    """Small in-memory DataFrame with numeric-string age bands and a nominal column."""
    return pd.DataFrame({
        'Age': ['0-10', '21-30', '11-20', '0-10', '21-30', '11-20', '21-30'],
        'Sex': ['Male', 'Female', 'Male', 'Male', 'Female', 'Male', 'Male'],
        'Vehicle_Age': ['1', '2', '3', '10', '11', '19','>=20'],
    })


def make_df_with_missing():
    """DataFrame containing known NA sentinel values."""
    return pd.DataFrame({
        'Age': ['0-10', 'Unknown', '11-20', 'NA', '21-30'],
        'Sex': ['Male', 'Female', 'None', 'Male', 'Female'],
    })


# ---------------------------------------------------------------------------
# prepare()
# ---------------------------------------------------------------------------

def test_prepare_creates_ordered_categorical():
    df = make_df()
    result = pandas_cat.prepare(df)
    assert result['Age'].dtype.name == 'category', "Age should be categorical after prepare"
    assert result['Age'].cat.ordered, "Age should be ordered after prepare"


def test_prepare_age_category_order():
    df = make_df()
    result = pandas_cat.prepare(df)
    cats = list(result['Vehicle_Age'].cat.categories)
    assert cats.index('1') < cats.index('2') < cats.index('3') < cats.index('10') < cats.index('19') < cats.index('>=20'), (
        "Categories should be ordered numerically, not alphabetically"
    )


# ---------------------------------------------------------------------------
# handle_missing_values()
# ---------------------------------------------------------------------------

def test_handle_missing_values_replaces_sentinels():
    df = make_df_with_missing()
    result, detected, counts = pandas_cat.handle_missing_values(df)
    assert result['Age'].isna().sum() == 2, "Expected 2 NAs in Age ('Unknown', 'NA')"
    assert result['Sex'].isna().sum() == 1, "Expected 1 NA in Sex ('None')"


def test_handle_missing_values_custom_na_values():
    df = pd.DataFrame({'Status': ['OK', 'TBD', 'OK', 'TBD']})
    result, detected, _ = pandas_cat.handle_missing_values(df, na_values=['TBD'])
    assert result['Status'].isna().sum() == 2


def test_handle_missing_values_na_ignore():
    df = pd.DataFrame({'Col': ['-', 'A', '-', 'B']})
    result, _, _ = pandas_cat.handle_missing_values(df, na_ignore=['-'])
    assert result['Col'].isna().sum() == 0, "'-' should be ignored when in na_ignore"


# ---------------------------------------------------------------------------
# profile() — default template
# ---------------------------------------------------------------------------

def test_profile_default_creates_html_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    df = make_df()
    pandas_cat.profile(df=df, dataset_name="Test", out_html="test_default.html",
                       opts={"auto_prepare": False})
    assert (tmp_path / "report" / "test_default.html").exists()


# ---------------------------------------------------------------------------
# profile() — interactive template
# ---------------------------------------------------------------------------

def test_profile_interactive_creates_html_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    df = make_df()
    pandas_cat.profile(df=df, dataset_name="Test", template="interactive",
                       out_html="test_interactive.html")
    assert (tmp_path / "report" / "test_interactive.html").exists()


def test_profile_interactive_autoprepare_false(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    df = make_df()
    pandas_cat.profile(df=df, dataset_name="Test", template="interactive",
                       out_html="test_interactive_no_prep.html",
                       opts={"auto_prepare": False})
    assert (tmp_path / "report" / "test_interactive_no_prep.html").exists()
