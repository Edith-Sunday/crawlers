import scrapy
import re
from ..helpers import *
from ..items import CategoryItem, ProductItem


class Spa(scrapy.Spider):
    name = "trial"
    base_url = "https://store.spaservice.se/sv/"

    no_of_requests = 0
    custom_delay_rules = {
        # Example: After 500 requests, do a paus for 180 seconds and so forth
        # 500: 180,
        # 200: 90,
        50: 30,
        # 20: 10,
        5: 1,
    }

    log_error = log_error

    def start_requests(self):
        yield scrapy.Request(
            url=self.base_url,
            callback=self.parse
        )

    def parse(self, response):
        category_urls =  [a.attrib.get('href') for a in response.css("ul.nav.nav-stacked.nav-pills li a")]
        for url in category_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_category
            )   

    def parse_category(self, response):
        category_item = CategoryItem()
        parent_url = response.meta.get('parent_url')

        category_item['scraper'] = self.name
        category_item['item_type'] = 'category'
        category_item['url'] = response.url
        category_item['title'] = response.css("h1.title::text").get().strip()
        category_item['parent_category_url'] = parent_url
        category_item['breadcrumbs'] = response.url.replace(self.base_url, '')
        category_item['child_product_urls'] = []
        category_item['child_category_urls'] = [a.attrib.get('href') for a in response.css("div.category.hover-light a.link")]
        category_item['description_html'] = []
        
        if response.css("div#box-category.box div div p"):
            category_item['description_html'] = response.css("div#box-category.box div div p").get()
            
        if response.css("div#box-category.box"):
            category_item['description_html'] = response.css("div#box-category.box").get()
               

        for div in response.css('div.product.product-column.hover-light'):
            link = div.css('a.link').attrib.get('href')
            category_item['child_product_urls'].append(link)
            yield scrapy.Request(
                url=link,
                callback=self.parse_product,
                meta={'parent_url': category_item['url']}
            )

        for link in category_item['child_category_urls']:
            yield scrapy.Request(
                url=link,
                callback=self.parse_category,
                meta={'parent_url': category_item['url']}
            )
        yield category_item

    def parse_product(self, response):
        
        parent_url = response.meta.get('parent_url')

        item = ProductItem()
        item['scraper'] = self.name
        item['item_type'] = 'product'
        item['breadcrumbs'] = response.url.replace(self.base_url, '')
        item['parent_category_url'] = parent_url
        item['product_type'] = 'SIMPLE'
        item['url'] = response.url
        item['sku'] =  response.css("div.sku span.value::text").get()
        item['title'] =  response.css("div div h1.title::text").get()
        item['image_urls'] = [img.attrib.get('src') for img in response.css("div.image-wrapper a img.img-responsive")]
        item['price_currency'] = "SEK"
        
        item['price_value'] = []
        item['stock_status_refined'] = "DISCONTINUED"

        if response.css("div.price-wrapper span.price"):
            item['price_value'] =  response.css("div.price-wrapper span.price::text").get().replace('kr', "")

        if response.css("div.stock-status div.stock-partly-available"):
             item['stock_status_refined'] = 'BACKORDER'
        if response.css("div.stock-status div.stock-available"):
             item['stock_status_refined'] = 'IN_STOCK'


        attributes = {}
        for table in response.css("div.technical-data table.table.table-striped"):
            table_key = table.css("thead tr th::text").get()
            temp_attr = {}
        
            for tr in  response.css("div.technical-data table.table.table-striped tbody tr"):
                try:
                    key = tr.css("td")[0].css('::text').get()
                    value = tr.css("td")[1].css('::text').get()
                    temp_attr.update({key: value})
                except Exception as e:
                    print(e)
            attributes.update({table_key: temp_attr})

        item['attributes'] = attributes



        item['related_products'] = []

        for div in response.css("div.col-xs-6.col-sm-4.col-md-3"):
            item['related_products'].append({
                'relation': 'RELATED_PRODUCT',
                'sku': div.css('div.gtin span.value::text').get()
            })

        desc_text = ''
        desc_html = ''

        if response.css('div#description'):
            desc_text +=  ''.join([text.strip() for text in response.css("div#description::text").getall()])
            desc_html +=  ''.join( response.css("div#description").getall())

        # if response.css("div#description.tab-pane p"):
        #     desc_text +=  ''.join([text.strip() for text in response.css("div#description.tab-pane p::text").getall()])
        #     desc_html += ''.join(response.css("div#description.tab-pane p").getall())

        item['product_descriptions'] = {
            'SV': {
                'Product Description': {
                    'text': desc_text,
                    'html': desc_html
                }
            }
        }
        yield item