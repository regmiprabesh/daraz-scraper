# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DarazscrapingItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

# Define a class for category items that inherits from the base item
class CategoryItem(scrapy.Item):
    # Each category has an id, name, and URL
    id = scrapy.Field()
    category_name = scrapy.Field()
    category_url = scrapy.Field()
    scraped_date = scrapy.Field()
# Define a class for product items that inherits from the base item
class ProductItem(scrapy.Item):
    # Each product has an id, name, URL, price,rating, reviews count, sold quantity, category name, and category id
    id = scrapy.Field()
    product_name = scrapy.Field()
    product_price = scrapy.Field()
    product_rating = scrapy.Field()
    total_reviews = scrapy.Field()
    sold_quantity = scrapy.Field()
    product_url = scrapy.Field()
    category_name = scrapy.Field()
    category_id = scrapy.Field()
    scraped_date = scrapy.Field()