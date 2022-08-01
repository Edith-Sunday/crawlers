import scrapy
from ..helpers import log_error
from ..items import CategoryItem, ProductItem


class Spapart(scrapy.Spider):
    name = "spapartnordic"
    base_url = "https://www.spapartsnordic.se/se-webbutik_med_reservdelar_och_tillbehor_for_spabad_och_pool"

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
    error_log = []

    def start_requests(self):
        yield scrapy.Request(
            url=self.base_url,
            callback=self.parse
        )

    def parse(self, response):
        category_urls = [li.css('a.opensubcatlink').attrib.get('href') for li in response.css("ul#menu li") if li.css('a.opensubcatlink').attrib.get('href')]
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
        if response.css("div.col-xs-12.catdescription.limit h1 strong"):
            category_item['title'] = response.css("div.col-xs-12.catdescription.limit h1 strong::text").get().strip()
        elif response.css("div.row div.col-lg-6.col-sm-12 h1"):
            category_item['title'] = response.css("div.row div.col-lg-6.col-sm-12 h1::text").get().strip()
        else:
            category_item['title'] = response.css("title::text").get().split('-')[0]

        category_item['parent_category_url'] = parent_url
        category_item['breadcrumbs'] = '/'.join([li.css('a::text').get().strip() for li in response.css("ol.breadcrumb li")])
        category_item['child_product_urls'] = []
        category_item['child_category_urls'] = [f"{'https://www.spapartsnordic.se/'}{a.attrib.get('href')}" for a in response.css('div#catdisplayhoriz div.col-xs-12 a')]
        category_item['description_html'] = ''.join([tag.get() for tag in response.css('div.col-xs-12.catdescription *') if not tag.css("img")])

        for link in category_item['child_category_urls']:
            yield scrapy.Request(
                url=link,
                callback=self.parse_category,
                meta={'parent_url': category_item['url']}
            )

        for div in response.css('div#proddisplayhoriz'):
            link = div.css('a.link').attrib.get('href')

            if not link:
                link = div.css('a.thumbnail').attrib.get('href')

            _url = f"{'https://www.spapartsnordic.se/'}{link}"
            category_item['child_product_urls'].append(_url)

            yield scrapy.Request(
                url=_url,
                callback=self.parse_product,
                meta={'parent_url': category_item['url']}
                )

        yield category_item

    def parse_product(self, response):
        parent_url = response.meta.get('parent_url')

        item = ProductItem()
        item['scraper'] = self.name
        item['item_type'] = 'product'
        item['breadcrumbs'] = '/'.join([li.css('a::text').get().strip() for li in response.css("ol.breadcrumb li")])
        item['parent_category_url'] = parent_url
        item['product_type'] = 'SIMPLE'
        item['url'] = response.url
        item['sku'] = response.css("div.row div.col-lg-6.col-sm-12 p span.pull-left small::text").get().replace('Artikelnummer:', '')
        item['title'] = response.css("div.row div.col-lg-6.col-sm-12 h1.h2::text").get()
        item['image_urls'] = [f"{'https://www.spapartsnordic.se/'}{img.attrib.get('src')}" for img in response.css("img.thumbnail.col-lg-12.img-responsive")]

        item['price_currency'] = "SEK"
        item['price_value'] = response.css("div.well h4.h4 span#displayprice::text").get().replace('kr', '')
        if response.css("div.well h4.h4 span.pull-right::text").get():
            item['price_discount_value'] = response.css("div.well h4.h4 span.pull-right::text").get().replace('kr', '')
        item['stock_status_refined'] = "IN_STOCK"

        desc_text = ''
        desc_html = ''

        list1 = [text.strip() for text in response.css("div.row div.col-lg-6.col-sm-12 p::text").getall()]
        list2 = [text.strip() for text in response.css("div.row div.col-lg-6.col-sm-12 ul li::text").getall()]
        description_text = list1 + list2

        list3 = [text.strip() for text in response.css("div.row div.col-lg-6.col-sm-12 p").getall()]
        list4 = [text.strip() for text in response.css("div.row div.col-lg-6.col-sm-12 ul li").getall()]
        description_html = list3 + list4

        desc_text += ''.join(description_text).strip()
        desc_html += ''.join(description_html).strip()

        item['product_descriptions'] = {
            'SV': {
                'Product Description': {
                    'text': desc_text,
                    'html': desc_html
                }
            }
        }

        item['related_products'] = []

        for a in response.css("div.caption a"):
            if not a.attrib.get('type'):
                _rel_prod_url = f"https://www.spapartsnordic.se/{a.attrib.get('href')}"
                item['related_products'].append({
                    'relation': 'RELATED_PRODUCT',
                    'url': _rel_prod_url
                })

        item['attributes'] = {}
        yield item
