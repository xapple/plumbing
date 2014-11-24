# Built-in modules #
import os, time, getpass

# Internal modules #
from common import split_thousands
from autopaths import FilePath

# Third party modules #
import matplotlib, brewer2mpl
from matplotlib import pyplot

# Constants #
cool_colors = brewer2mpl.get_map('Set1', 'qualitative', 8).mpl_colors
cool_colors.reverse()
cool_colors += brewer2mpl.get_map('Set2',    'qualitative', 8).mpl_colors
cool_colors += brewer2mpl.get_map('Set3',    'qualitative', 8).mpl_colors
cool_colors += brewer2mpl.get_map('Pastel1', 'qualitative', 8).mpl_colors
cool_colors += brewer2mpl.get_map('Pastel2', 'qualitative', 8).mpl_colors
cool_colors += brewer2mpl.get_map('Greys',   'sequential', 8).mpl_colors

################################################################################
class Graph(FilePath):
    width  = 12.0
    height = 7.0
    bottom = 0.14
    top    = 0.93
    left   = 0.06
    right  = 0.98
    formats = ('pdf',)

    def __init__(self, parent=None, base_dir=None, short_name=None):
        # Save parent #
        self.parent = parent
        # Base dir #
        if not base_dir: self.base_dir = self.parent.p.graphs_dir
        else: self.base_dir = base_dir
        # Short name #
        if short_name: self.short_name = short_name
        if not hasattr(self, 'short_name'): self.short_name = 'graph'
        # Paths #
        self.path = self.base_dir + self.short_name + '.pdf'

    def save_plot(self, fig, axes, width=None, height=None, bottom=None, top=None, left=None, right=None, sep=()):
        # Attributes or parameters #
        w = width  if width  != None else self.width
        h = height if height != None else self.height
        b = bottom if bottom != None else self.bottom
        t = top    if top    != None else self.top
        l = left   if left   != None else self.left
        r = right  if right  != None else self.right
        # Adjust #
        fig.set_figwidth(w)
        fig.set_figheight(h)
        fig.subplots_adjust(hspace=0.0, bottom=b, top=t, left=l, right=r)
        # Data and source #
        if hasattr(self, 'dev_mode'):
            fig.text(0.99, 0.98, time.asctime(), horizontalalignment='right')
            job_name = os.environ.get('SLURM_JOB_NAME', 'Unnamed')
            user_msg = 'user: %s, job: %s' % (getpass.getuser(), job_name)
            fig.text(0.01, 0.98, user_msg, horizontalalignment='left')
        # Nice digit grouping #
        if 'x' in sep:
            seperate = lambda x,pos: split_thousands(x)
            axes.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(seperate))
        if 'y' in sep:
            seperate = lambda y,pos: split_thousands(y)
            axes.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(seperate))
        # Save it as different formats #
        for ext in self.formats: fig.savefig(self.replace_extension(ext))

    def plot(self):
        """An example plot function. You have to subclass this method."""
        fig = pyplot.figure()
        axes = fig.add_subplot(111)
        axes.plot([0,1,10,1000], [0,1,2,3], 'ro')
        axes.set_title("Rarefaction curve of the diversity estimate")
        axes.set_xlabel("Sequences rarefied down to this many sequences")
        axes.set_ylabel("The diversity estimate")
        axes.yaxis.grid(True)
        axes.set_xscale('symlog')
        axes.set_xlim(0, axes.get_xlim()[1])
        self.save_plot(fig, axes, sep=('x',))
        pyplot.close(fig)

    def save_anim(self, fig, animate, init, bitrate=10000, fps=30):
        """Not functional TODO"""
        from matplotlib import animation
        anim = animation.FuncAnimation(fig, animate, init_func=init, frames=360, interval=20)
        FFMpegWriter = animation.writers['ffmpeg']
        writer = FFMpegWriter(bitrate= bitrate, fps=fps)
        # Save #
        self.avi_path = self.base_dir + self.short_name + '.avi'
        anim.save(self.avi_path, writer=writer, codec='x264')
