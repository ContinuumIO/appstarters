from __future__ import print_function
import datetime

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from ..items import RedditCommentItem, RedditPostItem


def parse_comments(response):
    item = response.meta["item"]
    for comment in response.xpath('//div[@data-type="comment"]'):
        l = ItemLoader(RedditCommentItem(), selector=comment)
        comment_root_xpath = './div[contains(@class, "entry")]'
        tagline = comment_root_xpath + '/p'
        content = comment_root_xpath + '/form'
        buttons = comment_root_xpath + '/ul'
        l.add_xpath('poster', tagline + '/a[contains(@class, "author")]/text()')
        l.add_xpath('score', tagline + '/span[contains(@class, "unvoted")]/text()')
        l.add_xpath('post_timestamp', tagline + '/time/@datetime')
        l.add_value('scrape_timestamp', datetime.datetime.now())
        l.add_xpath('text', content + '/div[contains(@class, "usertext-body")]/div/p')
        l.add_xpath('permalink', buttons + '/li[@class="first"]/a[@class="bylink"]/@href')
        # l.add_xpath('parent', '//div[@class="product_title"]')
        # l.add_xpath('children', '//div[@class="product_title"]')
        item["comments"].append(dict(l.load_item()))
    return [item]


def parse_link_page(response):
    for post in response.xpath('//div[@data-type="link"]'):
        l = ItemLoader(RedditPostItem(), selector=post)
        post_root_xpath = './div[contains(@class, "entry")]'
        title = post_root_xpath + '/p[@class="title"]'
        tagline = post_root_xpath + '/p[@class="tagline"]'
        buttons = post_root_xpath + '/ul'
        l.add_xpath('title', title + '/a/text()')
        l.add_xpath('link', title + '/a/@href')
        l.add_xpath('poster', tagline + '/a[contains(@class, "author")]/text()')
        l.add_xpath('score', tagline + '//div[contains(@class, "score unvoted")]/text()')
        l.add_xpath('number_of_comments', buttons + '//a[contains(@class, "comments")]/text()')
        l.add_xpath('comments_link', buttons + '//a[contains(@class, "comments")]/@href')
        l.add_xpath('subreddit', '/@data-subreddit')
        l.add_xpath('post_timestamp', tagline + '/time/@datetime')
        l.add_value('scrape_timestamp', datetime.datetime.now())

        item = l.load_item()
        # if there are any comments for the post, go scrape them
        item["comments"] = []
        if item["number_of_comments"] > 0:
            print("trying to scrape comment page")
            yield scrapy.Request(item["comments_link"], callback=parse_comments,
                                 meta={'item': item})
        yield l.load_item()


class RedditSpider(scrapy.Spider):
    name = "reddit"
    allowed_domains = ["reddit.com"]
    start_urls = (
        'https://www.reddit.com/r/Python',
    )

    index = 'reddit_python'

    #rules = (
        #Rule(LinkExtractor(allow=('https://www.reddit.com/r/IAmA/comments/470yep/videogameattorney_here_to_answer_questions_about/')), callback='parse_comments'),
        #Rule(LinkExtractor(allow=('https://www.reddit.com/r/[A-Za-z0-9_]+/comments/[A-Za-z0-9_]+/we_are_rocksdb_developers_ask_us_anything/$')), callback='parse_comments', follow=True), #[A-Za-z0-9\._+]+

        #Rule(LinkExtractor(allow=('?count=25&')))
    #)

    def parse(self, response):
        return parse_link_page(response)


