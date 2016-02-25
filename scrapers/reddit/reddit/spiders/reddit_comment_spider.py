import scrapy
from scrapy.loader import ItemLoader
from ..items import RedditCommentItem


class RedditSpider(scrapy.Spider):
    name = "reddit"
    allowed_domains = ["reddit.com"]
    start_urls = (
        'https://www.reddit.com/r/IAmA/comments/470yep/videogameattorney_here_to_answer_questions_about/',
    )
    index = 'reddit_comments'

    def parse_comments(self, response):
        for comment in response.xpath('//div[@data-type="comment"]'):
            l = ItemLoader(RedditCommentItem(), selector=comment)
            comment_root_xpath = './div[contains(@class, "entry")]'
            tagline = comment_root_xpath + '/p'
            content = comment_root_xpath + '/form'
            buttons = comment_root_xpath + '/ul'
            l.add_xpath('poster', tagline + '/a[contains(@class, "author")]/text()')
            l.add_xpath('score', tagline + '/span[contains(@class, "unvoted")]/text()')
            l.add_xpath('timestamp', tagline + '/time/@datetime')
            l.add_xpath('text', content + '/div[contains(@class, "usertext-body")]/div/p/text()')
            l.add_xpath('permalink', buttons + '/li[@class="first"]/a[@class="bylink"]/@href')
            # l.add_xpath('parent', '//div[@class="product_title"]')
            # l.add_xpath('children', '//div[@class="product_title"]')
            yield l.load_item()

    def parse(self, response):
        return self.parse_comments(response)
