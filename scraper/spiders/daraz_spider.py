# Import the necessary libraries
import scrapy
from scrapy_playwright.page import PageMethod
from urllib.parse import urlparse, urlunparse
from scrapy.utils.project import get_project_settings
from ..items import CategoryItem
from ..items import ProductItem
import re

# Function to abort requests for images to optimize scraping speed
def should_abort_request(request):
     if request.resource_type == "image":
          return True
     return False

# Function to remove query parameters from a URL
def remove_query_params(url):
    parsed_url = urlparse(url)
    return urlunparse(parsed_url._replace(query=""))

# Define JavaScript scripts for scrolling down the page in category and product pages
scrolling_script_category = """
// Scroll down the page 8 times
let scrollCount = 0;
const scrolls = 8;
// Scroll down and then wait for 0.5s
const scrollInterval = setInterval(() => {
  window.scrollTo(0, document.body.scrollHeight);
  scrollCount++;
  if (scrollCount === scrolls) {
    clearInterval(scrollInterval);
  }
}, 500);
    """
scrolling_script_product = """
// Scroll down the page 5 times
let scrollCount = 0;
const scrolls = 5;
// Scroll down and then wait for 0.6s
const scrollInterval = setInterval(() => {
  window.scrollTo(0, document.body.scrollHeight);
  scrollCount++;
  if (scrollCount === scrolls) {
    clearInterval(scrollInterval);
  }
}, 600);
    """

# Define the spider class
class DarazSpider(scrapy.Spider):

    #Define name of spider
    name = "daraz_spider"

    # Define custom settings for the spider
    custom_settings = {
         'PLAYWRIGHT_ABORT_REQUEST': should_abort_request
    }
   
    # Get the URL to start scraping from
    def __init__(self, *args, **kwargs):
        super(DarazSpider, self).__init__(*args, **kwargs)
        settings = get_project_settings()
        self.website_url = settings.get('WEBSITE_URL')

    # Initialize request to scrape the subcategories under wines beers and spirits and their url
    def start_requests(self):
            yield scrapy.Request(self.website_url,self.parse_category,meta=dict(playwright = True,playwright_include_page = True,
            playwright_page_coroutines = [
                PageMethod("evaluate",scrolling_script_category),
                PageMethod("wait_for_timeout", 10000),
                PageMethod('wait_for_selector','#lzd-site-menu-third-layer-heading'),
            ]))
    
    # Define the parse method that will be called to process the response of category request
    async def parse_category(self, response):
        # Select the sub-categories under groceries & pets from the response
        categories_selector = response.css("ul[data-spm='cate_8']")
        #Loop through sub-categories
        for category in categories_selector:
            # Select the sub-categories under wines,beer and spirits from the response
            sub_category_elements = category.css("li[data-cate='cate_8_7']")
            child_categories = sub_category_elements.css("li.lzd-site-menu-grand-item")
            #Loop through child-categories
            for child_category in child_categories:
                #Initialize empty category item
                category_item = CategoryItem()
                # Extract the child-category details
                category_url = child_category.css("a::attr('href')").extract()
                category_name = child_category.css("span::Text").extract()
                initial_category_url = "https:"+category_url[0]+"?page=1"
                # Store the extracted data in the category item
                category_item['category_name'] = category_name[0].strip()
                category_item['category_url'] = "https:"+category_url[0]
                # Yield the category item and a new request to parse the category
                yield category_item
                #Go through every category page to scrape their product
                yield scrapy.Request(initial_category_url,self.parse_product,
                    cb_kwargs={"category_name": category_name,'page_number':1},
                    meta=dict(playwright = True,playwright_include_page = True,
                    playwright_page_coroutines = [
                    PageMethod("evaluate",scrolling_script_product),
                    PageMethod('wait_for_selector','div.gridItem--Yd0sa'),
                    ]))

    # Define the method to parse a product    
    async def parse_product(self, response,category_name,page_number):
        page = response.meta["playwright_page"]
        # Select the products from the response
        products_selector = response.css("div.gridItem--Yd0sa")
        #Loop through products in current page
        for product in products_selector:
            #Initialize empty product item
            product_item = ProductItem()
            # Extract the product details
            product_name = product.css("div#id-title::Text").extract()
            product_price = product.css("span.currency--GVKjl::Text").extract()
            product_rating = product.css(".ratig-num--KNake::Text").extract()
            total_reviews = product.css(".rating__review--ygkUy::Text").extract()
            sold_quantity = product.css("div.split--cTjJp + div::text").get()
            product_url = product.css("a.product-card--vHfY9::attr('href')").extract()
            # Store the extracted data in the product item
            product_item['product_name'] = product_name[0].strip()
            # Convert the string to number before storing the price
            product_item['product_price'] =  float(re.sub(r'[^0-9.]', '',product_price[0].strip()))
            product_item['product_rating'] = float(product_rating[0].split("/")[0]) if product_rating is not None and len(product_rating) > 0 else None
            product_item['total_reviews'] = int(total_reviews[0].strip("()")) if total_reviews is not None and len(total_reviews) > 0 else None
            product_item['sold_quantity'] = int(sold_quantity[0]) if sold_quantity is not None and len(sold_quantity) > 0 else None
            product_item['product_url'] = "https:" + product_url[0]
            product_item['category_name'] = category_name[0].strip()
            # Yield the product item
            yield product_item
            # Close the page if it's not the first or second page to save resources
            if page_number != 1 and page_number != 2:
                await page.close()
        # Check if this is last page
        next_page = response.css('div.title--sUZjQ').get()
        if  next_page is None:
            # If this isn't a last page, increase the page number
            page_number += 1
            # Remove query parameters from the previous URL
            previous_url = remove_query_params(response.url)
            # Build the URL for the next page
            next_page_url = previous_url+"?page="+str(page_number)
            # Yield a new request to scrape the next page
            yield response.follow(next_page_url,
                callback = self.parse_product,cb_kwargs={"category_name": category_name,'page_number':page_number},
                meta=dict(playwright = True,playwright_include_page = True,
                playwright_page_coroutines = [
                PageMethod("evaluate",scrolling_script_product),
                PageMethod('wait_for_selector','div.gridItem--Yd0sa'),
                ]))






           
