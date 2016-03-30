import numpy as np

from bokeh.models import Button, TextInput, DateRangeSlider, Dropdown
from bokeh.plotting import curdoc, vplot
import sentiment_history_plot


# add a text renderer to out plot (no data yet)
r = p.text(x=[], y=[], text=[], text_color=[], text_font_size="20pt",
           text_baseline="middle", text_align="center")

i = 0
renderers, plot = sentiment_history_plot.

ds = r.data_source

# create a callback that will add a number in a random location
def callback():
    global i
    ds.data['x'].append(np.random.random()*70 + 15)
    ds.data['y'].append(np.random.random()*70 + 15)
    ds.data['text'].append(str(i))
    ds.trigger('data', ds.data, ds.data)
    i = i + 1

def hosts_changed():
    pass

def query_changed():
    pass

def date_changed():
    pass

def time_group_changed():
    pass

# add a button widget and configure with the call back
hosts = TextInput(title="Elasticsearch host", callback=hosts_changed)
query = TextInput(title="Elasticsearch query", callback=hosts_changed)
interval_value = TextInput(title="Time interval", callback=hosts_changed, callback=)
interval_units = Dropdown(default_value="days", menu=[("days", "d"), ("hours", "h")], callback=)
date_range = DateRangeSlider(title="Date range", callback=)

# put the button and plot in a layout and add to the document
curdoc().add_root(vplot(hosts, query, interval_value, interval_units, date_range, p))