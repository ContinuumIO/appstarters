# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import datetime

from elasticsearch import Elasticsearch, helpers


class ElasticsearchPipeline(object):
    batch_size = 1000

    def open_spider(self, spider):
        self.es_instance = Elasticsearch()
        self.batch = []
        self.index = spider.index
        if self.es_instance.indices.exists(index=self.index):
            self.es_instance.indices.delete(self.index)
        self.es_instance.indices.create(self.index)

    def process_item(self, item, spider):
        # add item to the batch upload queue.  Does not actually upload yet
        self.batch.append({"_source": dict(item), "_type": spider.name,
                           "_scraped_date": datetime.datetime.now()})
        # This triggers an upload every 'batch_size' items
        if len(self.batch) >= self.batch_size:
            helpers.bulk(client=self.es_instance, actions=self.batch, index=self.index)
            self.batch = []

    def close_spider(self, spider):
        # this uploads any remaining items, if collection of items was not evenly divisible by batch_size
        if self.batch:
            helpers.bulk(client=self.es_instance, actions=self.batch, index=self.index)
        self.es_instance.indices.refresh(self.index)
