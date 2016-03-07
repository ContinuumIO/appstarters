"""
Analyze collection of some data structure, returning average sentiment value for each element of the data collection
"""

from textblob import TextBlob

def calculate_sentiment(input_data):
    """
    input data can either be a string, or a dictionary with document ID as key, and content as text.
    Content can in turn be a key-value pair of more content.  For example, a reddit post would be the outer ID, and
    it would have a score as the mean of its comments.  Its associated comment page would contain comments,
    each of would have their own score as the mean of their component sentences.

    :param input_data:
    :return:
    """
    pass


def calculate_keywords(input_data):
    """
    input data can either be a string, or a dictionary with document ID as key, and content as text.
    Content can in turn be a key-value pair of more content.  For example, a reddit post would be the outer ID, and
    it would have a collection of keywords in its post content.  Its associated comment page would contain comments,
    each of would have their own score as the mean of their component sentences.
    """
    pass
