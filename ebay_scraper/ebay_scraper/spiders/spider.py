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
            yield scrapy.Request(url=url, callback=self.get_grand_children,meta={'category': child_category})
    

    def get_grand_children(self,response):
        category = response.meta.get('category')
        paramValue = re.findall(r'\/(\d+)\/',response.url)[0]
        param_url = re.findall(r'(.*\/)\d+',response.url)[0]
        refine = self.refine_end_point(response)
        group_category = {}
        for group in refine["group"]:
            if group["fieldId"] == "category":
                group_category = group
                break
        has_child = True
        if len(group_category["entries"]) == 1:
            has_child = False
        if has_child:
            children_names = [entry["label"]["textSpans"][0]["text"] for entry in group_category["entries"] if entry["paramValue"]!=paramValue ]
            children_urls = [ param_url + entry["paramValue"] for entry in group_category["entries"] if entry["paramValue"]!=paramValue ]

        for name , url in zip(children_names,children_urls):
            child_category = {"parent":category["name"] , "url":url,"name":name}

            if self.product_count(response) < 10000:
                self.children_without_child.append(child_category)
                yield scrapy.Request(url=url, callback=self.scrape_category)

            elif not has_child:
                self.children_without_child.append(child_category)
                yield scrapy.Request(url=url, callback=self.scrape_category)
            
            else:
                yield scrapy.Request(url=url, callback=self.get_grand_children,meta={'category': child_category})


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
        aspect_group = {}
        for group in groups:
            if group["fieldId"] == "aspectlist":
                aspect_group = group
                break
        for entry in aspect_group["entries"]:
                data={}
                data["filter_name"] = entry["paramKey"]
                data["filter_list"] = []
                for entry2 in entry["entries"]:
                    data["filter_list"].append(entry2["paramValue"])
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