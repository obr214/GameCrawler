# -*- coding: utf-8 -*-
import scrapy
import itertools
import logging
from scrapy.spiders import CrawlSpider
from unidecode import unidecode
from gamecrawler.items import GamecrawlerItem
from scrapy.utils.log import configure_logging


class GameInfoSpider(CrawlSpider):
    name = 'game_info'
    allowed_domains = ['metacritic.com']

    def __init__(self):
        CrawlSpider.__init__(self)
        configure_logging({'LOG_FORMAT': '%(asctime)s %(levelname)s: %(message)s',
                           'LOG_FILE': 'logs/game_info_errors.log',
                           'LOG_LEVEL': logging.ERROR})

    def start_requests(self):
        base_url = 'http://www.metacritic.com/browse/games/title/'
        consoles = ['ps4', 'xboxone', 'ps3', 'xbox360', 'pc', 'wii-u', '3ds', 'vita']
        alph_links = list('abcdefghijklmnopqrstuvwxyz')

        console_base_urls = [base_url + console + '/' for console in consoles]
        alph_console_links = [a[0] + a[1] for a in itertools.product(console_base_urls, alph_links)]

        starting_urls = console_base_urls + alph_console_links
        starting_urls = sorted(starting_urls)

        for url in starting_urls:
            yield scrapy.Request(url, self.parse)

    def parse(self, response):
        # Gets the pages
        next_page = response.css('div.page_flipper > span.next > a::attr("href")')
        for page in next_page:
            url = response.urljoin(page.extract())
            yield self.make_requests_from_url(url)

        link_elements = response.css('.product_condensed > ol > li.product > div > div.product_title > a::attr("href")')
        for href in link_elements:
            game_url = response.urljoin(href.extract())
            yield scrapy.Request(game_url, callback=self.parse_game_info)

    def parse_game_info(self, response):

        game_info_obj = GamecrawlerItem()

        # Gets the title with hyphens
        url = response.css('.product_title > a')[0]
        title_safe = url.css('a::attr("href")').extract()[0].split('/')[-1]
        game_info_obj['title_safe'] = str(title_safe).strip()

        # Gets the exact name
        title = url.css('span::text').extract()[0]
        title = str(title).strip()
        game_info_obj['title'] = str(title).strip()

        # Gets the Platforms
        platform_element = response.css('.platform > a::attr("href")')[0]
        platform = platform_element.extract().split('/')[-1]
        game_info_obj['platform'] = str(platform).strip()

        # Get data summary element
        data_summary_element = response.css('.product_data')[0]

        # Get the Publishers
        publisher_element = data_summary_element.css('ul > li.publisher > span.data > a > span::text')
        publishers_list = [str(publisher.extract()).strip() for publisher in publisher_element]
        publishers_str = '|'.join(publishers_list)
        game_info_obj['publisher'] = publishers_str

        # Release Date
        release_date_element = data_summary_element.css('ul > li.release_data > span.data::text')[0]
        release_date = str(release_date_element.extract()).strip()
        game_info_obj['release_date'] = release_date

        # Get the scores
        try:
            score_meta_element = response.xpath('//div[contains(@class, "metascore_w xlarge game")]')[0]
            score_meta = str(score_meta_element.css('span::text')[0].extract()).strip()
            game_info_obj['score_metacritic'] = score_meta
        except IndexError:
            game_info_obj['score_metacritic'] = 'tbd'

        try:
            score_users_element = response.xpath('//div[contains(@class, "metascore_w user large game")]')[0]
            score_users = str(score_users_element.css('div::text')[0].extract()).strip()
            game_info_obj['score_users'] = score_users
        except IndexError:
            game_info_obj['score_users'] = 'tbd'

        # Get the summary
        try:
            summary_element = response.xpath('//span[contains(@class, "blurb blurb_expanded")]')
            if summary_element:
                summary_str = summary_element[0].css('span::text')[0].extract()
                summary_str = str(unidecode(summary_str)).strip()
                game_info_obj['summary'] = summary_str
            else:
                summary_str = response.css('ul.summary_details > li > span.data > span::text')[0].extract()
                summary_str = str(unidecode(summary_str)).strip()
                game_info_obj['summary'] = summary_str
        except IndexError:
            game_info_obj['summary'] = ''

        # Gets the developer
        try:
            developer_element = response.xpath('//li[contains(@class, "summary_detail developer")]')[0]
            developers = str(developer_element.css('span.data::text')[0].extract()).strip()

            developers_list = developers.split(',')
            developers_list = [dev.strip() for dev in developers_list]
            game_info_obj['developer'] = '|'.join(developers_list)
        except IndexError:
            game_info_obj['developer'] = ''

        # Gets the rating
        try:
            rating_element = response.xpath('//li[contains(@class, "summary_detail product_rating")]')[0]
            game_info_obj['rating'] = str(rating_element.css('span.data::text')[0].extract()).strip()
        except IndexError:
            game_info_obj['rating'] = ''

        # Gets the genres
        try:
            genres_element = response.xpath('//li[contains(@class, "summary_detail product_genre")]')[0]
            genres = str(genres_element.css('span.data::text')[0].extract()).strip()

            genres_list = genres.split(',')
            genres_list = [gen.strip() for gen in genres_list]
            game_info_obj['genres'] = '|'.join(genres_list)
        except IndexError:
            game_info_obj['genres'] = ''

        yield game_info_obj
