from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from ebay_scraper.spiders.shop_spider import ShopSpider

def run_spider():
    # Create a CrawlerProcess
    process = CrawlerProcess(get_project_settings())

    # Add your spider to the process
    process.crawl(ShopSpider)

    # Start the crawling process
    process.start()

if __name__ == "__main__":
    run_spider()