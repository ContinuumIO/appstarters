# -*- coding: utf-8 -*-

import datetime
import re

import elasticsearch as es
import elasticsearch.helpers as helpers
import numpy as np
import pandas as pd
from textblob import TextBlob
from bokeh.palettes import brewer
from bokeh.plotting import figure
from bokeh.io import output_file, show

import json


# batch for uploading sentiment values to ES
batch_size=1000


def get_elasticsearch_data(hosts, content_field, time_field, query={}, doc_type="comment"):
    instance = es.Elasticsearch(hosts=hosts)
    calculate_sentiment(instance=instance, content_field=content_field, query=query, doc_type=doc_type)
    return helpers.scan(instance, query=query, _source=[content_field, time_field, content_field+"_sentiment"],
                        doc_type=doc_type)


def calculate_sentiment(instance, content_field, query, doc_type):
    batch = []
    indices = []
    query = json.loads(query)
    # TODO: this breaks people's ability to use their own filters.  It's not too bad - just this process might take longer.
    query = {"query": {"filtered": {
        "filter": {
            "missing": {"field": content_field+"_sentiment"}
        }}}}
    iterable = helpers.scan(instance, query=json.dumps(query), _source=[content_field],
                        doc_type=doc_type)
    for item in iterable:
        action = {'_op_type': 'update',
                  '_index': item["_index"],
                  '_type': item["_type"],
                  '_id': item["_id"],
                  'doc': {content_field+"_sentiment": TextBlob(item["_source"][content_field]).polarity},
                  'doc_as_upsert': "true",
                  }
        batch.append(action)
        indices.append(item["_index"])
        if len(batch) >= batch_size:
            helpers.bulk(client=instance, actions=batch)
            batch = []
    if batch:
        helpers.bulk(client=instance, actions=batch)
    indices = set(indices)
    for index in indices:
        instance.indices.refresh(index)

def get_sentiment_dataframe(elasticsearch_iterable, content_field, time_field):
    """
    Given input data as generator or collection of records, this processes the text field, obtaining the sentiment,
    and returns a pandas DataFrame that has the time field as the index.
    """
    # TODO: get rid of _source garbage (see Topik)
    df = pd.DataFrame(((item["_source"][time_field], item["_source"][content_field],
                        item["_source"][content_field+"_sentiment"]) for item in elasticsearch_iterable),
                      columns=[time_field, content_field, content_field+"_sentiment"])
    df[time_field] = pd.to_datetime(df[time_field])
    df.set_index(time_field, inplace=True)
    return df


def slice_data(data, start_time, interval):
    """Divide input data up into time chunks.

    data : a Pandas dataframe with the time as the primary index
    start_time : A datetime.datetime object representing a time to start from.  Times after this time are not part
         of the output of this function.  A value of None means datetime.datetime.now()
    interval : A datetime.timedelta object.  Times start from the start_time, and step backwards through time with
         this timedelta as the step size.  This is the time-size of each chunk.
    """
    # it is essential that the data are sorted here.  If they are not, this step makes no sense at all.
    data = data.sort_index()
    current_time = start_time
    if not start_time:
        current_time = datetime.datetime.now()
    intervals = {}
    min_time = min(data.index)
    while current_time > min_time:
        start = data.index.searchsorted(current_time - interval)
        end = data.index.searchsorted(current_time)
        if not data.ix[start:end].empty:
            intervals[current_time - interval/2] = data.ix[start:end]
        current_time -= interval
    return intervals


def time_groups_to_plot_elements(slices, nbins, content_field):
    """Given the grouped time-sentiment relationships, break it down into a single point/line for the plot.

    In each time interval, sentiment is binned into ```nbins```, ranging from -1 to 1.  That time interval is
    represented in a new dataframe as the counts in each bin.  For negative sentiment, counts are negative.

    This data is directly plottable as a Bokeh area chart.
    """
    if nbins % 2 == 0:
        raise ValueError("number of categories should be an odd.  %d were provided." % nbins)
    plot_data = {}
    bins = np.linspace(-1.0, 1.0, nbins)
    for k, v in slices.items():
        binned_data = np.digitize(v[content_field+"_sentiment"], bins=bins) - 1
        segments = np.zeros(nbins)
        for bin_id in set(binned_data):
            segments[bin_id] = v[content_field+"_sentiment"][binned_data == bin_id].count()
        segments *= np.sign(bins)
        plot_data[k] = segments
    return plot_data


