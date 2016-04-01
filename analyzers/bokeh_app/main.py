import datetime

from bokeh.models import TextInput, Select, HBox, VBoxForm, VBox, Icon, Range1d
from bokeh.io import curdoc

import elasticsearch

from sentimenthistory import sentiment_history_plot

# make logging quiet during testing, to keep Travis CI logs short.
import logging
logging.basicConfig()
logging.getLogger('elasticsearch').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

categories = ["Very bad", "Bad", "Annoying", "meh", "Pleasant", "Good", "Very good"]

def get_es_indices(hosts):
    instance = elasticsearch.Elasticsearch(hosts)
    return instance.cat.indices(h="index").split()


def get_es_doctypes(hosts, index):
    instance = elasticsearch.Elasticsearch(hosts)
    return instance.indices.get_mapping(index)[index]["mappings"].keys()

def get_content_and_time_mappings(hosts, index, doctype):
    instance = elasticsearch.Elasticsearch(hosts)
    fields = instance.indices.get_mapping(index)[index]["mappings"][doctype]["properties"]
    content_fields = [field for field in fields if fields[field]["type"] =='string']
    time_fields = [field for field in fields if fields[field]["type"] == 'date']
    return content_fields, time_fields

hosts = "smalls:9200"
# UI elements
hosts_input = TextInput(title="Elasticsearch host", value=hosts)
index_input = Select(title="Elasticsearch index", options=get_es_indices(hosts_input.value),
                     value=get_es_indices(hosts_input.value)[0])
doctype_input = Select(title="Elasticsearch doctype", options=get_es_doctypes(hosts_input.value, index_input.value),
                       value=get_es_doctypes(hosts_input.value, index_input.value)[0])
query_input = TextInput(title="Elasticsearch query", value='{}')
content_options, time_options = get_content_and_time_mappings(hosts_input.value, index_input.value, doctype_input.value)
content_field_input = Select(title="Content field", options=content_options, value='text')
time_field_input = Select(title="Date field", options=time_options, value='post_timestamp')
interval_value_input = TextInput(title="Time interval", value='1')
interval_units_input = Select(title='Time interval unit', options=["d", "h"], value='d')
now = datetime.datetime.now()
#date_range_input = DateRangeSlider(title="Date range", value=(now-datetime.timedelta(days=30), now))
spinner = Icon(icon_name='spinner')
# TODO: change number of categories and alter labels


initial_data = sentiment_history_plot.query_sentiment(content_field=content_field_input.value,
                                                      time_field=time_field_input.value,
                                                      hosts=hosts_input.value,
                                                      query=query_input.value,
                                                      doctype=doctype_input.value,
                                                      #start_time=start_date,
                                                      #end_time=end_date,
                                                      interval=interval_value_input.value+interval_units_input.value,
                                                      categories=categories,)
initial_plots = sentiment_history_plot.sentiment_history_plots(initial_data)
area_plot, area_renderers = (initial_plots["area"]["plot"], initial_plots["area"]["renderers"])
mean_plot, mean_renderers = (initial_plots["mean"]["plot"], initial_plots["mean"]["renderers"])


# with new server specified, populate the available indices
def update_server_info(attr, old, new):
    index_input.menu = get_es_indices(new)
    # TODO: if only one present, select automatically
    # TODO: clear doctype
    # TODO: clear plot?


# with index specified, populate doctype
def update_index(attr, old, new):
    doctype_input.menu = get_es_doctypes(hosts_input.value, new)
    # TODO: if only one present, select automatically
    # TODO: clear content field and time field inputs
    # TODO: clear plot?


# with index and doctype specified, populate the available fields
def update_doctype_info(attr, old, new):
    content_field_input.menu, time_field_input.menu = get_content_and_time_mappings(hosts_input.value,
                                                                                    index_input.value,
                                                                                    new)
    # TODO: if both content and time have only one possibility, choose automatically
    # TODO: clear plot?


# data update callback
def update_data(attr, old, new):
    interval = interval_value_input.value + interval_units_input.value
    #start_date, end_date = date_range_input.value
    # show spinner to say we're working
    spinner.spin = True
    spinner.disabled = False
    new_data = sentiment_history_plot.query_sentiment(content_field=content_field_input.value,
                                                      time_field=time_field_input.value,
                                                      hosts=hosts_input.value,
                                                      query=query_input.value,
                                                      doctype=doctype_input.value,
                                                      #start_time=start_date,
                                                      #end_time=end_date,
                                                      interval=interval,
                                                      categories=categories,
                                                      )
    areas, time = sentiment_history_plot.data_to_areas(new_data["area"])
    area_plot.set(y_range=Range1d(start=1.1*new_data['area'].min().min(), end=1.1*new_data['area'].max().max()))
    for category in area_renderers:
        ds = area_renderers[category].data_source
        ds.data['x'] = time
        ds.data['y'] = areas[category]
        ds.trigger('data', ds.data, ds.data)
    ds = mean_renderers[0].data_source
    ds.data['x'] = new_data['mean'].index.values
    ds.data['y'] = new_data['mean'].values
    ds.trigger('data', ds.data, ds.data)
    # if start_date or end_date:
    #
    #     area_plot.set(x_range=Range1d(left, right), y_range=Range1d(bottom, top))
    #     mean_plot.set(x_range=Range1d(left, right), y_range=Range1d(bottom, top))
    # hide spinner
    spinner.spin = False
    spinner.disabled = True


# set up widgets with callback:
hosts_input.on_change('value', update_server_info)
index_input.on_change('value', update_index)
doctype_input.on_change('value', update_doctype_info)
for w in [content_field_input, time_field_input, query_input, interval_units_input, interval_value_input]:
    w.on_change('value', update_data)

elastic_inputs = VBox(children=[
                       HBox(children=[hosts_input, index_input, doctype_input]),
                       HBox(children=[content_field_input, time_field_input]),
                      ]
                      )
parameter_inputs = VBox(children=[
                         HBox(children=[query_input, spinner]),
                         HBox(children=[interval_value_input,
                                        interval_units_input,]),
                               #date_range_input
                         ])

# put the button and plot in a layout and add to the document
curdoc().add_root(VBoxForm(children=[
    HBox(children=[VBox(children=[elastic_inputs, parameter_inputs]),
                   VBox(children=[area_plot, mean_plot]),
                   ])]))
