from bokeh.models import TextInput, DateRangeSlider, Dropdown
from bokeh.plotting import curdoc, vplot, hplot
import sentiment_history_plot

import elasticsearch

initial_data = sentiment_history_plot.query_sentiment()
plot, renderers = sentiment_history_plot.plot_data(initial_data)

# UI elements
hosts_input = TextInput(title="Elasticsearch host")
index_input = Dropdown(title="Elasticsearch index")
doctype_input = Dropdown(title="Elasticsearch doctype")
query_input = TextInput(title="Elasticsearch query")
content_field_input = Dropdown(title="Content field to analyze")
time_field_input = Dropdown(title="Field containing date information")
interval_value_input = TextInput(title="Time interval")
interval_units_input = Dropdown(default_value="days", menu=[("days", "d"), ("hours", "h")])
date_range_input = DateRangeSlider(title="Date range")


# with new server specified, populate the available indices
def update_server_info():
    instance = elasticsearch.Elasticsearch(hosts_input.value)
    index_input.menu = instance.cat.indices(h="index").split()
    # TODO: if only one present, select automatically


# with index specified, populate doctype
def update_index():
    instance = elasticsearch.Elasticsearch(hosts_input.value)
    doctype_input.menu = instance.indices.get_mapping(index_input.value)[index_input.value]["mappings"].keys()
    # TODO: if only one present, select automatically


# with index and doctype specified, populate the available fields
def update_doctype_info():
    instance = elasticsearch.Elasticsearch(hosts_input.value)
    mapping = instance.indices.get_mapping(index_input.value)[index_input.value]["mappings"][doctype_input.value]
    content_field_input.menu = [field for field in mapping["properties"] if mapping["properties"][field]["type"] =='string']
    time_field_input.menu = [field for field in mapping["properties"] if mapping["properties"][field]["type"] == 'date']
    # TODO: if both content and time have only one possibility, choose automatically


# data update callback
def update_data():
    interval = interval_value_input.value + interval_units_input.value
    start_date, end_date = date_range_input.value
    new_data = sentiment_history_plot.query_sentiment(content_field=content_field_input.value,
                                                      time_field=time_field_input.value,
                                                      hosts=hosts_input.value,
                                                      query=query_input.value,
                                                      doctype=doctype_input.value,
                                                      start_time=start_date,
                                                      end_time=end_date,
                                                      interval=interval,
                                                      )
    area_renderers = renderers["area"]
    areas, time = sentiment_history_plot.data_to_areas(new_data["area"])
    for category in area_renderers:
        ds = area_renderers[category.data_source]
        ds.data['x'] = time
        ds.data['y'] = areas[category]
        ds.trigger('data', ds.data, ds.data)
    ds = renderers["mean"].data_source
    ds["x"] = new_data["mean"].index
    ds["y"] = new_data["mean"].values
    ds.trigger('data', ds.data, ds.data)


# set up widgets with callback:
hosts_input.on_change('value', update_server_info)
index_input.on_change('value', update_index)
doctype_input.on_change('value', update_doctype_info)
for w in [content_field_input, time_field_input, interval_units_input, interval_value_input, date_range_input]:
    w.on_change('value', update_data)

# put the button and plot in a layout and add to the document
curdoc().add_root(vplot(
    hplot(hosts_input, index_input, content_field_input, time_field_input),
    hplot(query_input, interval_value_input, interval_units_input, date_range_input),
    plot)
)