def query_sentiment(content_field, time_field, query={}, hosts="https://localhost:9200", doctype="comment",
                    start_time=None, interval=datetime.timedelta(days=1), categories=["negative", "null", "positive"]):
    records = get_elasticsearch_data(hosts=hosts, content_field=content_field, time_field=time_field, query=query,
                                     doc_type=doctype)
    # takes iterable records, outputs pandas dataframe
    raw_df = get_sentiment_dataframe(records, content_field=content_field, time_field=time_field)
    group_data = time_groups_to_plot_elements(slice_data(raw_df, start_time=start_time, interval=interval),
                                             len(categories), content_field=content_field)
    plot_data = pd.DataFrame(group_data).T.sort_index()
    plot_data.columns = categories
    return plot_data


def data_to_areas(plot_data):
    # concat the list of indexed y values into dataframe
    df = plot_data
    #  split the dataframe up into the negative and positive parts.  If negative and positive parts
    #    are both in the same column, this is wrong, and a per-row approach is needed.
    #  get rightmost column that has negative numbers in it
    right_negative = (df <= 0).all(axis=0).nonzero()[0][-1]
    #  get leftmost positive value that has numbers larger than
    left_positive = (df >= 0).all(axis=0).nonzero()[0][0]

    #  cumulative sum flips columns around so that summation goes opposite direction to positive space
    negative_sum = df[df.columns[:right_negative][::-1]].cumsum(axis=1)
    #  flip around to original order
    negative_sum = negative_sum[negative_sum.columns[::-1]]
    #  normal cumsum for the positive columns
    positive_sum = df[df.columns[left_positive:]].cumsum(axis=1)
    #  lower bounds of each area series are diff between stacked and orig values
    negative_lower_bounds = negative_sum
    negative_upper_bounds = negative_sum - df[negative_sum.columns]
    positive_lower_bounds = positive_sum - df[positive_sum.columns]
    positive_upper_bounds = positive_sum
    lower_bounds = negative_lower_bounds.join(positive_lower_bounds)
    #  reverse the df so the patch is drawn in correct order
    lower_bounds = lower_bounds.iloc[::-1]
    upper_bounds = negative_upper_bounds.join(positive_upper_bounds)
    # concat the upper and lower bounds together - note that lower bounds is reversed.
    #    reversal draws it backwards - think of it as a polygon.  Reversing one draws from start to finish.
    areas = {cat: np.hstack([lower_bounds[cat].values, upper_bounds[cat].values]) for cat in upper_bounds.keys()}
    time = np.hstack([plot_data.index[::-1], plot_data.index])
    return areas, time

def sentiment_history_plot(plot_data):
    areas, time = data_to_areas(plot_data)
    p = figure(x_axis_type="datetime")
    colors = brewer["RdBu"][len(areas)][::-1]
    for index, cat in enumerate(reversed(plot_data.columns)):
        p.patch(time, areas[cat], color=colors[index], alpha=0.8, line_color=None, legend=cat)
    return p


def show_sentiment_history_plot(plot_data, filename="sentiment_history.png"):
    output_file(filename=filename)
    show(sentiment_history_plot(plot_data))


