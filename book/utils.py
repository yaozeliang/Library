
import numpy as np
import pandas as pd
import glob
import shutil
import os
import sqlite3
from copy import deepcopy
from datetime import datetime,timedelta,date



def get_n_days_ago(n=0,time_format="%d-%m-%Y"):
    time_stamp = datetime.now()-timedelta(days=n)
    return time_stamp.strftime(time_format)


def create_clean_dir(name):
    if os.path.isdir(name):
        shutil.rmtree(name)
        os.makedirs(name)
    else:
        os.makedirs(name)
    os.chdir(name)
    
def change_col_format(df,target_type):
    for c in df.columns:
        df[c] = df[c].astype(target_type)
    return df