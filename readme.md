# 雪球网用户信息爬虫

## 部署信息

1. 爬虫框架：scrapy
2. 爬虫拓展模块（实现分布式）：scrapy-redis
3. 数据库：redis, mongodb
4. python 2.7

## 功能介绍

该爬虫可以爬取雪球网的所有用户信息，包括用户id，用户名，用户的关注数，用户的粉丝数。

## 特色

基于redis数据库实现了bloom filter功能，在进行url过滤的同时节省了内存的开销。并且在pipeline中增加了item去重功能。该爬虫支持分布式爬取，可以加速爬取速度。同时该爬虫具备断点续爬功能！！！