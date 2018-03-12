# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.conf import settings
import pymongo
from scrapy.exceptions import DropItem
import redis

class XueqiucrawlerPipeline(object):
    def process_item(self, item, spider):
        return item

class DuplicatesPipeline(object):
    def __init__(self):
        host = settings['REDIS_HOST']
        port = settings['REDIS_PORT']
        db = 0
        self.redis_db = redis.Redis(host=host, port=port, db=db)
        self.redis_data_dict = "Mongodb_Item_Data"

    def process_item(self, item, spider):
        # 如果该item已经在redis中出现了，那么丢弃
        if self.redis_db.hexists(self.redis_data_dict, item['user_id']):
            raise DropItem("Duplicate item found: %s" % item)
            # raise DropItem("Duplicate item found!!!")
        else:
            # 如果没有出现过，那么将该item的信息插入到redis中
            self.redis_db.hset(self.redis_data_dict, item['user_id'], 0)
            return item

class MongoPipeline(object):
    def __init__(self):
        host = settings['MONGODB_HOST']
        port = settings['MONGODB_PORT']
        dbName = settings['MONGODB_DBNAME']
        col = settings['MONGODB_COLLECTION']

        client = pymongo.MongoClient(host=host, port=port)
        db = client[dbName]
        self.post = db[col]

    def process_item(self, item, spider):
        user = dict(item)
        self.post.insert(user)
        return item