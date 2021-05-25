# Built-in modules #
import os, time, inspect, getpass
from collections import OrderedDict

# Internal modules #
from plumbing.common import split_thousands, camel_to_snake
from plumbing.cache  import property_cached

# First party modules #
from autopaths           import Path
from autopaths.file_path import FilePath

################################################################################
class Graph(object):
    """
    A nice class to make graphs with matplotlib. Example usage:

        from plumbing.graphs import Graph

        class RegressionGraph(Graph):
            formats = ('pdf', 'svg')
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
        ('x_labels_rot', None),
        ('x_labels_size', None),
        ('y_labels_size', None),
        ('title'  , None),
        ('y_lim_min', None), # Minimum (ymax - ymin) after autoscale
        ('x_lim_min', None), # Minimum (xmax - xmin) after autoscale
        ('sep'    , ()),
        ('formats', ('pdf',)),
        ('close'  , True),
        ('dpi'    , None),
        ('bbox'   , None),
        ('remove_frame', None),
    ))

    def __repr__(self):
        return '<%s graph "%s">' % (self.__class__.__name__, self.short_name)

    def __bool__(self): return bool(self.path)
    __nonzero__ = __bool__

    def __init__(self, parent=None, base_dir=None, short_name=None):
        # Save parent #
        self.parent = parent
        # If we got a file as base_dir #
        if isinstance(base_dir, FilePath):
            self.base_dir = base_dir.directory
            short_name    = base_dir.short_prefix
        # If no parent and no directory given get the calling script #
        if base_dir is None and parent is None:
            file_name     = os.path.abspath((inspect.stack()[1])[1])
            self.base_dir = os.path.dirname(os.path.abspath(file_name)) + '/'
            self.base_dir = Path(self.base_dir)
        # If no directory given but a parent is present we can guess #
        if base_dir is None:
            if hasattr(self.parent, 'p'):
                self.base_dir = self.parent.p.graphs_dir
            elif hasattr(self.parent, 'paths'):
                self.base_dir = self.parent.paths.graphs_dir
            elif hasattr(self.parent, 'autopaths'):
                self.base_dir = self.parent.autopaths.graphs_dir
            elif hasattr(self.parent, 'graphs_dir'):
                self.base_dir = self.parent.graphs_dir
            else:
                raise Exception("Please specify a `base_dir` for this graph.")
        else:
            self.base_dir = Path(base_dir)
        # Make sure the directory exists #
        self.base_dir.create_if_not_exists()
        # Short name #
        if short_name: self.short_name = short_name
        # Use the parents name or the base class name #
        if not hasattr(self, 'short_name'):
            if hasattr(self.parent, 'short_name'):
                self.short_name = self.parent.short_name
            else:
                self.short_name = camel_to_snake(self.__class__.__name__)

    @property_cached
    def path(self):
        return Path(self.base_dir + self.short_name + '.pdf')

    def __call__(self, *args, **kwargs):
        """
        Plot the graph if it doesn't exist. Then return the path to it.
        Force the re-runing with rerun=True.
        """
        if not self or kwargs.get('rerun'): self.plot(*args, **kwargs)
        return self.path

    def save_plot(self, fig=None, axes=None, **kwargs):
        # Import #
        from matplotlib import pyplot
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
        if 'x_grid' in self.params:
            if self.params['x_grid']: axes.xaxis.grid(True, linestyle=':')
            else: axes.xaxis.grid(False)
        if 'y_grid' in self.params:
            if self.params['y_grid']: axes.yaxis.grid(True, linestyle=':')
            else: axes.yaxis.grid(False)
        # Frame #
        if 'remove_frame' in self.params:
            axes.spines["top"].set_visible(False)
            axes.spines["right"].set_visible(False)
        # Data and source extra text #
        if hasattr(self, 'dev_mode') and self.dev_mode is True:
            fig.text(0.99, 0.98, time.asctime(), horizontalalignment='right')
            job_name = os.environ.get('SLURM_JOB_NAME', 'Unnamed')
            user_msg = 'user: %s, job: %s' % (getpass.getuser(), job_name)
            fig.text(0.01, 0.98, user_msg, horizontalalignment='left')
        # Nice digit grouping #
        import matplotlib
        if 'x' in self.params['sep']:
            separate = lambda x,pos: split_thousands(x)
            axes.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(separate))
        if 'y' in self.params['sep']:
            separate = lambda y,pos: split_thousands(y)
            axes.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(separate))
        # Add custom labels #
        if 'x_labels' in self.params: axes.set_xticklabels(self.params['x_labels'])
        if 'x_labels_rot' in self.params:
            pyplot.setp(axes.xaxis.get_majorticklabels(), rotation=self.params['x_labels_rot'])
        # Adjust font size #
        if 'x_labels_size' in self.params:
            pyplot.setp(axes.xaxis.get_majorticklabels(), fontsize=self.params['x_labels_size'])
        if 'y_labels_size' in self.params:
            pyplot.setp(axes.yaxis.get_majorticklabels(), fontsize=self.params['y_labels_size'])
        # Possibility to overwrite path #
        if 'path' in self.params:   path = FilePath(self.params['path'])
        elif hasattr(self, 'path'): path = FilePath(self.path)
        else:                       path = FilePath(self.short_name + '.pdf')
        # The arguments to save #
        save_args = {}
        if 'dpi'  in self.params: save_args['dpi']  = self.params['dpi']
        if 'bbox' in self.params: save_args['bbox_inches'] = self.params['bbox']
        # Save it as different formats #
        for ext in self.params['formats']:
            fig.savefig(path.replace_extension(ext), **save_args)
        # Close it #
        if self.params['close']: pyplot.close(fig)

    def plot_and_save(self, **kwargs):
        """
        Used when the plot method defined does not create a figure nor calls save_plot
        Then the plot method has to use self.fig.
        """
        from matplotlib import pyplot
        self.fig = pyplot.figure()
        self.plot()
        self.axes = pyplot.gca()
        self.save_plot(self.fig, self.axes, **kwargs)
        pyplot.close(self.fig)

    def plot(self, bins=250, **kwargs):
        """An example plot function. You have to subclass this method."""
        # Import #
        import numpy
        # Data #
        counts = [sum(map(len, b.contigs)) for b in self.parent.bins]
        # Linear bins in logarithmic space #
        if 'log' in kwargs.get('x_scale', ''):
            start, stop = numpy.log10(1), numpy.log10(max(counts))
            bins = list(numpy.logspace(start=start, stop=stop, num=bins))
            bins.insert(0, 0)
        # Plot #
        from matplotlib import pyplot
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
        """Not functional -- TODO."""
        from matplotlib import animation
        anim = animation.FuncAnimation(fig, animate, init_func=init, frames=360, interval=20)
        FFMpegWriter = animation.writers['ffmpeg']
        writer = FFMpegWriter(bitrate= bitrate, fps=fps)
        # Save #
        self.avi_path = self.base_dir + self.short_name + '.avi'
        anim.save(self.avi_path, writer=writer, codec='x264')
