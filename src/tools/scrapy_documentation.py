from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider

class ClabSpider(CrawlSpider):
    name = "Clab_doc"
    
    allowed_domains = ["containerlab.dev"]
    start_urls = ["https://containerlab.dev/manual/kinds/"]

    rules = (
        Rule(LinkExtractor(allow=(r"/manual/kinds/[^/]+/$",)),
                callback='parse_kind',
                follow=True),
    )
    
    def parse_kind(self, response):
        kind_name = response.url.rstrip("/").split("/")[-1]
        title = response.css(f"h1#{kind_name}::text").get()
        item = {
            "kind_name": kind_name,
            "title" : title,
            "html": response.text
        }
        
        
        self.logger.info("Item extraído: %r", item)
        yield item         