# Built-in modules #
import os, time, getpass

# Internal modules #
from common import split_thousands
from autopaths import FilePath
from collections import OrderedDict

# Third party modules #
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
    default_params = OrderedDict((
        ('width'  , 12.0),
        ('height' , 7.0),
        ('bottom' , 0.14),
        ('top'    , 0.93),
        ('left'   , 0.06),
        ('right'  , 0.98),
        ('x_grid' , False),
        ('y_grid' , False),
        ('x_scale', None),
        ('y_scale', None),
        ('sep'    , ()),
        ('formats', ('pdf',)),
    ))

    def __nonzero__(self): return self.path.__nonzero__()

    def __init__(self, parent=None, base_dir=None, short_name=None):
        # Save parent #
        self.parent = parent
        # Base dir #
        if base_dir is None: self.base_dir = self.parent.p.graphs_dir
        else: self.base_dir = base_dir
        # Short name #
        if short_name: self.short_name = short_name
        if not hasattr(self, 'short_name'): self.short_name = 'graph'
        # Paths #
        self.path = FilePath(self.base_dir + self.short_name + '.pdf')

    def __call__(self, *args, **kwatgs):
        """Plot the graph if it doesn't exist. Then return the path to it."""
        if not self: self.plot(*args, **kwatgs)
        return self.path

    def save_plot(self, fig, axes, **kwargs):
        # Parameters #
        self.params = {}
        for key in self.default_params:
            if key in kwargs:                      self.params[key] = kwargs[key]
            elif hasattr(self, key):               self.params[key] = getattr(self, key)
            elif self.default_params[key] != None: self.params[key] = self.default_params[key]
        # Backwards compatibility #
        if kwargs.get('x_log', False): self.params['x_scale'] = 'symlog'
        if kwargs.get('y_log', False): self.params['y_scale'] = 'symlog'
        # Log #
        if 'x_scale' in self.params: axes.set_xscale(self.params['x_scale'])
        if 'y_scale' in self.params: axes.set_xscale(self.params['y_scale'])
        # Adjust #
        fig.set_figwidth(self.params['width'])
        fig.set_figheight(self.params['height'])
        fig.subplots_adjust(hspace=0.0, bottom = self.params['bottom'], top   = self.params['top'],
                                        left   = self.params['left'],   right = self.params['right'])
        # Grid #
        axes.xaxis.grid(self.params['x_grid'])
        axes.yaxis.grid(self.params['y_grid'])
        # Data and source #
        if hasattr(self, 'dev_mode') and self.dev_mode is True:
            fig.text(0.99, 0.98, time.asctime(), horizontalalignment='right')
            job_name = os.environ.get('SLURM_JOB_NAME', 'Unnamed')
            user_msg = 'user: %s, job: %s' % (getpass.getuser(), job_name)
            fig.text(0.01, 0.98, user_msg, horizontalalignment='left')
        # Nice digit grouping #
        if 'x' in self.params['sep']:
            seperate = lambda x,pos: split_thousands(x)
            axes.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(seperate))
        if 'y' in self.params['sep']:
            seperate = lambda y,pos: split_thousands(y)
            axes.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(seperate))
        # Add custom labels #
        if 'x_labels' in kwargs: axes.set_xticklabels(kwargs['x_labels'])
        if 'x_labels_rot' in kwargs: pyplot.setp(axes.xaxis.get_majorticklabels(), rotation=kwargs['x_labels_rot'])
        # Possibility to overwrite path #
        if 'path' in kwargs: path = FilePath(kwargs['path'])
        else:                path = self.path
        # Save it as different formats #
        for ext in self.params['formats']: fig.savefig(path.replace_extension(ext))

    def plot(self, **kwargs):
        """An example plot function. You have to subclass this method."""
        fig = pyplot.figure()
        axes = fig.add_subplot(111)
        axes.plot([0,1,10,1000], [0,1,2,3], 'ro')
        axes.set_title("Rarefaction curve of the diversity estimate")
        axes.set_xlabel("Sequences rarefied down to this many sequences")
        axes.set_ylabel("The diversity estimate")
        axes.set_xlim(0, axes.get_xlim()[1])
        self.save_plot(fig, axes, **kwargs)
        pyplot.close(fig)

    def save_anim(self, fig, animate, init, bitrate=10000, fps=30):
        """Not functional -- TODO"""
        from matplotlib import animation
        anim = animation.FuncAnimation(fig, animate, init_func=init, frames=360, interval=20)
        FFMpegWriter = animation.writers['ffmpeg']
        writer = FFMpegWriter(bitrate= bitrate, fps=fps)
        # Save #
        self.avi_path = self.base_dir + self.short_name + '.avi'
        anim.save(self.avi_path, writer=writer, codec='x264')
