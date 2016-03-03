# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from datetime import datetime

import scrapy


def extract_string_from_list(input_object):
    """Extracts first string from list, if list is input.  Converts string to ascii."""
    if not hasattr(input_object, "lower"):
        # NOTE: discarding multiple entries here
        ret = input_object[0]
    else:
        ret = input_object
    return ret.encode("ascii", "replace")


def score_to_number(input_field):
    """output parser to get numeric score out of string"""
    return int(extract_string_from_list(input_field).split(" ")[0])


def time_string_to_datetime(input_field):
    return datetime.strptime(extract_string_from_list(input_field)[:-6], "%Y-%m-%dT%H:%M:%S")


class RedditCommentItem(scrapy.Item):
    poster = scrapy.Field(output_processor=extract_string_from_list)
    post_timestamp = scrapy.Field(output_processor=time_string_to_datetime)
    scrape_timestamp = scrapy.Field()
    text = scrapy.Field(output_processor=extract_string_from_list)
    score = scrapy.Field(output_processor=score_to_number)
    parent = scrapy.Field(output_processor=extract_string_from_list)
    children = scrapy.Field(output_processor=extract_string_from_list)
    permalink = scrapy.Field(output_processor=extract_string_from_list)

class SubRedditResultsPageItem(scrapy.Item):
    pass