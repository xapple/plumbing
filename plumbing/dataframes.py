#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio
"""

# Built-in modules #
from io import StringIO

# Third party modules #
import pandas

################################################################################
def r_matrix_to_dataframe(matrix):
    import numpy
    cols = list(matrix.colnames)
    rows = list(matrix.rownames)
    return pandas.DataFrame(numpy.array(matrix), index=rows, columns=cols)

################################################################################
def pandas_df_to_r_df(pandas_df):
    from pandas.rpy.common import convert_to_r_dataframe
    return convert_to_r_dataframe(pandas_df)

################################################################################
def pandas_df_to_named_r_df(pandas_df, r_name):
    eval("%s = convert_to_r_dataframe(pandas_df)" % r_name)
    eval("return %s" % r_name)

################################################################################
def string_to_df(string, **kwargs):
    """
    Parse a string as a dataframe. Example:

        >>> from plumbing.dataframes import string_to_df
        >>>
        >>> a = '''  i  | x | y | z
        >>>         AR  | v | 5 | 1
        >>>         For | w | 3 | 3
        >>>         For | w | 4 | 4 '''
        >>>
        >>> df = string_to_df(a)
        >>> print(df)

             i  x  y  z
        0   AR  v  5  1
        1  For  w  3  3
        2  For  w  4  4
    """
    handle = StringIO(string.replace(' ',''))
    df     = pandas.read_csv(handle, sep="|", header=0, **kwargs)
    return df

################################################################################
def count_unique_index(df, by):
    """
    This function enables you to quickly see how many unique combinations of
    column values exist in a data frame. Here are two examples:

        >>> df = ''' i   | A  | B | C
        >>>          For | 3  | 1 | x
        >>>          For | 3  | 2 | x
        >>>          For | 3  | 3 | y '''
        >>> from plumbing.dataframes import string_to_df
        >>> df = string_to_df(df)
        >>> count_unique_index(df, by=['A', 'C'])

           A  C  count
        0  3  x      2
        1  3  y      1

        >>> import seaborn
        >>> tips = seaborn.load_dataset("tips")
        >>> print(count_unique_index(tips, ['sex', 'smoker']))

              sex smoker  count
        0    Male    Yes     60
        1    Male     No     97
        2  Female    Yes     33
        3  Female     No     54

        >>> tips = seaborn.load_dataset("tips")
        >>> print(count_unique_index(tips, ['sex', 'smoker', 'day']))

              sex smoker    time  count
        0    Male    Yes   Lunch     13
        1    Male    Yes  Dinner     47
        2    Male     No   Lunch     20
        3    Male     No  Dinner     77
        4  Female    Yes   Lunch     10
        5  Female    Yes  Dinner     23
        6  Female     No   Lunch     25
        7  Female     No  Dinner     29
    """
    return df.groupby(by).size().reset_index().rename(columns={0: 'count'})

################################################################################
def multiply_propagate_nan(df, series):
    """
    This function enables you to multiply a dataframe by a series with 'smart'
    propagation of NaN values.

    We implement a simple rule where:

        x * NaN = NaN | ∀x≠0
        0 * NaN = 0

    In essence, multipling a NaN with a zero will yield a zero and multipling
    a NaN with anything else will yield a NaN.
    This is usefull in some scenarios where NaN simply indicates a missing
    value in a dataset, which is known to be a dataset of real numbers.
    For instance, when a scientist knows that all values considered in a given
    experiment are scalars but a few of the values were not recorded or were
    lost.
    This is done because, as it stands, NaN can represent anything even the
    result of an operation yielding infinity. But there is no float named "IaN"
    that would stand for "Is a Number", where we know that the number is
    in R or N, but are missing its particular value.

    #TODO restore zeros from the series too not only the dataframe.

    An example follows:

        >>> one = '''    | W1   | W2   | W3
        >>>           A  | 0.0  | 0.7  | NaN
        >>>           B  | 0.1  | 1.0  | 1.0
        >>>           C  | 0.2  | 0.8  | 0.49
        >>>           D  | 0.0  | 0.0  | 1.0  '''
        >>>
        >>> two = '''    | Y
        >>>           W3 | 8.0
        >>>           W1 | NaN
        >>>           W2 | 9.0  '''
        >>>
        >>> from plumbing.dataframes import string_to_df
        >>> one = string_to_df(one, index_col=0)
        >>> two = string_to_df(two, index_col=0)
        >>>
        >>> from plumbing.dataframes import multiply_propagate_nan
        >>> print(multiply_propagate_nan(one, two['Y']))

                W1   W2    W3
            A  0.0  6.3   NaN
            B  NaN  9.0  8.00
            C  NaN  7.2  3.92
            D  0.0  0.0  8.00
    """
    # Multiply #
    result = df * series
    # Restore the zeros where they should be #
    result[df == 0.0] = 0.0
    # Return #
    return result
