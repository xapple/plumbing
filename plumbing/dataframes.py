# Built-in modules #

# Internal modules #

# Third party modules #
import pandas, numpy
#from pandas.rpy.common import convert_to_r_dataframe
from six import StringIO

################################################################################
def r_matrix_to_dataframe(matrix):
    cols = list(matrix.colnames)
    rows = list(matrix.rownames)
    return pandas.DataFrame(numpy.array(matrix), index=rows, columns=cols)

################################################################################
def pandas_df_to_r_df(pandas_df):
    return convert_to_r_dataframe(pandas_df)

################################################################################
def pandas_df_to_named_r_df(pandas_df, r_name):
    eval("%s = convert_to_r_dataframe(pandas_df)" % r_name)
    eval("return %s" % r_name)

################################################################################
def string_to_df(string):
    """
    Parse a string as a dataframe. Example:

        >>> a = '''  i  | x | y | z
        >>>         AR  | v | 5 | 1
        >>>         For | w | 3 | 3
        >>>         For | w | 4 | 4 '''
        >>> df = string_to_df(a)
        >>> print(df)
             i  x  y  z
        0   AR  v  5  1
        1  For  w  3  3
        2  For  w  4  4
    """
    return pandas.read_csv(StringIO(string.replace(' ','')), sep="|", header=0)

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


