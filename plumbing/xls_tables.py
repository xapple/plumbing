#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Built-in modules #

# First party modules #
from autopaths import Path

# Third party modules #
import pandas

# Internal modules #

###############################################################################
class MultiDataFrameXLS:
    """
    Takes several dataframes and writes them to an XLS file.
    The dataframes are spread through different work sheets.
    But each work sheet can contain an arbitrary number of dataframes.
    You have to provide a dictionary where:

    * Each key is the name of a given work sheet in the final XLS as a string.
    * Each value is a list containing an arbitrary number of dictionaries.
    * Each one of these dictionaries must contain a DataFrame in the
      'dataframe' key, as well as optional extra labels as seen below.

            sheet = {
                'dataframe': df,
                'title':     "Best dataframe ever",
                'x_title':   "Foot length",
                'y_title':   "Yearly income",
                'x_label':   None,
                'y_label':   None,
                'x_extra':   None,
                'y_extra':   None,
            }
    """

    # Parameters #
    spacing = 6
    indentation = 1

    def __init__(self, sheet_to_dfs, path):
        self.sheet_to_dfs = sheet_to_dfs
        self.path         = Path(path)

    def __call__(self):
        """
        Write several dataframes, to several excel sheets.
        """
        # Create a writer #
        self.writer = pandas.ExcelWriter(str(self.path), engine='xlsxwriter')
        # Create a sheet per every key #
        for key in self.sheet_to_dfs:
            worksheet = self.writer.book.add_worksheet(key)
            self.writer.sheets[key] = worksheet
        # Write each sheet #
        for key in self.sheet_to_dfs: self.write_one_sheet(key)
        # Save #
        self.writer.save()
        # Return #
        return self.path

    def write_one_sheet(self, key):
        """
        Write several dataframes, all to the same excel sheet.
        It will append a custom title before hand for each
        dataframe.
        """
        # Get sheet #
        sheet = self.writer.sheets[key]
        # Get dataframes #
        all_dfs = self.sheet_to_dfs[key]
        # Initialize #
        row = 0
        # Loop #
        for info in all_dfs:
            # Get dataframe #
            df = info['dataframe']
            # Write custom title #
            sheet.write_string(row, 0, info.get('title', ''))
            row += 2
            # Add extras #
            df.index.name   = info.get('y_extra', '')
            df.columns.name = info.get('x_extra', '')
            # Add Y labels #
            title, label = info.get('y_title', ''), info.get('y_label', '')
            df = pandas.concat({title: df}, names=[label])
            # Add X labels #
            title, label = info.get('x_title', ''), info.get('x_label', '')
            df = pandas.concat({title: df}, names=[label], axis=1)
            # Write dataframe #
            df.to_excel(self.writer,
                        sheet_name = key,
                        startrow   = row,
                        startcol   = self.indentation)
            # Increment #
            row += len(df.index) + self.spacing

