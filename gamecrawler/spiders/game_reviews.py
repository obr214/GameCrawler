# -*- coding: utf-8 -*-
import re
import scrapy
import itertools
import logging
from unidecode import unidecode
from scrapy.spiders import CrawlSpider
from scrapy.utils.log import configure_logging
from gamecrawler.items import GameReviewItem


class GameReviewsSpider(CrawlSpider):
    name = 'game_reviews'
    allowed_domains = ['metacritic.com']

    def __init__(self):
        CrawlSpider.__init__(self)
        configure_logging({'LOG_FORMAT': '%(asctime)s %(levelname)s: %(message)s',
                           'LOG_FILE': 'logs/game_review_errors.log',
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

        # Gets on the game info page
        link_elements = response.css('.product_condensed > ol > li.product > div > div.product_title > a::attr("href")')
        for href in link_elements:
            game_url = response.urljoin(href.extract())
            #yield self.make_requests_from_url(game_url)
            yield scrapy.Request(game_url, callback=self.parse_review_link)

    def parse_review_link(self, response):
        # Gets the critics reviews
        critics_element = response.xpath('//li[contains(@class, "nav nav_critic_reviews")]')[0]
        critics = critics_element.css('span > span > a::attr("href")')[0].extract()
        critics_url = response.urljoin(critics)
        request = scrapy.Request(critics_url, callback=self.parse_reviews)
        request.meta['review_type'] = 'critic'
        yield request

        # Gets the user reviews
        users_element = response.xpath('//li[contains(@class, "nav nav_user_reviews")]')[0]
        users = users_element.css('span > span > a::attr("href")')[0].extract()
        users_url = response.urljoin(users)
        request = scrapy.Request(users_url, callback=self.parse_reviews)
        request.meta['review_type'] = 'user'
        yield request

    def parse_reviews(self, response):

        review_type = response.meta['review_type']

        reviews_container = response.xpath('//div[contains(@class, "body product_reviews")]')
        review_contents_elements = reviews_container.css('div.review_content')

        if review_contents_elements:
            for review_critic in review_contents_elements:

                game_review_obj = GameReviewItem()

                # Gets the title with hyphens
                url = response.css('.product_title > a')[0]
                title_safe = url.css('a::attr("href")').extract()[0].split('/')[-1]
                game_review_obj['title_safe'] = str(title_safe).strip()

                # Gets the title
                title = url.css('a::text')[0].extract()
                title = str(title).strip()
                game_review_obj['title'] = str(title).strip()

                # Gets the platform
                platform_element = response.css('.platform > a::attr("href")')[0]
                platform = platform_element.extract().split('/')[-1]
                game_review_obj['platform'] = str(platform).strip()

                game_review_obj['score'] = review_critic.css('div.review_grade > div::text')[0].extract()

                game_review_obj['reviewer_type'] = review_type
                game_review_obj['review_date'] = review_critic.css('div.review_critic > div.date::text')[0].extract()

                if review_type == 'critic':
                    # Gets the name of the critic
                    review_critic_element = review_critic.css('div.review_critic > div.source')[0]

                    reviewer = review_critic_element.css('a::text')
                    if reviewer:
                        game_review_obj['reviewer'] = str(reviewer[0].extract()).strip()
                    else:
                        game_review_obj['reviewer'] = str(reviewer.extract()).strip()

                    # Gets the summary
                    try:
                        review_summary = review_critic.css('div.review_body::text')[0].extract()
                        game_review_obj['review'] = str(unidecode(review_summary)).strip()
                    except IndexError:
                        game_review_obj['review'] = ''

                    # Gets the url with the complete review
                    try:
                        review_url = review_critic.css('ul.review_actions > li.full_review > a::attr("href")')[0]
                        review_url_str = str(review_url.extract()).strip()
                        game_review_obj['review_url'] = review_url_str
                    except IndexError:
                        game_review_obj['review_url'] = ''
                        # TODO: Change to Logging
                        print "Critic URL Not Available for:", title
                else:
                    # Gets the name of the user
                    game_review_obj['reviewer'] = review_critic.css('div.review_critic > div.name > a::text')[
                        0].extract()

                    # Gets the summary
                    try:
                        review_element = review_critic.css('div.review_body')[0]
                        review_element_expanded = \
                            review_element.xpath('.//span[contains(@class, "blurb blurb_expanded")]')

                        if review_element_expanded:
                            review_text_parts = review_element_expanded[0].css('span::text')
                            pre_review_str = ''
                            for rev_part in review_text_parts:
                                pre_review_str += rev_part.extract()
                            # Substitudes the /r for empty spaces
                            pre_review_str = re.sub(r"(\r)+", " ", pre_review_str)
                            review_str = str(unidecode(pre_review_str)).strip()
                            game_review_obj['review'] = review_str
                        else:
                            review_str = review_element.css('span::text')[0].extract()
                            review_str = str(unidecode(review_str)).strip()
                            game_review_obj['review'] = review_str
                    except IndexError:
                        game_review_obj['review'] = ''

                    # There is no URL for user reviews
                    game_review_obj['review_url'] = ''

                yield game_review_obj
