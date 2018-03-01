# -*- coding: utf-8 -*-
import scrapy
import json
from collections import deque
from xueqiuCrawler.items import XueqiucrawlerItem
from xueqiuCrawler.scrapy_redis.spiders import RedisSpider

class XueqiuSpider(RedisSpider):
    name = 'xueqiu'
    allowed_domains = ['xueqiu.com']
    start_urls = ['https://xueqiu.com/friendships/groups/members.json?uid=3386345727&page=1&gid=0']
    first_user_id = 3386345727
    id_queue = deque() # 层次遍历所有的用户
    # 在关注页面用的header
    my_header = {
        "Host": "xueqiu.com",
        "Connection": "keep-alive",
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",
        "Referer": "https://xueqiu.com/u/5762889842",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cookie": "device_id=288387fa2efe85a6e006edc54a5eda57; s=fp1157htg6; bid=b7785bba313ecf158609498a2d9f49bf_jcjuxw50; __utmz=1.1516242744.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); remember=1; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; xq_a_token=aae1db46abe1e1ed71f6fea88fde2ed306c64063; xq_a_token.sig=rHnC-h2pvBo_iFv1RBKNQsaUc6U; xq_r_token=8ef08c78aefc61aa9394f163640e68c81d338b99; xq_r_token.sig=tDqW3wGLsJBSypal5tKrNYGkbAw; xq_is_login=1; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; u=6507446955; u.sig=cSuuCuFU_r2EmTKvwOFMewzKcyI; aliyungf_tc=AQAAAPnKBHOEaw4AomIYdLQ43IMpgjBu; __utmc=1; Hm_lvt_1db88642e346389874251b5a1eded6e3=1517973487,1519619536,1519715701,1519727668; __utma=1.1764713070.1516242744.1519715704.1519727671.7; __utmt=1; __utmb=1.1.10.1519727671; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1519727795",
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
            id = user['id']
            screen_name = user['screen_name']
            follow_num = user['friends_count']
            fans_num = user['followers_count']

            a_user = UserInfo(user_id=id, user_name=screen_name,
                               follow_num=follow_num, fans_num=fans_num)
            XueqiuSpider.id_queue.append(a_user)

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
            id = user['id']
            screen_name = user['screen_name']
            follow_num = user['friends_count']
            fans_num = user['followers_count']

            a_user = UserInfo(user_id=id, user_name=screen_name,
                              follow_num=follow_num, fans_num=fans_num)
            XueqiuSpider.id_queue.append(a_user)

        if current_page >= page_num:  # 当前用户的所有页面（关注+粉丝）已经收集完毕
            # print(len(XueqiuSpider.id_queue))
            # print("====================over=============")

            # 开始遍历收集的用户
            while XueqiuSpider.id_queue:
                next_user = XueqiuSpider.id_queue.popleft() # 从队列中取出一个用户

                # 将该用户的信息进行保存
                item = XueqiucrawlerItem()
                item['user_id'] = next_user.user_id
                item['user_name'] = next_user.user_name
                item['follow_num'] = next_user.follow_num
                item['fans_num'] = next_user.fans_num
                yield item

                url_str = "https://xueqiu.com/friendships/groups/members.json?uid={user_id}&page=1&gid=0"
                next_url = url_str.format(user_id=next_user.user_id)

                yield scrapy.Request(
                    url=next_url,
                    headers=XueqiuSpider.my_header,
                    callback=self.parse, # 开始收集用户的关注页面
                    meta={'user_id': next_user.user_id} # 用户的id
                )
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

