import os
import logging

from bokeh.models import CustomAction, CustomJS, tools, ColumnDataSource
from bokeh.palettes import Blues
from bokeh.plotting import figure

logger = logging.getLogger(__name__)

WEEKDAY = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def configure_figure(plot, url_help):
    """Common configuration for all the figures"""
    my_path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(my_path, "help.png")
    info_tool = CustomAction(icon=path,
                             callback=CustomJS(code=f"window.open('{url_help}', '_blank');"),
                             action_tooltip='More information about this figure.')
    plot.title.align = 'center'
    plot.toolbar.logo = None
    plot.toolbar.active_drag = None
    plot.left[0].formatter.use_scientific = False
    plot.add_tools(info_tool,
                   tools.PanTool(dimensions='width'),
                   tools.WheelZoomTool(dimensions='width'),
                   tools.WheelZoomTool(dimensions='height'),
                   tools.SaveTool(),
                   tools.ResetTool())


def configure_heatmap(plot, url_help):
    """Configuration for heatmap figures"""
    my_path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(my_path, "help.png")
    info_tool = CustomAction(icon=path,
                             callback=CustomJS(code=f"window.open('{url_help}', '_blank');"),
                             action_tooltip='More information about this figure.')
    plot.title.align = 'center'
    plot.toolbar.logo = None
    plot.toolbar.active_drag = None
    plot.grid.grid_line_color = None
    plot.axis.axis_line_color = None
    plot.axis.major_tick_line_color = None
    plot.axis.major_label_standoff = 0
    plot.add_tools(info_tool)


def weekday_vbar_figure(top, y_axis_label, title, tooltips, url_help):
    """Create a vbar figure for weekday"""
    source = ColumnDataSource(data=dict(
        top=top,
        x=WEEKDAY
    ))

    plot = figure(y_axis_label=y_axis_label,
                  height=300,
                  sizing_mode="stretch_width",
                  x_range=WEEKDAY,
                  tools='')
    plot.title.text = title
    configure_figure(plot, url_help)

    plot.vbar(x='x', top='top',
              source=source,
              width=0.9,
              color=Blues[3][0])

    plot.add_tools(tools.HoverTool(
        tooltips=tooltips,
        mode='vline',
        toggleable=False
    ))
    return plot


def year_over_year(current, previous):
    """Calculate the % increase of year-over-year"""
    try:
        result = ((current - previous) / previous) * 100
    except ZeroDivisionError:
        result = 0
    return result


def get_interval(from_date, to_date):
    """
    Checks if the visualizations should be aggregated by days or weeks
    :return agg_name, elastic_agg, bokeh_bar_width
    """
    # week = 1000 ms/s * 60 s/m * 60 m/h * 24 h/d * 7 d/w * 0.9
    # day = 1000 ms/s * 60 s/m * 60 m/h * 24 h/d * 0.9
    delta = to_date - from_date
    if delta.days > 150:
        return 'week', '1w', 544320000
    else:
        return 'day', '1d', 77760000
