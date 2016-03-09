"""
This file handles the I/O of data from Elasticsearch.  It facilitates the dynamic description of scraped content,
and aids in feeding that content into the analyzers.  It handles the feedback loop of analyzed results back into
Elasticsearch, so that they are accessible for presentation.
"""

class DataSource(object):
    def __init__(self, elastic_hosts, index_name):
        pass

    def select_data(self, pattern, sub_pattern=None):
        """
        recursively selects data, querying first with pattern, then with sub-pattern.
        Sub-pattern may be <some nested structure> to facilitate arbitrary nested data structures.

        :return: iterator over selected data pattern, key is ID of data item in its native structure, value is data item.
        """
        pass

    def append_data(self, changed_data, field_name):
        """
        Update Elasticsearch with new data from processing.  changed_data should have id.  field_name is new field
        to be stored with that record.

        :param changed_data:
        :param field_name:
        :return:
        """
        pass