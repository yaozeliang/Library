"""Database utility functions for the Library Management System."""

import os
import shutil
import sqlite3
from copy import deepcopy
from datetime import date, datetime, timedelta
from typing import Any, List, Optional

import numpy as np
import pandas as pd


class Database:
    """Database utility class for SQLite operations."""

    def __init__(self, db_name: str) -> None:
        """Initialize database connection.

        Args:
            db_name: Name of the database file.
        """
        self.db_name = db_name
        self.status = False
        try:
            self.connection = sqlite3.connect(self.db_name)
            print(f"Connected to << {self.db_name}>>")
            self.status = True
        except sqlite3.Error as error:
            print("Error while trying connect", error)

    def close_connection(self) -> None:
        """Close the database connection."""
        if self.status:
            self.connection.close()
            print(f"Connection for << {self.db_name} >> is closed")
        else:
            print(f"Connection for << {self.db_name} >> is already closed")

    def read_database_version(self) -> None:
        """Read and display the SQLite version."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("select sqlite_version();")
            db_version = cursor.fetchone()
            print(f"<< {self.db_name} >> 's version is {db_version}")

        except sqlite3.Error as error:
            print(f"Error while getting data", error)

    def get_table_names(self) -> pd.DataFrame:
        """Get all table names from the database.

        Returns:
            DataFrame containing table names.
        """
        try:
            cursor = self.connection.cursor()
            query = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            records = cursor.fetchall()
            cols = [column[0] for column in query.description]
            cursor.close()
        except sqlite3.Error as error:
            print(f"Failed to read data from sqlite table", error)
            return pd.DataFrame()

        results = pd.DataFrame.from_records(data=records, columns=cols).rename(
            columns={"name": "Table Name"},
        )
        return results

    def read_table(self, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
        """Read data from a specific table.

        Args:
            table_name: Name of the table to read.
            limit: Optional limit on number of rows to read.

        Returns:
            DataFrame containing table data.
        """
        try:
            if limit is None:
                sqlite_query = f"""SELECT * from {table_name}"""
            else:
                sqlite_query = f"""SELECT * from {table_name} LIMIT {limit}"""

            df = pd.read_sql(sqlite_query, self.connection)
        except sqlite3.Error as error:
            print("Failed to read data from sqlite table", error)
            return pd.DataFrame()

        return df

    def get_column_names_from_table(self, table_name: str) -> List[str]:
        """Get column names from a specific table.

        Args:
            table_name: Name of the table.

        Returns:
            List of column names.
        """
        columns_names = []
        try:
            cursor = self.connection.cursor()
            table_column_names = "PRAGMA table_info(" + table_name + ");"
            cursor.execute(table_column_names)
            records = cursor.fetchall()
            for name in records:
                columns_names.append(name[1])

            cursor.close()
        except sqlite3.Error as error:
            print("Failed to get data", error)

        return columns_names

    def update_table_with_df(
        self, table_name: str, df: pd.DataFrame, drop_duplicate: bool = False
    ) -> None:
        """Update table with DataFrame data.

        Args:
            table_name: Name of the table to update.
            df: DataFrame containing data to insert.
            drop_duplicate: Whether to drop duplicates after insertion.
        """
        try:
            if table_name in list(self.get_table_names()["Table Name"]):
                print(f"Found table <<{table_name}>> in Database <<{self.db_name}>>")

            else:
                print(
                    f"Attention , creating new table <<{table_name}>> in Database <<{self.db_name}>> ",
                )

            df.to_sql(name=table_name, con=self.connection, if_exists="append", index=False)

            if drop_duplicate:
                new_df = self.read_table(table_name).drop_duplicates()
                new_df.to_sql(
                    name=table_name, con=self.connection, if_exists="replace", index=False
                )

            print("Sql insert process finished.")

        except sqlite3.Error as error:
            print("Failed to update", error)
            print("If it's a creation, be careful with columns format and value types")

    def delete_table(self, table_name: str) -> None:
        """Delete a table from the database.

        Args:
            table_name: Name of the table to delete.
        """
        try:
            cursor = self.connection.cursor()
            sqlite_query = f"DROP TABLE {table_name};"
            cursor.execute(sqlite_query)
            self.connection.commit()
            cursor.close()
            print(f"Drop table << {table_name} >> success.")

        except sqlite3.Error as error:
            print(f"Failed to delete table <<{table_name}>>", error)

    def back_up_to(self, dest: str) -> None:
        """Create a backup of the database.

        Args:
            dest: Destination directory for the backup.
        """
        current_path = os.getcwd()
        os.chdir(dest)
        new_name = "Backup" + datetime.now().strftime("%d-%m-%Y") + self.db_name
        bck = sqlite3.connect(new_name)
        self.connection.backup(bck)
        bck.close()
        print("Back Up finished.")
        os.chdir(current_path)