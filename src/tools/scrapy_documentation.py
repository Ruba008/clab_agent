from collections.abc import AsyncIterator
from typing import Any, AsyncIterator, List
import scrapy
from scrapy.http import Response, Request
import tools.db as db

class ClabDoc(scrapy.Spider):
    name = "clabdoc"
    
    list_url: List[str] = []
    
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": False 
        }
    }
    
    async def start(self) -> AsyncIterator[Any]:
        url = 'https://containerlab.dev/manual/topo-def-file'
        yield Request(url=url, callback=self.parse_doc, meta={"playwright": True})
        
    def parse_doc(self, response: Response, **kwargs: Any):
        article = response.xpath('//article/*')
        
        page_content: str
        
        page_content = "url: " + response.url + "\n"
        
        for index, element in enumerate(article):
            tag = element.xpath('name()').get()
            codes = element.xpath('.//code[@class="md-code__content"]')

            text_code = []
            
            if (codes):
                spans = codes.xpath('./span')
                
                for span in spans:
                    text_code = text_code + ["\n                            "] + span.xpath("./span/text()").getall() if len(text_code) != 0 else span.xpath("./span/text()").getall()
                
                page_content = page_content + "                         -> Code:\n                              " + "".join(text_code) + "\n"
            
            if (tag == "h1"):
                title = element.xpath('text()').get()
                
                page_content = page_content + "-> Title: " + str(title) + "\n"
            
            if (tag == "h2"):
                subtitle = element.xpath('text()').get()
                
                page_content = page_content + " -> Subtitle: " + str(subtitle) + "\n"
            
            if (tag == "h3"): 
                subtitle = element.xpath('text()').get()
                
                page_content = page_content + "     -> Subtitle: " + str(subtitle) + "\n"
            
            if (tag == "h4"): 
                subtitle = element.xpath('text()').get()
                
                page_content = page_content + "         -> Subtitle: " + str(subtitle) + "\n"
            
            if (tag == "h5"): 
                subtitle = element.xpath('text()').get()
                
                page_content = page_content + "             -> Subtitle: " + str(subtitle) + "\n"
            
            if (tag == "h6"): 
                subtitle = element.xpath('text()').get()
                
                page_content = page_content + "                 -> Subtitle: " + str(subtitle) + "\n"
                
            if (tag == "p"): 
                subtitle = element.xpath('text()').get()
                
                page_content = page_content + "                     -> Explain: " + str(subtitle) + "\n"

        if len(self.list_url) == 0:
            
            urls = response.xpath('/html/body/div[3]/main/div/div[1]/div/div/nav/ul/li[5]/nav/ul/li[contains(@class, "md-nav__item")]//a[not(contains(@href, "#"))]')
            for url in urls:
                self.list_url = self.list_url + list(map(
                    lambda url: "https://containerlab.dev/manual/" + url.replace('../', "") if url != './' else "https://containerlab.dev/manual/topo-def-file/"
                    , url.xpath('./@href').getall()
                ))
        
        
        yield page_content
        
        db.connect_collection(session_id=None ,collection_type="scrapy")
        
        db.add_context(url=response.url, response=page_content, collection_type="scrapy", session_id=None, user_input=None)
        
        
        if len(self.list_url) != 0: 
            self.list_url.pop(0)
            yield Request(url=self.list_url[0], callback=self.parse_doc, meta={"playwright": True})
        