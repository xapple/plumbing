#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio
"""

# Built-in modules #
import logging

# Internal modules #

# Third party modules #

###############################################################################
def create_file_logger(name, path, file_level='debug', console_level='error'):
    # Create a custom logger #
    logger = logging.getLogger(name)
    # Console logger and file logger #
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(str(path), mode="w")
    # Choose the level of information for each #
    c_handler.setLevel(getattr(logging, console_level.upper()))
    f_handler.setLevel(getattr(logging, file_level.upper()))
    # Set the level of the logger itself to the lowest common denominator #
    #TODO: what if the console has a higher level than the file?
    logger.setLevel(getattr(logging, file_level.upper()))
    # Choose the format of each #
    c_format = '%(name)s - %(levelname)s - %(message)s'
    f_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    c_format = logging.Formatter(c_format)
    f_format = logging.Formatter(f_format)
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)
    # No need to display Exceptions on the console #
    class NoExceptionFilter(logging.Filter):
        def filter(self, record):
            return not record.getMessage() == 'Exception'
    c_handler.addFilter(NoExceptionFilter())
    # Add handlers to the logger #
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    # Return #
    return logger
