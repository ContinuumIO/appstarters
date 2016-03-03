import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader


class RedditDepthFinderSpider(CrawlSpider):
    name = "reddit_depth_finder"
    allowed_domains = ["reddit.com"]
    start_urls = (
        'https://www.reddit.com/r/IAmA/',
        #'https://www.reddit.com/r/IAmA/comments/470yep/videogameattorney_here_to_answer_questions_about/',
    )
    #global subreddit_depth = 0

    index = 'reddit_results'

    rules = (
        #Rule(LinkExtractor(allow=('https://www.reddit.com/r/IAmA/comments/470yep/videogameattorney_here_to_answer_questions_about/')), callback='parse_comments'),
        #Rule(LinkExtractor(allow=('https://www.reddit.com/r/[A-Za-z0-9_]+/comments/[A-Za-z0-9_]+/we_are_rocksdb_developers_ask_us_anything/$')), callback='parse_comments', follow=True), #[A-Za-z0-9\._+]+

        Rule(LinkExtractor(allow=('/?count=')), callback='parse_page', follow=False),
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
            l.add_value('scrape_timestamp',datetime.datetime.now())
            l.add_xpath('text', content + '/div[contains(@class, "usertext-body")]/div/p/text()')
            l.add_xpath('permalink', buttons + '/li[@class="first"]/a[@class="bylink"]/@href')
            # l.add_xpath('parent', '//div[@class="product_title"]')
            # l.add_xpath('children', '//div[@class="product_title"]')
            yield l.load_item()
        #for next_link in response.xpath('//')

    def parse_page(self, response):
        # for link in response.xpath('//a'):
        #     print(link)
        for i, count_link in enumerate(response.xpath('//a[contains(@href, "/?count=")/..')):
            print('='*50)
            print(i)
            print('-'*50)
            print(count_link)
            print('='*50)



    # def parse(self, response):
    #     return self.parse_comments(response)
