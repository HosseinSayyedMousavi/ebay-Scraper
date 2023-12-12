import scrapy
import json
import requests
import re
class EbaySpider(scrapy.Spider):
    name = 'ebay-scraper'
    categories_tree = []
    children_without_child = []


    def start_requests(self):
        url = "https://www.ebay.de/n/all-categories"
        yield scrapy.Request(url=url, callback=self.fetch_mains)


    def fetch_mains(self, response):
        cat_names = response.css("div.cat-container > a.top-cat > h2.ttl::text").extract()
        cat_urls = response.css("div.cat-container > a.top-cat ::attr(href)").extract()

        for url , name in zip(cat_urls , cat_names):
            category = {"parent":"","name":name,"url":url}
            self.categories_tree.append(category)
            yield scrapy.Request(url=url, callback=self.get_children,meta={'category': category})


    def get_children(self,response):
        category = response.meta.get('category')
        first_children_names = response.xpath("//div[@class='dialog__cell']/section[1]/div[@class='b-list__header']/following-sibling::ul/li[not(button)]/a/text()").extract()
        first_children_urls = response.xpath("//div[@class='dialog__cell']/section[1]/div[@class='b-list__header']/following-sibling::ul/li[not(button)]/a/@href").extract()
        for name , url in zip (first_children_names ,first_children_urls):
            self.children_without_child.append({"parent":category["name"] , "url":url,"name":name})
            yield scrapy.Request(url=url, callback=self.scrape_category)
        
        children_urls = response.css("div.dialog__cell > section:nth-child(1) ul.b-accordion-subtree > li:nth-child(1) > a::attr(href)").extract()
        children_names = response.css("div.dialog__cell > section:nth-child(1) ul.b-accordion-subtree > li:nth-child(1) > a::text").extract()
        children_names=[name.replace("Alle Artikel in","").strip() for name in children_names ]
        children_urls = response.css("li[data-state='selected']>ul.srp-refine__category__list>li>a::attr(href)").extract()

        for url , name  in list(zip(children_urls,children_names)):
            
            child_category = {"parent":category["name"],"nam":name,"url":url}
            self.categories_tree.append(child_category)
            yield scrapy.Request(url=url, callback=self.get_grand_children,meta={'category': child_category,'brothers':children_urls})
    

    def get_grand_children(self,response):
        category = response.meta.get('category')
        brothers = response.meta.get('brothers')
        may_child_or_brothers_names = response.xpath("//div[@class='dialog__cell']/section[1]/div[@class='b-list__header']/following-sibling::ul/li/a[@class='b-textlink b-textlink--sibling']/text()").extract()
        child_or_brothers_urls = response.xpath("//div[@class='dialog__cell']/section[1]/div[@class='b-list__header']/following-sibling::ul/li/a[@class='b-textlink b-textlink--sibling']/@href").extract()
        for name , url in zip(may_child_or_brothers_names,child_or_brothers_urls):
            child_category = {"parent":category["name"] , "url":url,"name":name}

            if self.product_count(response) < 10000:
                self.children_without_child.append(child_category)
                yield scrapy.Request(url=url, callback=self.scrape_category)

            elif not self.has_child(url=url,brothers=brothers):
                self.children_without_child.append(child_category)
                yield scrapy.Request(url=url, callback=self.scrape_category)
            
            else:
                yield scrapy.Request(url=url, callback=self.get_grand_children,meta={'category': child_category,'brothers':child_or_brothers_urls})


    def has_child(self,url,brothers):
        request = scrapy.Request(url)
        response = self.crawler.engine.download(request, self)
        child_or_brothers_urls = response.xpath("//div[@class='dialog__cell']/section[1]/div[@class='b-list__header']/following-sibling::ul/li/a[@class='b-textlink b-textlink--sibling']/@href").extract()
        if all(url in brothers for url in child_or_brothers_urls):
            return False
        else:
            return True

    
    def scrape_category(self,response):
        if self.product_count(response) > 10000:
            filters = self.get_filters(response)
        for filter in filters:
            for sub_filter in filter["filter_list"]:
                pass

    def filter_2_params(self,filters):
        params ={}

        for filter in filters:
            params[filter["filter_name"]] =""

            for p in filter["filter_list"]:
                params[filter["filter_name"]] += "|"+ p
            params[filter["filter_name"]] = params[filter["filter_name"]].strip("|")

        return params



    def get_filters(self,response):


        filter_list=[]

        groups = self.refine_end_point(response)["group"]
        for group in groups:

            entries = group["entries"]
            for f in entries:
                data={}
                data["filter_name"] = f["paramKey"]
                data["filter_list"] = []
                for f2 in f["entries"]:
                    data["filter_list"].append(f2["label"]["textSpans"][0]["text"])
                filter_list.append(data)

        return filter_list


    def product_count(self,response):
        digit_pattern = re.compile(r'\d+')
        digit_matches = digit_pattern.findall(response.css("h2.srp-controls__count-heading ::text").extract()[0])
        result = ''.join(digit_matches)
        return int(result)
    
    
    def refine_end_point(self,response):
        headers = {
        'authority': 'www.ebay.de',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,fa;q=0.8',
        'referer': response.url,
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Cookie': response.headers['Set-Cookie'].decode('utf-8'),
        'x-requested-with': 'XMLHttpRequest'
        }
        data=json.loads(response.css("li > button[aria-label='Alle Filter']::attr(data-track)").extract()[0])
        params = {
            "_fsrp":"0",
            "rt":"nc",
            "pageci":data["eventProperty"]["pageci"],
            "modules":"SEARCH_REFINEMENTS_MODEL_V2:Afa",
            "_sacat": re.findall(r'\/(\d+)\/',response.url)[0],
            "no_encode_refine_params":"1",
        }
        r = requests.request("GET",url=re.findall(r'.*\/',response.url)[0],params=params,headers=headers)
        return r.json()