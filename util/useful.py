
import numpy as np
import pandas as pd
import glob
import shutil
import os
import sqlite3
from copy import deepcopy
from datetime import datetime,timedelta,date
from django.core.exceptions import PermissionDenied


"""
About DataFrame

"""

def get_mem_usage(df):
    print(f"{df.memory_usage(deep=True).sum()/1024 **2:3.2f}Mb")

def get_general_info(df):
    name = [x for x in globals() if globals()[x] is df][0]
    print(f"Dataframe << {name}>>has {df.shape[0]} rows, {df.shape[1]} columns")
    print("=======================================")
    print("Column Types:\n")
    print(df.dtypes)
    print("=======================================")
    print("Missing values per column: ")
    percent_missing = df.isnull().sum()*100 / len(df)
    missing_value_df = pd.DataFrame({'column_name':df.columns,'percent_missing':percent_missing})
    missing_value_df['percent_missing'] = ["{:.2f}%".format(x) for x in missing_value_df['percent_missing'] ]
    print(missing_value_df)
    print("=======================================")
    print(f"Memory Use: {df.memory_usage(deep=True).sum()/1024 **2:3.2f}Mb")    
    print("=======================================")
    print("Missing Values in columns: ")
    print(df.isnull().sum())

def get_optimize_df(df):
    df.astype({col:'category' for col in df.columns if df[col].nunique() / df[col].shape[0]<0.5})
    return df

def save_as_pickle(df,name,path=None):
    try:
        if path==None:
            df.to_pickle(f"{name}.pkl")
            print(f"Dataframe saved as pickle in => {os.getcwd()}")
        else:
            current_path = os.getcwd()
            df.to_pickle(f"{path}/{name}.pkl")
            print(f"Dataframe saved as pickle in => {path}/{name}.pkl")
            os.chdir(current_path)
    except:
        print("Save failed. Make sure it's a dataframe or the path is correct")


def read_pickle_as_df(path=None):
    result={}
    current_path = os.getcwd()
    target_path = os.getcwd()
    if path!=None:
        target_path = path

    os.chdir(target_path)
    lst = glob.glob(f"*.pkl")
        
    for p in lst:
        name = p.split(".")[0]
        result[name]=pd.read_pickle(p)
    
    os.chdir(current_path)
    return result


def read_large_csv(name,chunkSize=1000000,encoding='utf-8'):
    reader = pd.read_csv(name,iterator=True,encoding=encoding)
    chunks=[]
    loop=True
    while loop:
        try:
            chunk = reader.get_chunk(chunkSize)
            chunks.append(chunk)
        except StopIteration:
            loop=False
    df = pd.concat(chunks,ignore_index=True)
    return df

    
def change_col_format(df,target_type):
    for c in df.columns:
        df[c] = df[c].astype(target_type)
    return df



"""
Others
"""

def get_n_days_ago(n=0,time_format="%d-%m-%Y"):
    time_stamp = datetime.now()-timedelta(days=n)
    return time_stamp.strftime(time_format)


def get_files(extension):
    return glob.glob(f"*.{extension}")

def create_clean_dir(name):
    if os.path.isdir(name):
        shutil.rmtree(name)
        os.makedirs(name)
    else:
        os.makedirs(name)
    os.chdir(name)


