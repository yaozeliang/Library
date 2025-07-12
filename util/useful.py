"""Useful utility functions for the Library Management System."""

import glob
import os
import shutil
import sqlite3
from copy import deepcopy
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from django.core.exceptions import PermissionDenied


def get_mem_usage(df: pd.DataFrame) -> None:
    """Print memory usage of a DataFrame.

    Args:
        df: DataFrame to analyze.
    """
    print(f"{df.memory_usage(deep=True).sum() / 1024 ** 2:3.2f}Mb")


def get_general_info(df: pd.DataFrame) -> None:
    """Print general information about a DataFrame.

    Args:
        df: DataFrame to analyze.
    """
    name = [x for x in globals() if globals()[x] is df][0]
    print(f"Dataframe << {name}>>has {df.shape[0]} rows, {df.shape[1]} columns")
    print("=======================================")
    print("Column Types:\n")
    print(df.dtypes)
    print("=======================================")
    print("Missing values per column: ")
    percent_missing = df.isnull().sum() * 100 / len(df)
    missing_value_df = pd.DataFrame(
        {"column_name": df.columns, "percent_missing": percent_missing},
    )
    missing_value_df["percent_missing"] = [
        "{:.2f}%".format(x) for x in missing_value_df["percent_missing"]
    ]
    print(missing_value_df)
    print("=======================================")
    print(f"Memory Use: {df.memory_usage(deep=True).sum() / 1024 ** 2:3.2f}Mb")
    print("=======================================")
    print("Missing Values in columns: ")
    print(df.isnull().sum())


def get_optimize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize DataFrame by converting low-cardinality columns to category type.

    Args:
        df: DataFrame to optimize.

    Returns:
        Optimized DataFrame.
    """
    df.astype(
        {
            col: "category"
            for col in df.columns
            if df[col].nunique() / df[col].shape[0] < 0.5
        },
    )
    return df


def save_as_pickle(df: pd.DataFrame, name: str, path: Optional[str] = None) -> None:
    """Save DataFrame as pickle file.

    Args:
        df: DataFrame to save.
        name: Name of the file.
        path: Optional path to save the file.
    """
    try:
        if path is None:
            df.to_pickle(f"{name}.pkl")
            print(f"Dataframe saved as pickle in => {os.getcwd()}")
        else:
            current_path = os.getcwd()
            df.to_pickle(f"{path}/{name}.pkl")
            print(f"Dataframe saved as pickle in => {path}/{name}.pkl")
            os.chdir(current_path)
    except Exception:
        print("Save failed. Make sure it's a dataframe or the path is correct")


def read_pickle_as_df(path: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """Read pickle files as DataFrames.

    Args:
        path: Optional path to read pickle files from.

    Returns:
        Dictionary mapping file names to DataFrames.
    """
    result = {}
    current_path = os.getcwd()
    target_path = os.getcwd()
    if path is not None:
        target_path = path

    os.chdir(target_path)
    lst = glob.glob("*.pkl")

    for p in lst:
        name = p.split(".")[0]
        result[name] = pd.read_pickle(p)

    os.chdir(current_path)
    return result


def read_large_csv(
    name: str, chunk_size: int = 1000000, encoding: str = "utf-8"
) -> pd.DataFrame:
    """Read large CSV file in chunks.

    Args:
        name: Name of the CSV file.
        chunk_size: Size of each chunk to read.
        encoding: File encoding.

    Returns:
        Concatenated DataFrame.
    """
    reader = pd.read_csv(name, iterator=True, encoding=encoding)
    chunks = []
    loop = True
    while loop:
        try:
            chunk = reader.get_chunk(chunk_size)
            chunks.append(chunk)
        except StopIteration:
            loop = False
    df = pd.concat(chunks, ignore_index=True)
    return df


def change_col_format(df: pd.DataFrame, target_type: str) -> pd.DataFrame:
    """Change column format of DataFrame.

    Args:
        df: DataFrame to modify.
        target_type: Target data type for all columns.

    Returns:
        Modified DataFrame.
    """
    for c in df.columns:
        df[c] = df[c].astype(target_type)
    return df


def get_n_days_ago(n: int = 0, time_format: str = "%d-%m-%Y") -> str:
    """Get date n days ago.

    Args:
        n: Number of days ago.
        time_format: Format string for the date.

    Returns:
        Formatted date string.
    """
    time_stamp = datetime.now() - timedelta(days=n)
    return time_stamp.strftime(time_format)


def get_files(extension: str) -> List[str]:
    """Get files with specific extension.

    Args:
        extension: File extension to search for.

    Returns:
        List of file paths.
    """
    return glob.glob(f"*.{extension}")


def create_clean_dir(name: str) -> None:
    """Create a clean directory (remove if exists).

    Args:
        name: Name of the directory.
    """
    if os.path.isdir(name):
        shutil.rmtree(name)
        os.makedirs(name)
    else:
        os.makedirs(name)
    os.chdir(name)


