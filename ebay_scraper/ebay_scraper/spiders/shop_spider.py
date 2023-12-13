import scrapy
import json
import requests
import re
from scrapy.crawler import CrawlerProcess
import math
from urllib.parse import urlencode
import os
class ShopSpider(scrapy.Spider):
    name = 'shop-scraper'
    # file_path = os.path.abspath("ebay_scraper/spider/spider_config.json")
    # with open(file_path,"r") as f:
    #     shop_url = json.loads(f.read())["shop_url"]
    shop_url = "https://www.ebay.de/sch/i.html?_dkr=1&iconV2Request=true&_blrs=recall_filtering&_ssn=kfz_elektrik&store_name=woospakfzteile&LH_ItemCondition=3&_ipg=240&_oac=1&store_cat=0"
    count_product = 0
    def start_requests(self):
        url = self.shop_url
        yield scrapy.Request(url=url, callback=self.test_fetch)
    
    def test_fetch(self,response):
        print("salam")
        category_urls = response.css("li.srp-refine__category__item>a::attr(href)").extract()
        with open("text.html","w") as f:
                f.write(response.text)
        print("salam "+str(len(category_urls)))
        for url in category_urls:
            yield scrapy.Request(url=url, callback=self.product_count)

    def product_count(self,response):
        # try:
            print("salam")
            digit_pattern = re.compile(r'\d+')
            digit_matches = digit_pattern.findall(response.css("h1.srp-controls__count-heading ::text").extract()[0])
            result = ''.join(digit_matches)
            self.count_product+= int(result)
            with open("text.text","a+") as f:
                 f.write(str(self.count_product))
            with open("text.html","w") as f:
                 f.write(response.text)
        # except:
        #     pass

