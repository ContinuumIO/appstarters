import datetime

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from ..items import RedditCommentItem


class RedditSpider(CrawlSpider):
    name = "reddit"
    allowed_domains = ["reddit.com"]
    start_urls = (
        'https://www.reddit.com/r/IAmA/',
        #'https://www.reddit.com/r/IAmA/comments/470yep/videogameattorney_here_to_answer_questions_about/',
    )
    index = 'reddit_comments'

    rules = (
        #Rule(LinkExtractor(allow=('https://www.reddit.com/r/IAmA/comments/470yep/videogameattorney_here_to_answer_questions_about/')), callback='parse_comments'),
        Rule(LinkExtractor(allow=('https://www.reddit.com/r/[A-Za-z0-9_]+/comments/[A-Za-z0-9_]+/we_are_rocksdb_developers_ask_us_anything/$')), callback='parse_comments', follow=True), #[A-Za-z0-9\._+]+
        #Rule(LinkExtractor(allow=('ronnie_coleman')), callback='parse_comments', follow=False),
        #Rule(LinkExtractor(allow=('comments')), callback='parse_comments', follow=False),
        #Rule(LinkExtractor(allow=('?count=25&')))
    )

    def parse_comments(self, response):
        for comment in response.xpath('//div[@data-type="comment"]'):
            l = ItemLoader(RedditCommentItem(), selector=comment)
            comment_root_xpath = './div[contains(@class, "entry")]'
            tagline = comment_root_xpath + '/p'
            content = comment_root_xpath + '/form'
            buttons = comment_root_xpath + '/ul'
            l.add_xpath('poster', tagline + '/a[contains(@class, "author")]/text()')
            l.add_xpath('score', tagline + '/span[contains(@class, "unvoted")]/text()')
            l.add_xpath('post_timestamp', tagline + '/time/@datetime')
            l.add_value('scrape_timestamp',datetime.datetime.now())#datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%H:%M:%S'))
            l.add_xpath('text', content + '/div[contains(@class, "usertext-body")]/div/p/text()')
            l.add_xpath('permalink', buttons + '/li[@class="first"]/a[@class="bylink"]/@href')
            # l.add_xpath('parent', '//div[@class="product_title"]')
            # l.add_xpath('children', '//div[@class="product_title"]')
            yield l.load_item()

    def parse_page(self, ):
        pass

    # def parse(self, response):
    #     return self.parse_comments(response)
