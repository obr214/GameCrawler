# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class GamecrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    title_safe = scrapy.Field()
    platform = scrapy.Field()
    publisher = scrapy.Field()
    developer = scrapy.Field()
    release_date = scrapy.Field()
    score_metacritic = scrapy.Field()
    score_users = scrapy.Field()
    summary = scrapy.Field()
    rating = scrapy.Field()
    genres = scrapy.Field()


class GameReviewItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    title_safe = scrapy.Field()
    platform = scrapy.Field()
    reviewer = scrapy.Field()
    reviewer_type = scrapy.Field()
    score = scrapy.Field()
    review_date = scrapy.Field()
    review = scrapy.Field()
    review_url = scrapy.Field()

