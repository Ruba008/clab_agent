from collections.abc import AsyncIterator
from typing import Any, AsyncIterator, List
import scrapy
from scrapy.http import Response, Request
import db as db
import re
import os, hashlib
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

class ClabDoc(scrapy.Spider):
    name = "clabdoc"
    
    list_url: List[str] = []
    
    # Define the allowed URL patterns
    ALLOWED_PATTERNS = [
        r'^https://containerlab\.dev/manual/kinds/.*',
        r'^https://containerlab\.dev/manual/nodes/$',
        r'^https://containerlab\.dev/manual/topo-def-file/$',
        r'^https://containerlab\.dev/manual/network/$'
    ]
    
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.raw_docs: list[Document] = []
        self.list_url: list[str] = []
        self._finalized: bool = False
        self.processed_urls: set = set()  # Track processed URLs to avoid duplicates
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    def is_allowed_url(self, url: str) -> bool:
        """Check if URL matches any of the allowed patterns"""
        for pattern in self.ALLOWED_PATTERNS:
            if re.match(pattern, url):
                return True
        return False
    
    async def start(self) -> AsyncIterator[Any]:
        # Start with the main pages we want to scrape
        start_urls = [
            'https://containerlab.dev/manual/kinds/',
            'https://containerlab.dev/manual/nodes/',
            'https://containerlab.dev/manual/topo-def-file/',
            'https://containerlab.dev/manual/network/'
        ]
        
        for url in start_urls:
            yield Request(url=url, callback=self.parse_doc, meta={"playwright": True})
    
    def extract_urls_from_navigation(self, response: Response) -> List[str]:
        """Extract URLs from navigation that match our allowed patterns"""
        urls = []
        
        # Get all navigation links
        nav_links = response.xpath('//nav//a/@href').getall()
        
        for href in nav_links:
            # Convert relative URLs to absolute
            if href.startswith('../'):
                absolute_url = href.replace('../', 'https://containerlab.dev/manual/')
            elif href.startswith('./'):
                absolute_url = href.replace('./', response.url if response.url.endswith('/') else response.url + '/')
            elif href.startswith('/'):
                absolute_url = 'https://containerlab.dev' + href
            elif href.startswith('http'):
                absolute_url = href
            else:
                # Relative to current directory
                base_url = response.url.rstrip('/') + '/'
                absolute_url = base_url + href
            
            # Remove fragments and query parameters
            absolute_url = absolute_url.split('#')[0].split('?')[0]
            
            # Ensure URL ends with / for directory URLs
            if not absolute_url.endswith('/') and not absolute_url.split('/')[-1].count('.'):
                absolute_url += '/'
            
            # Check if URL matches our patterns
            if self.is_allowed_url(absolute_url) and absolute_url not in self.processed_urls:
                urls.append(absolute_url)
                self.logger.info(f"Found matching URL: {absolute_url}")
        
        return urls
        
    def parse_doc(self, response: Response, **kwargs: Any):
        # Mark this URL as processed
        self.processed_urls.add(response.url)
        
        article = response.xpath('//article/*')
        
        page_content: str
        
        page_content = "url: " + response.url + "\n"
        
        for index, element in enumerate(article):
            tag = element.xpath('name()').get()
            codes = element.xpath('.//code[@class="md-code__content"]')

            text_code = ["\nCode (YAML ou SQL ou CLI)\n"]
            
            if (codes):
                spans = codes.xpath('./span')
                
                for span in spans:
                    text_code = text_code + ["\n"] + span.xpath("./span/text()").getall() if len(text_code) != 0 else span.xpath("./span/text()").getall()
                
                if not "".join(text_code).strip() == "Code (YAML ou SQL ou CLI)":
                    page_content = page_content + "".join(text_code) + "\n\n"
            
            if (tag == "h1"):
                title = element.xpath('text()').get()
                page_content = page_content + "# " + str(title) + "\n\n"
            
            if (tag == "h2"):
                subtitle = element.xpath('text()').get()
                page_content = page_content + "## " + str(subtitle) + "\n\n"
            
            if (tag == "h3"): 
                subtitle = element.xpath('text()').get()
                page_content = page_content + "### " + str(subtitle) + "\n\n"
                
            if (tag == "h4"): 
                subtitle = element.xpath('text()').get()
                page_content = page_content + "#### " + str(subtitle) + "\n\n"
                
            if (tag == "p"): 
                p_content = element.get()
                
                if p_content:
                    p_content = re.sub(r'^<p[^>]*>|</p>$', '', p_content.strip())
                    p_content = re.sub(r'<code[^>]*>|</code>', '', p_content)
                    p_content = re.sub(r'<a[^>]*>|</a>', '', p_content)
                    
                    p_content = ' '.join(p_content.split())
                    
                    page_content = page_content + str(p_content) + "\n\n"

        # Extract URLs from this page that match our patterns
        new_urls = self.extract_urls_from_navigation(response)
        
        # Add new URLs to our list (avoiding duplicates)
        for url in new_urls:
            if url not in self.list_url and url not in self.processed_urls:
                self.list_url.append(url)
        
        page_content_filtred = page_content.replace('"', "'")
        
        doc = Document(page_content=page_content_filtred, metadata={"url": response.url})
        self.raw_docs.append(doc)
        
        self.logger.info(f"☑️ {response.url} recorded! ({len(self.raw_docs)} docs so far)")
        
        # Process next URL from our filtered list
        if self.list_url:
            next_url = self.list_url.pop(0)
            self.logger.info(f"Next URL to process: {next_url}")
            yield Request(url=next_url, callback=self.parse_doc, meta={"playwright": True})
            
    def _finalize(self):
        if self._finalized:
            return
        self._finalized = True

        self.logger.info(f"Finalizing with {len(self.raw_docs)} documents")

        if not self.raw_docs:
            self.logger.warning("No documents were scraped!")
            return

        # Log dos documentos antes do chunking
        total_chars = sum(len(doc.page_content) for doc in self.raw_docs)
        self.logger.info(f"Total characters in documents: {total_chars}")

        try:
            self.logger.info("Starting semantic chunking...")
            splitter = SemanticChunker(
                embeddings=self.embeddings,
                breakpoint_threshold_type="percentile",
                buffer_size=1
            )
            
            chunks = splitter.split_documents(self.raw_docs)
            self.logger.info(f"✅ Chunking completed! Original docs: {len(self.raw_docs)} -> Chunks: {len(chunks)}")
            
            # Log algumas estatísticas dos chunks
            if chunks:
                chunk_sizes = [len(chunk.page_content) for chunk in chunks]
                avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes)
                self.logger.info(f"Average chunk size: {avg_chunk_size:.0f} characters")
                self.logger.info(f"Chunk size range: {min(chunk_sizes)} - {max(chunk_sizes)} characters")
                
            # Mostrar exemplo de chunk
            if chunks:
                self.logger.info(f"Sample chunk preview: {chunks[0].page_content[:200]}...")

        except Exception as e:
            self.logger.error(f"❌ Error during chunking: {e}")
            # Fallback: usar documentos originais sem chunking
            chunks = self.raw_docs
            self.logger.info(f"Using original documents as fallback: {len(chunks)} docs")

        ids = []
        for i, d in enumerate(chunks):
            d.metadata["chunk"] = i
            key = (d.metadata.get("url", "") + "|" + str(i) + "|" + d.page_content[:200]).encode("utf-8")
            ids.append(hashlib.sha1(key).hexdigest())

        self.logger.info(f"Split into {len(chunks)} chunks, adding to database...")

        try:
            db.add_scrapy(document=chunks, embeddings=self.embeddings, ids=ids)
            self.logger.info("✅ Database insertion completed!")
        except Exception as e:
            self.logger.error(f"❌ Error adding to database: {e}")

        self.logger.info("✅ Scraped successfully!")
        self.logger.info(f"Processed URLs: {list(self.processed_urls)}")
    
    def closed(self, reason):
        self._finalize()