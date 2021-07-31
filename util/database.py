
import numpy as np
import pandas as pd
import glob
import shutil
import os
import sqlite3
from copy import deepcopy
from datetime import datetime,timedelta,date

class Database:
    
    def __init__(self,db_name):
        self.db_name =db_name
        self.status=False
        try:
            self.connection = sqlite3.connect(self.db_name)
            print(f"Connected to << {self.db_name}>>")
            self.status = True
        except(Exception,sqlite3.Error) as error:
            print("Error while trying connect",error)
    
    def close_connection(self):
        if self.status:
            self.connection.close()
            print(f"Connection for << {self.db_name} >> is closed")
        else:
            print(f"Connection for << {self.db_name} >> is already closed")
            
    def read_database_version(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("select sqlite_version();")
            db_version = cursor.fetchone()
            print(f"<< {self.db_name} >> 's version is {db_version}")
            
        except(Exception,sqlite3.Error) as error:
            print(f"Error while getting data",error)
    
    def get_table_names(self):
        try:
            cursor = self.connection.cursor()
            query = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            records =cursor.fetchall()
            cols = [column[0] for column in query.description]
            cursor.close()
        except sqlite3.Error as error:
            print(f"Failed to read data from sqlite table",error)
        results = pd.DataFrame.from_records(data=records,columns=cols).rename(columns={'name':'Table Name'})
        return results
    
    def read_table(self,table_name,limit=None):
        try:
            if limit==None:
                sqlite_query = f"""SELECT * from {table_name}"""
            else:
                sqlite_query = f"""SELECT * from {table_name} LIMIT {limit}"""
            
            df = pd.read_sql(sqlite_query,self.connection)
        except sqlite3.Error as error:
            print("Failed to read data from sqlite table")
        
        return df
    
    def get_column_names_from_table(self,table_name):
        columns_names=list()
        try:
            cursor =self.connection.cursor()
            table_column_names = 'PRAGMA table_info('+table_name+');'
            cursor.execute(table_column_names)
            records = cursor.fetchall()
            for name in records:
                columns_names.append(name[1])
            
            cursor.close()
        except sqlite3l.Error as error:
            print("Failed to get data",error)
            
        return columns_names
    
    def update_table_with_df(self,table_name,df,drop_duplicate=False):
        try:
            if table_name in list(self.get_table_names()['Table Name']):
                print(f"Found table <<{table_name}>> in Database <<{self.db_name}>>")
                
            else:
                print(f"Attention , creating new table <<{table_name}>> in Database <<{self.db_name}>> ")
            
            df.to_sql(name=table_name,con=self.connection,if_exists="append", index=False)
            
            if drop_duplicate:
                new_df = self.read_table(table_name).drop_duplicates()
                new_df.to_sql(name=table_name,con=self.connection,if_exists="replace", index=False)
            
            print("Sql insert process finished.")
        
        except sqlite3.Error as error:
            print("Failed to update",error)
            print("If it's a creation, be careful with columns format and value types")
            
            
    def delete_table(self,table_name):
        try:
            cursor =self.connection.cursor()
            sqlite_query = f"DROP TABLE {table_name};"
            cursor.execute(sqlite_query)
            self.connection.commit()
            cursor.close()
            print(f"Drop table << {table_name} >> success.")
            
        except sqlite3l.Error as error:
            print(f"Failed to delete table <<{table_name}>>",error)
            
    def back_up_to(self,dest):
        current_path = os.getcwd()
        os.chdir(dest)
        new_name ="Backup"+datetime.now().strftime("%d-%m-%Y")+self.db_name
        bck = sqlite3.connect(new_name)
        self.connection.backup(bck)
        bck.close()
        print("Back Up finished.")
        os.chdir(current_path)