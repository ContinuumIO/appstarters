"""
This file handles the I/O of data from Elasticsearch.  It facilitates the dynamic description of scraped content,
and aids in feeding that content into the analyzers.  It handles the feedback loop of analyzed results back into
Elasticsearch, so that they are accessible for presentation.
"""