# Third party modules #
import brewer2mpl

################################################################################
# Nice colors from the brewer project #
colors = brewer2mpl.get_map('Set1', 'qualitative', 8).mpl_colors
colors.reverse()
colors += brewer2mpl.get_map('Set2',    'qualitative', 8).mpl_colors
colors += brewer2mpl.get_map('Set3',    'qualitative', 8).mpl_colors
colors += brewer2mpl.get_map('Pastel1', 'qualitative', 8).mpl_colors
colors += brewer2mpl.get_map('Pastel2', 'qualitative', 8).mpl_colors
colors += brewer2mpl.get_map('Greys',   'sequential',  8).mpl_colors

################################################################################
# Nice colors for plotting stacked bar charts #
other_colors = ["#9b59b6", "#3498db", "#95a5a6", "#e74c3c", "#34495e", "#2ecc71",
                "#FCD124", "#5F0061", "#FBBEBA", "#AAC2F6", "#606925", "#469A55",
                "#ABD8B2", "#B4B1ED", "#613162", "#76C3E5", "#F05575", "#48CBD1"]
