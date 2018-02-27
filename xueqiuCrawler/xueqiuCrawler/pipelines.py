# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.conf import settings
import pymongo
from scrapy.exceptions import DropItem

class XueqiucrawlerPipeline(object):
    def process_item(self, item, spider):
        return item

class DuplicatesPipeline(object):
    def __init__(self):
        id_list = []
        with open('set_file.csv', 'r') as f:
            for id in f.readlines():
                id = id.strip()
                id_list.append(id)
        self.ids_seen = set(id_list)

    def process_item(self, item, spider):
        set_size = len(self.ids_seen)

        if set_size%3 == 0:
            # 备份set中的数据
            with open('set_file.csv', 'w') as f:
                for id in self.ids_seen:
                    f.write("%s\n" % str(id))

            # 在备份set的同时，将最新的id保存，便于在中断爬虫后，从断点启动
            with open('stop_log.csv', 'w') as f:
                f.write("%s\n" % str(item['user_id']))

        if set_size%10 == 0:
            print("there are %d items in the database" % set_size)

        if item['user_id'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(item['user_id'])
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