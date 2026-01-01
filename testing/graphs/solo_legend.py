#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to test the functionality of the graph module and legend generation.

Written by Lucas Sinclair. MIT Licensed.

Call it like this:

    $ ipython3 -i ~/repos/plumbing/testing/graphs/solo_legend.py
"""

# Modules #
import inspect
from autopaths import Path
from plumbing.graphs.solo_legend import SoloLegend

# Constants #
this_file = Path((inspect.stack()[0])[1])
this_dir  = this_file.directory

###############################################################################
class TestLegend(SoloLegend):

    short_name = "test_legend"
    n_col      = 3
    capitalize = False

    @property
    def label_to_color(self):
        return {'Pink': (0.9686274509803922, .5058823529411764, 0.7490196078431373),
                'Black': 'black',
                'White':  '#FFFFFF',
                'Yellow': (1.0, 1.0, 0.2),
                'Other_A': (0.6509803921568628, 0.33725490196078434, 0.1568627450980392),
                'Orange': (1.0, 0.4980392156862745, 0.0),
                'Other_C': (0.4, 0.7607843137254902, 0.6470588235294118),
                'Other_D': (0.5529411764705883, 0.6274509803921569, 0.796078431372549),
                'Other_E': (0.6509803921568628, 0.8470588235294118, 0.32941176470588235),
                'Other_F': (1.0, 0.8509803921568627, 0.1843137254901961),
                'Other_G': (0.8980392156862745, 0.7686274509803922, 0.5803921568627451),
                }

###############################################################################
legend = TestLegend(base_dir=this_dir)
legend(rerun=True)