# need a way to parse time intervals.  Gist from:
# https://gist.github.com/jnothman/4057689
class TimeDeltaType(object):
    """
    Interprets a string as a timedelta for argument parsing.
    With no default unit:
    >>> tdtype = TimeDeltaType()
    >>> tdtype('5s')
    datetime.timedelta(0, 5)
    >>> tdtype('5.5s')
    datetime.timedelta(0, 5, 500000)
    >>> tdtype('5:06:07:08s')
    datetime.timedelta(5, 22028)
    >>> tdtype('5d06h07m08s')
    datetime.timedelta(5, 22028)
    >>> tdtype('5d')
    datetime.timedelta(5)
    With a default unit of minutes:
    >>> tdmins = TimeDeltaType('m')
    >>> tdmins('5s')
    datetime.timedelta(0, 5)
    >>> tdmins('5')
    datetime.timedelta(0, 300)
    >>> tdmins('6:05')
    datetime.timedelta(0, 21900)
    And some error cases:
    >>> tdtype('5')
    Traceback (most recent call last):
        ...
    ValueError: Cannot infer units for '5'
    >>> tdtype('5:5d')
    Traceback (most recent call last):
        ...
    ValueError: Colon not handled for unit 'd'
    >>> tdtype('5:5ms')
    Traceback (most recent call last):
        ...
    ValueError: Colon not handled for unit 'ms'
    >>> tdtype('5q')
    Traceback (most recent call last):
        ...
    ValueError: Unknown unit: 'q'
    """

    units = {
        'd': datetime.timedelta(days=1),
        'h': datetime.timedelta(seconds=60 * 60),
        'm': datetime.timedelta(seconds=60),
        's': datetime.timedelta(seconds=1),
        'ms': datetime.timedelta(microseconds=1000),
    }
    colon_mult_ind = ['h', 'm', 's']
    colon_mults = [24, 60, 60]
    unit_re = re.compile(r'[^\d:.,-]+', re.UNICODE)

    def __init__(self, default_unit=None):
        self.default_unit = default_unit

    def __call__(self, val):
        res = datetime.timedelta()
        for num, unit in self._parse(val):
            unit = unit.lower()

            if ':' in num:
                try:
                    colon_mults = self.colon_mults[:self.colon_mult_ind.index(unit) + 1]
                except ValueError:
                    raise ValueError('Colon not handled for unit %r' % unit)
            else:
                colon_mults = []

            try:
                unit = self.units[unit]
            except KeyError:
                raise ValueError('Unknown unit: %r' % unit)

            mult = 1
            for part in reversed(num.split(':')):
                res += self._mult_td(unit, (float(part) if '.' in part else int(part)) * mult)
                if colon_mults:
                    mult *= colon_mults.pop()
        return res

    def _parse(self, val):
        pairs = []
        start = 0
        for match in self.unit_re.finditer(val):
            num = val[start:match.start()]
            unit = match.group()
            pairs.append((num, unit))
            start = match.end()
        num = val[start:]
        if num:
            if pairs or self.default_unit is None:
                raise ValueError('Cannot infer units for %r' % num)
            else:
                pairs.append((num, self.default_unit))
        return pairs

    @staticmethod
    def _mult_td(td, mult):
        # Necessary because timedelta * float is not supported:
        return datetime.timedelta(days=td.days * mult, seconds=td.seconds * mult, microseconds=td.microseconds * mult)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--hosts", help="Elasticsearch host(s)", nargs="+", required=True)
    parser.add_argument('--categories', help="Category labels, from negative to positive.  You need an odd number "
                                             "of text labels here.  E.g. 'good' 'ok' 'bad'",
                        nargs="+", required=True)
    parser.add_argument('-q', "--query", help="Text query, in Elasticsearch DSL format", default="{}")
    parser.add_argument('-c', "--content_field", help="Field to read text from", default="text")
    parser.add_argument('-t', "--time_field", help="Field to read time index from", default="post_timestamp")
    parser.add_argument('-d', "--doctype", help="Type of elasticsearch document to search", default="comment")
    parser.add_argument('-s', "--start_time", help="Study only entries from this time forward.  "
                                                   "Time is ISO 8601 format: yyyy-mm-ddThh:mm:ss.  Default (None) "
                                                   "is no limit.", default=None)
    parser.add_argument('-e', "--end_time", help="Study only entries from this time backward.  "
                                                   "Time is ISO 8601 format: yyyy-mm-ddThh:mm:ss.  Default (None) "
                                                   "is current time.", default=None)
    parser.add_argument('-i', "--interval", help="Time interval for grouping posts.  Examples: 4h, 1d", default="4h")

    args = parser.parse_args()
    tdtype = TimeDeltaType()
    interval = tdtype(args.interval)
    plot_data = query_sentiment(content_field=args.content_field, time_field=args.time_field, hosts=args.hosts,
                                categories=args.categories, query=args.query, doctype=args.doctype,
                                start_time=args.start_time, interval=interval)
    show_sentiment_history_plot(plot_data=plot_data, filename="sentiment_plot.html")
