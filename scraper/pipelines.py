# Import necessary libraries
from scrapy.exceptions import DropItem
from scrapy.exceptions import NotConfigured
import sqlite3
from .items import CategoryItem, ProductItem
import json
from itemadapter import ItemAdapter
import datetime;



# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class DarazscrapingPipeline:
    itemlist = []

    # Initialize the pipeline with the database name and a dictionary to store category IDs
    def __init__(self, db_path):
        self.db_path = db_path
        self.category_ids = {}

    # This method is called by Scrapy to create a pipeline instance
    @classmethod
    def from_crawler(cls, crawler):
        db_path = crawler.settings.get('DB_PATH')
        if not db_path:
            raise NotConfigured('DB_PATH setting is required')
        return cls(db_path)
    
    # This method is called when the spider is opened
    def open_spider(self, spider):
        self.conn = sqlite3.connect(self.db_path)
        self.curr = self.conn.cursor()
        #Create table if not exists
        self.create_table()
        #Open category jsonl file and product jsonl file
        self.categoryfile = open("data/category.jsonl", "a")
        self.productfile = open("data/product.jsonl", "a")

    # This method is called when the spider is closed
    def close_spider(self, spider):
        self.conn.close()
        self.categoryfile.close()
        self.productfile.close()

    # This method creates the necessary tables in the database
    def create_table(self):
        self.curr.execute('''CREATE TABLE IF NOT EXISTS categories_tb(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name text,
        category_url text,
        scraped_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        self.curr.execute('''CREATE TABLE IF NOT EXISTS products_tb(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name text,
                product_price DECIMAL(10, 5),
                product_rating DECIMAL(10, 5),
                total_reviews INTEGER,
                sold_quantity INTEGER,
                product_url text,
                category_name text,
                category_id INTEGER,
                scraped_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(category_id) REFERENCES categories_tb(id)
                )''')
              
    def process_item(self, item, spider):
        if item in self.itemlist:
            raise DropItem("Duplicate Entry")
        if not item['category_name']:
            raise DropItem("Missing category_name in %s" % item)
        self.store_db(item)        
        self.itemlist.append(item)
        dict_item = ItemAdapter(item).asdict()
        # get current time
        now = datetime.datetime.now()
        dict_item['scraped_date'] = str(now)
        line = json.dumps(dict_item) + "\n"
        if (isinstance(item, CategoryItem)):
            self.categoryfile.write(line)
        if (isinstance(item, ProductItem)):
            self.productfile.write(line)
        return item

    # This method stores the item in the database
    def store_db(self,item):
        if (isinstance(item, CategoryItem)):
            self.curr.execute("""INSERT INTO categories_tb (category_name, category_url) VALUES (?,?)""",(
            item['category_name'],
            item['category_url']
        ))
            self.category_ids[item['category_name']] = self.curr.lastrowid
        elif isinstance(item, ProductItem):
            category_id = self.category_ids.get(item['category_name'])
            if category_id is not None:
                self.curr.execute("""INSERT INTO products_tb (product_name, product_price, product_rating, total_reviews, sold_quantity, product_url, category_name, category_id) VALUES (?,?,?,?,?,?,?,?)""",(
                    item['product_name'],
                    item['product_price'],
                    item['product_rating'],
                    item['total_reviews'],
                    item['sold_quantity'],
                    item['product_url'],
                    item['category_name'],
                    category_id
                ))
        self.conn.commit()