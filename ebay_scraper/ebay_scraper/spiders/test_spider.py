import scrapy
import json
import requests
import re
from scrapy.crawler import CrawlerProcess
import math
from urllib.parse import urlencode
import os
import numpy as np

class TestSpider(scrapy.Spider):
    name = 'test_scraper'
    def start_requests(self):
        yield scrapy.Request(url="https://www.ebay.de/sch/i.html?_dkr=1&iconV2Request=true&_blrs=recall_filtering&_ssn=kfz_elektrik&store_name=woospakfzteile&LH_ItemCondition=3&_ipg=240&_oac=1&store_cat=0&_udlo=400&_udhi=450",callback=self.test_scrape)
    
    def test_scrape(self,response):
        with open("test.html","w") as f:
            f.write(response.text)