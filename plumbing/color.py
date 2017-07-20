################################################################################
# Nice colors for plotting stacked bar charts #
cool_colors = ["#9b59b6", "#3498db", "#95a5a6", "#e74c3c", "#34495e", "#2ecc71",
               "#FCD124", "#5F0061", "#FBBEBA", "#AAC2F6", "#606925", "#469A55",
               "#ABD8B2", "#B4B1ED", "#613162", "#76C3E5", "#F05575", "#48CBD1"]

################################################################################
class Color:
    """Shortcuts for the ANSI escape sequences to control
       formatting, color, etc. on text terminals. Use it like this:

            from plumbing.color import Color
            print Color.red + "Hello world" + Color.end

    An easy command to see all 256 possible colors in a terminal:

        $ for x in 0 1 4 5 7 8; do for i in `seq 30 37`; do for a in `seq 40 47`; do echo -ne "\e[$x;$i;$a""m\\\e[$x;$i;$a""m\e[0;37;40m "; done; echo; done; done; echo "";

    """
    # Special #
    end = '\033[0m'
    # Regular #
    blk   = '\033[0;30m' # Black
    red   = '\033[0;31m' # Red
    grn   = '\033[0;32m' # Green
    ylw   = '\033[0;33m' # Yellow
    blu   = '\033[0;34m' # Blue
    pur   = '\033[0;35m' # Purple
    cyn   = '\033[0;36m' # Cyan
    wht   = '\033[0;37m' # White
    # Bold #
    bold  = '\033[1m'
    b_blk = '\033[1;30m' # Black
    b_red = '\033[1;31m' # Red
    b_grn = '\033[1;32m' # Green
    b_ylw = '\033[1;33m' # Yellow
    b_blu = '\033[1;34m' # Blue
    b_pur = '\033[1;35m' # Purple
    b_cyn = '\033[1;36m' # Cyan
    b_wht = '\033[1;37m' # White
    # Light #
    light = '\033[2m'
    l_blk = '\033[2;30m' # Black
    l_red = '\033[2;31m' # Red
    l_grn = '\033[2;32m' # Green
    l_ylw = '\033[2;33m' # Yellow
    l_blu = '\033[2;34m' # Blue
    l_pur = '\033[2;35m' # Purple
    l_cyn = '\033[2;36m' # Cyan
    l_wht = '\033[2;37m' # White
    # Italic #
    italic = '\033[1m'
    i_blk = '\033[3;30m' # Black
    i_red = '\033[3;31m' # Red
    i_grn = '\033[3;32m' # Green
    i_ylw = '\033[3;33m' # Yellow
    i_blu = '\033[3;34m' # Blue
    i_pur = '\033[3;35m' # Purple
    i_cyn = '\033[3;36m' # Cyan
    i_wht = '\033[3;37m' # White
    # Underline #
    underline = '\033[4m'
    u_blk = '\033[4;30m' # Black
    u_red = '\033[4;31m' # Red
    u_grn = '\033[4;32m' # Green
    u_ylw = '\033[4;33m' # Yellow
    u_blu = '\033[4;34m' # Blue
    u_pur = '\033[4;35m' # Purple
    u_cyn = '\033[4;36m' # Cyan
    u_wht = '\033[4;37m' # White
    # Glitter #
    flash = '\033[5m'
    g_blk = '\033[5;30m' # Black
    g_red = '\033[5;31m' # Red
    g_grn = '\033[5;32m' # Green
    g_ylw = '\033[5;33m' # Yellow
    g_blu = '\033[5;34m' # Blue
    g_pur = '\033[5;35m' # Purple
    g_cyn = '\033[5;36m' # Cyan
    g_wht = '\033[5;37m' # White
    # Fill #
    f_blk = '\033[40m'   # Black
    f_red = '\033[41m'   # Red
    f_grn = '\033[42m'   # Green
    f_ylw = '\033[43m'   # Yellow
    f_blu = '\033[44m'   # Blue
    f_pur = '\033[45m'   # Purple
    f_cyn = '\033[46m'   # Cyan
    f_wht = '\033[47m'   # White