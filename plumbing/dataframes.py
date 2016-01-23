# Built-in modules #

# Internal modules #

# Third party modules #
import pandas, numpy
#from pandas.rpy.common import convert_to_r_dataframe

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