#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Built-in modules #

# Internal modules #

# First party modules #
from plumbing.graphs import Graph
from plumbing.cache import property_cached

###############################################################################
class Multiplot(Graph):
    """
    Similar to a FacetPlot, expect we don't use `seaborn` and do everything
    ourselves with `matplotlib`.
    """

    # Size of grid #
    n_rows = 1
    n_cols = 1

    # Defaults #
    share_y = True
    share_x = True

    # Defaults #
    height = None
    width  = None

    @property_cached
    def fig_and_axes(self):
        # Synonyms #
        if self.share_x is True: self.share_x = 'all'
        if self.share_y is True: self.share_y = 'all'
        # Figure size #
        width  = self.n_cols * 5 if self.width is None else self.width
        height = self.n_rows * 5 if self.height is None else self.height
        # Create #
        from matplotlib import pyplot
        fig, axes = pyplot.subplots(nrows   = self.n_rows,
                                    ncols   = self.n_cols,
                                    sharex  = self.share_x,
                                    sharey  = self.share_y,
                                    figsize = (width, height))
        # Return #
        return fig, axes

    @property
    def fig(self): return self.fig_and_axes[0]

    @property
    def axes(self): return self.fig_and_axes[1]

    #--------------------------- Convenience ---------------------------------#
    def iterate_all_axes(self, fn):
        import numpy
        for axes in numpy.nditer(self.axes, flags=['refs_ok']): fn(axes[()])

    def x_grid_on(self):
        """Add horizontal lines on the x axis."""
        fn = lambda axes: axes.xaxis.grid(True, linestyle=':')
        self.iterate_all_axes(fn)

    def y_grid_on(self):
        """Add horizontal lines on the y axis."""
        fn = lambda axes: axes.yaxis.grid(True, linestyle=':')
        self.iterate_all_axes(fn)

    def set_x_lim(self, a, b):
        fn = lambda axes: axes.set_xlim(a, b)
        self.iterate_all_axes(fn)

    def set_y_lim(self, a, b):
        fn = lambda axes: axes.set_ylim(a, b)
        self.iterate_all_axes(fn)

    def set_x_ticks(self, ticks):
        fn = lambda axes: axes.set_xticks(ticks)
        self.iterate_all_axes(fn)

    def set_y_ticks(self, ticks):
        fn = lambda axes: axes.set_yticks(ticks)
        self.iterate_all_axes(fn)

    def set_x_tick_labels(self, labels):
        fn = lambda axes: axes.set_xticklabels(labels)
        self.iterate_all_axes(fn)

    def set_y_tick_labels(self, labels):
        fn = lambda axes: axes.set_yticklabels(labels)
        self.iterate_all_axes(fn)

    def hide_titles(self):
        """Remove the subplot titles."""
        fn = lambda axes: axes.title.set_visible(False)
        self.iterate_all_axes(fn)

    def y_max_two_decimals(self):
        """Force maximum two decimals for y axis."""
        import matplotlib
        str_formatter = matplotlib.ticker.FormatStrFormatter('%.2f')
        fn = lambda axes: axes.yaxis.set_major_formatter(str_formatter)
        self.iterate_all_axes(fn)

    def set_x_labels(self, label):
        fn = lambda axes: axes.set_xlabel(label)
        self.iterate_all_axes(fn)

    def set_y_labels(self, label):
        fn = lambda axes: axes.set_ylabel(label)
        self.iterate_all_axes(fn)

    def remove_frame(self):
        fn = lambda axes: axes.spines["top"].set_visible(False)
        self.iterate_all_axes(fn)
        fn = lambda axes: axes.spines["right"].set_visible(False)
        self.iterate_all_axes(fn)

    def hide_full_axes(self, axes):
        axes.xaxis.grid(False)
        axes.yaxis.grid(False)
        axes.spines["top"].set_visible(False)
        axes.spines["right"].set_visible(False)
        axes.spines["left"].set_visible(False)
        axes.spines["bottom"].set_visible(False)
        axes.set_xlabel(None)
        # X axis #
        for xlabel in axes.get_xticklabels(): xlabel.set_visible(False)
        for tick in axes.get_xticklines(): tick.set_visible(False)
        # Y axis #
        for ylabel in axes.get_yticklabels(): ylabel.set_visible(False)
        for tick in axes.get_yticklines(): tick.set_visible(False)

    def y_center_origin(self):
        """
        Place the zero-intercept exactly the middle of the graph.
        This is not the same as doing:
        `axes.spines['left'].set_position('center')`
        """
        def fn(axes):
            bottom, top = axes.get_ylim()
            highest     = max(abs(top), abs(bottom))
            axes.set_ylim(-highest, highest)
        self.iterate_all_axes(fn)