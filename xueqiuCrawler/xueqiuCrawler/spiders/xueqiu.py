# -*- coding: utf-8 -*-
import scrapy
import json
from collections import deque
from xueqiuCrawler.items import XueqiucrawlerItem
from xueqiuCrawler.scrapy_redis.spiders import RedisSpider

class XueqiuSpider(RedisSpider):
    name = 'xueqiu'
    allowed_domains = ['xueqiu.com']
    start_urls = ['https://xueqiu.com/friendships/groups/members.json?uid=5842900570&page=1&gid=0']
    first_user_id = 5842900570

    # 在关注页面用的header
    my_header = {
        "Host": "xueqiu.com",
        "Connection": "keep-alive",
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36",
        "Referer": "https://xueqiu.com/u/5762889842",
        "Accept-Encoding": "gzip, deflate, sdch",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Cookie": "td_cookie=338701011; aliyungf_tc=AQAAAOvaFSAArAEAM2QR2vUw5U3A5Hsl; device_id=f4d89148e010312ef03b184238d9604e; remember=1; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; xq_a_token=6996688c8a46d3bdd49d43036bf257392509955c; xq_a_token.sig=7myyYxgzK01MrFpWksSIEgsFtT4; xq_r_token=e28c8ac51f97890bae6c32c0fde60c931ecb0af8; xq_r_token.sig=gkp6Nft4mhaLxam5UbcajCwlilQ; xq_is_login=1; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; u=6507446955; u.sig=cSuuCuFU_r2EmTKvwOFMewzKcyI; s=fp11kaqr2c; bid=b7785bba313ecf158609498a2d9f49bf_jgof29ap; __utma=1.612525609.1525224047.1525224047.1525224047.1; __utmb=1.4.10.1525224047; __utmc=1; __utmz=1.1525224047.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); Hm_lvt_1db88642e346389874251b5a1eded6e3=1525224047; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1525224123"
        }
    def start_requests(self):
        for url in XueqiuSpider.start_urls:
            yield scrapy.Request(
                                url=url,
                                headers=XueqiuSpider.my_header,
                                callback=self.parse,
                                meta={'user_id':XueqiuSpider.first_user_id}
                                )

    def parse(self, response):
        """该解析函数主要用来收集用户的所有关注"""
        context = json.loads(response.text)

        current_id = response.meta['user_id']
        page_num = context['maxPage'] # 该用户总共有多少页面
        current_page = context['page'] # 目前是第几页

        for user in context['users']: # 遍历当前页面下的所有关注用户
            item = XueqiucrawlerItem()
            item['user_id'] = user['id']
            item['user_name'] = user['screen_name']
            item['follow_num'] = user['friends_count']
            item['fans_num'] = user['followers_count']
            yield item

            url_str = "https://xueqiu.com/friendships/groups/members.json?uid={user_id}&page=1&gid=0"
            next_url = url_str.format(user_id=user['id'])

            yield scrapy.Request(
                url=next_url,
                headers=XueqiuSpider.my_header,
                callback=self.parse,  # 开始收集用户的关注页面
                meta={'user_id': user['id']}  # 用户的id
            )

        if current_page >= page_num: # 当前用户的所有关注页面已经收集完毕
            #开始收集该用户粉丝页面的用户
            url_str = "https://xueqiu.com/friendships/followers.json?uid={user_id}&pageNo=1"
            url = url_str.format(user_id=current_id)
            yield scrapy.Request(
                url=url,
                headers=XueqiuSpider.my_header,
                callback=self.parse2, # 收集所有的粉丝
                meta={'user_id': current_id}
            )

        else: # 该用户的下一个关注页面
            url_str = "https://xueqiu.com/friendships/groups/members.json?uid={user_id}&page={page_id}&gid=0"
            page_id = int(current_page)+1
            next_url = url_str.format(user_id=current_id, page_id=page_id)

            yield scrapy.Request(
                url=next_url,
                headers=XueqiuSpider.my_header,
                callback=self.parse,
                meta={'user_id': current_id} # 仍然是当前用户的id
            )

    def parse2(self, response):
        context = json.loads(response.text)
        current_id = response.meta['user_id']
        page_num = context['maxPage']  # 该用户总共有多少页面
        current_page = context['page']  # 目前是第几页

        for user in context['followers']:  # 遍历当前页面下的所有用户
            item = XueqiucrawlerItem()
            item['user_id'] = user['id']
            item['user_name'] = user['screen_name']
            item['follow_num'] = user['friends_count']
            item['fans_num'] = user['followers_count']
            yield item

            url_str = "https://xueqiu.com/friendships/groups/members.json?uid={user_id}&page=1&gid=0"
            next_url = url_str.format(user_id=user['id'])

            yield scrapy.Request(
                url=next_url,
                headers=XueqiuSpider.my_header,
                callback=self.parse,  # 开始收集用户的关注页面
                meta={'user_id': user['id']}  # 用户的id
            )

        if current_page >= page_num:  # 当前用户的所有页面（关注+粉丝）已经收集完毕
            pass
        else:  # 该用户的下一个粉丝页面
            url_str = "https://xueqiu.com/friendships/followers.json?uid={user_id}&pageNo={page_id}"
            page_id = int(current_page) + 1
            next_url = url_str.format(user_id=current_id, page_id=page_id)

            yield scrapy.Request(
                url=next_url,
                headers=XueqiuSpider.my_header,
                callback=self.parse2,
                meta={'user_id': current_id}  # 仍然是当前用户的id
            )

class UserInfo(object):
    def __init__(self, user_id, user_name, follow_num, fans_num):
        self.user_id = user_id
        self.user_name = user_name
        self.follow_num = follow_num
        self.fans_num = fans_num