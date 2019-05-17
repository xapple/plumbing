# Futures #
from __future__ import division

# Built-in modules #
import os, time, inspect, getpass
from collections import OrderedDict

# Internal modules #
from plumbing.common import split_thousands, camel_to_snake
from plumbing.cache  import property_cached
from autopaths       import Path
from autopaths.file_path import FilePath

# Third party modules #
import numpy
import matplotlib, brewer2mpl
matplotlib.use('Agg', warn=False)
from matplotlib import pyplot

# Constants #
cool_colors = brewer2mpl.get_map('Set1', 'qualitative', 8).mpl_colors
cool_colors.reverse()
cool_colors += brewer2mpl.get_map('Set2',    'qualitative', 8).mpl_colors
cool_colors += brewer2mpl.get_map('Set3',    'qualitative', 8).mpl_colors
cool_colors += brewer2mpl.get_map('Pastel1', 'qualitative', 8).mpl_colors
cool_colors += brewer2mpl.get_map('Pastel2', 'qualitative', 8).mpl_colors
cool_colors += brewer2mpl.get_map('Greys',   'sequential',  8).mpl_colors

################################################################################
class Graph(object):
    """ A nice class to make graphs with matplotlib. Example usage:
            from plumbing.graphs import Graph
            class RegressionGraph(Graph):
                def plot(self, **kwargs):
                    fig = pyplot.figure()
                    seaborn.regplot(self.x_data, self.y_data, fit_reg=True);
                    self.save_plot(fig, **kwargs)
            for x_name in x_names:
                graph            = PearsonGraph(short_name = x_name)
                graph.title      = "Regression between y and '%s'" % (x_name)
                graph.x_data     = x_data[x_name]
                graph.y_data     = y_data
                graph.plot()
    """

    default_params = OrderedDict((
        ('width'  , None),
        ('height' , None),
        ('bottom' , None),
        ('top'    , None),
        ('left'   , None),
        ('right'  , None),
        ('x_grid' , None), # Vertical lines
        ('y_grid' , None), # Horizontal lines
        ('x_scale', None),
        ('y_scale', None),
        ('x_label', None),
        ('y_label', None),
        ('title'  , None),
        ('y_lim_min', None), # Minium (ymax - ymin) after autoscale
        ('x_lim_min', None), # Minium (xmax - xmin) after autoscale
        ('sep'    , ()),
        ('formats', ('pdf',)),
        ('close'  , False),
    ))

    def __bool__(self): return bool(self.path)
    __nonzero__ = __bool__

    def __init__(self, parent=None, base_dir=None, short_name=None):
        # Save parent #
        self.parent = parent
        # If we got a file #
        if isinstance(base_dir, FilePath):
            self.base_dir = base_dir.directory
            short_name    = base_dir.short_prefix
        # If no parent and no directory #
        if base_dir is None and parent is None:
            file_name     = os.path.abspath((inspect.stack()[1])[1])
            self.base_dir = os.path.dirname(os.path.abspath(file_name)) + '/'
            self.base_dir = Path(self.base_dir)
        # If no directory but a parent is present #
        if base_dir is None:
            if hasattr(self.parent, 'p'):
                self.base_dir = self.parent.p.graphs_dir
            if hasattr(self.parent, 'paths'):
                self.base_dir = self.parent.paths.graphs_dir
        else:
            self.base_dir = Path(self.base_dir)
        self.base_dir.create_if_not_exists()
        # Short name #
        if short_name: self.short_name = short_name
        # Use the base class name #
        if not hasattr(self, 'short_name'):
            self.short_name = camel_to_snake(self.__class__.__name__)

    @property_cached
    def path(self):
        return Path(self.base_dir + self.short_name + '.pdf')

    def __call__(self, *args, **kwargs):
        """Plot the graph if it doesn't exist. Then return the path to it.
        Force the reruning with rerun=True"""
        if not self or kwargs.get('rerun'): self.plot(*args, **kwargs)
        return self.path

    def save_plot(self, fig=None, axes=None, **kwargs):
        # Missing figure #
        if fig is None:   fig = pyplot.gcf()
        # Missing axes #
        if axes is None: axes = pyplot.gca()
        # Parameters #
        self.params = {}
        for key in self.default_params:
            if key in kwargs:                          self.params[key] = kwargs[key]
            elif hasattr(self, key):                   self.params[key] = getattr(self, key)
            elif self.default_params[key] is not None: self.params[key] = self.default_params[key]
        # Backwards compatibility #
        if kwargs.get('x_log', False): self.params['x_scale'] = 'symlog'
        if kwargs.get('y_log', False): self.params['y_scale'] = 'symlog'
        # Log #
        if 'x_scale' in self.params: axes.set_xscale(self.params['x_scale'])
        if 'y_scale' in self.params: axes.set_yscale(self.params['y_scale'])
        # Axis limits #
        if 'x_min' in self.params: axes.set_xlim(self.params['x_min'], axes.get_xlim()[1])
        if 'x_max' in self.params: axes.set_xlim(axes.get_xlim()[0], self.params['x_max'])
        if 'y_min' in self.params: axes.set_ylim(self.params['y_min'], axes.get_ylim()[1])
        if 'y_max' in self.params: axes.set_ylim(axes.get_ylim()[0], self.params['y_max'])
        # Minimum delta on axis limits #
        if 'y_lim_min' in self.params:
            top, bottom = axes.get_ylim()
            minimum     = self.params['y_lim_min']
            delta       = top - bottom
            if delta < minimum:
                center = bottom + delta/2
                axes.set_ylim(center - minimum/2, center + minimum/2)
        # Title #
        title = self.params.get('title', False)
        if title: axes.set_title(title)
        # Axes labels  #
        if self.params.get('x_label'): axes.set_xlabel(self.params['x_label'])
        if self.params.get('y_label'): axes.set_ylabel(self.params['y_label'])
        # Set height and width #
        if self.params.get('width'):  fig.set_figwidth(self.params['width'])
        if self.params.get('height'): fig.set_figheight(self.params['height'])
        # Adjust #
        if self.params.get('bottom'):
            fig.subplots_adjust(hspace=0.0, bottom = self.params['bottom'], top   = self.params['top'],
                                            left   = self.params['left'],   right = self.params['right'])
        # Grid #
        if 'x_grid' in self.params: axes.xaxis.grid(self.params['x_grid'])
        if 'y_grid' in self.params: axes.yaxis.grid(self.params['y_grid'])
        # Data and source extra text #
        if hasattr(self, 'dev_mode') and self.dev_mode is True:
            fig.text(0.99, 0.98, time.asctime(), horizontalalignment='right')
            job_name = os.environ.get('SLURM_JOB_NAME', 'Unnamed')
            user_msg = 'user: %s, job: %s' % (getpass.getuser(), job_name)
            fig.text(0.01, 0.98, user_msg, horizontalalignment='left')
        # Nice digit grouping #
        if 'x' in self.params['sep']:
            separate = lambda x,pos: split_thousands(x)
            axes.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(separate))
        if 'y' in self.params['sep']:
            separate = lambda y,pos: split_thousands(y)
            axes.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(separate))
        # Add custom labels #
        if 'x_labels' in self.params: axes.set_xticklabels(self.params['x_labels'])
        if 'x_labels_rot' in self.params: pyplot.setp(axes.xaxis.get_majorticklabels(), rotation=self.params['x_labels_rot'])
        # Possibility to overwrite path #
        if 'path' in self.params:   path = FilePath(self.params['path'])
        elif hasattr(self, 'path'): path = FilePath(self.path)
        else:                       path = FilePath(self.short_name + '.pdf')
        # Save it as different formats #
        for ext in self.params['formats']: fig.savefig(path.replace_extension(ext))
        # Close it #
        if self.params['close']: pyplot.close(fig)

    def plot_and_save(self, **kwargs):
        """Used when the plot method defined does not create a figure nor calls save_plot
        Then the plot method has to use self.fig"""
        self.fig = pyplot.figure()
        self.plot()
        self.axes = pyplot.gca()
        self.save_plot(self.fig, self.axes, **kwargs)
        pyplot.close(self.fig)

    def plot(self, bins=250, **kwargs):
        """An example plot function. You have to subclass this method."""
        # Data #
        counts = [sum(map(len, b.contigs)) for b in self.parent.bins]
        # Linear bins in logarithmic space #
        if 'log' in kwargs.get('x_scale', ''):
            start, stop = numpy.log10(1), numpy.log10(max(counts))
            bins = list(numpy.logspace(start=start, stop=stop, num=bins))
            bins.insert(0, 0)
        # Plot #
        fig = pyplot.figure()
        pyplot.hist(counts, bins=bins, color='gray')
        axes = pyplot.gca()
        # Information #
        title = 'Distribution of the total nucleotide count in the bins'
        axes.set_title(title)
        axes.set_xlabel('Number of nucleotides in a bin')
        axes.set_ylabel('Number of bins with that many nucleotides in them')
        # Save it #
        self.save_plot(fig, axes, **kwargs)
        pyplot.close(fig)
        # For convenience #
        return self

    def save_anim(self, fig, animate, init, bitrate=10000, fps=30):
        """Not functional -- TODO"""
        from matplotlib import animation
        anim = animation.FuncAnimation(fig, animate, init_func=init, frames=360, interval=20)
        FFMpegWriter = animation.writers['ffmpeg']
        writer = FFMpegWriter(bitrate= bitrate, fps=fps)
        # Save #
        self.avi_path = self.base_dir + self.short_name + '.avi'
        anim.save(self.avi_path, writer=writer, codec='x264')
