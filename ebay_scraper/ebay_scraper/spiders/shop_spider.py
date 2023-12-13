import scrapy
import json
import requests
import re
from scrapy.crawler import CrawlerProcess
import math
from urllib.parse import urlencode
import os
import numpy as np
class ShopSpider(scrapy.Spider):
    name = 'shop-scraper'
    file_path = os.path.abspath("ebay_scraper/spiders/spider_config.json")
    with open(file_path,"r") as f:
        shop_url = json.loads(f.read())["shop_url"]


    def start_requests(self):
        shop_url = self.shop_url
        base_range = self.get_base_range()

        for _range in base_range:
            url = shop_url + f"&_udlo={_range[0]}&_udhi={_range[1]}"
            yield scrapy.Request(url=url, callback=self.scrape_all_ranges,meta={"_range":_range})


    def scrape_all_ranges(self,response):
        shop_url = self.shop_url
        _range = response.meta.get("_range")
        if self.product_count(response) < 10000:
            yield scrapy.Request(url=response.url, callback=self.scrape_all_pages)
        else:
            mid_rounded = round(_range[1]/2,2)
            _range_1 = [_range[0],mid_rounded]
            _range_2 = [mid_rounded,_range[1]]

            url = shop_url + f"&_udlo={_range_1[0]}&_udhi={_range_1[1]}"
            yield scrapy.Request(url=url, callback=self.scrape_all_ranges,meta={"_range":_range_1})

            url = shop_url + f"&_udlo={_range_2[0]}&_udhi={_range_2[1]}"
            yield scrapy.Request(url=url, callback=self.scrape_all_ranges,meta={"_range":_range_2})


    def scrape_all_pages(self,response):
        product_count = self.product_count(response)
        number_of_pages = math.ceil(product_count/250)
        for page_num in range(number_of_pages):
            url = response.url+"&_pgn="+str(page_num+1)
            yield scrapy.Request(url=url, callback=self.scrape_page)
    

    def scrape_page(self,response):
        pass
            

    def product_count(self,response):

        digit_pattern = re.compile(r'\d+')
        digit_matches = digit_pattern.findall(response.css("h1.srp-controls__count-heading ::text").extract()[0])
        result = ''.join(digit_matches)
        return int(result)

    
    def get_base_range(self):
        _range = []

        my_range = np.arange(7, 10, 0.5)
        rounded_range = [round(x, 1) for x in my_range]
        _range.extend(rounded_range)

        my_range = np.arange(10, 20, 0.1)
        rounded_range = [round(x, 1) for x in my_range]
        _range.extend(rounded_range)

        my_range = np.arange(20, 30, 0.2)
        rounded_range = [round(x, 1) for x in my_range]
        _range.extend(rounded_range)

        my_range = np.arange(30, 75, 1)
        _range.extend(my_range)

        my_range = np.arange(75, 150, 2)
        _range.extend(my_range)

        my_range = np.arange(150, 200, 4)
        _range.extend(my_range)

        my_range = np.arange(250, 300, 10)
        _range.extend(my_range)

        my_range = np.arange(300, 400, 20)
        _range.extend(my_range)

        return_rang = [ [_range[i],_range[i+1]] for i in range(0,len(_range)-1) ]
        return_rang.extend([[400,460],
                                [460,550],
                                [550,650],
                                [650,1000],
                                [1000,10000]
                                ])

        return return_rang
        
