import scrapy
from ..helpers import *
from ..items import CategoryItem, ProductItem


class Spapart(scrapy.Spider):
    name = "spasupport"
    base_url = "https://www.spasupport.se/"

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
        for _selector in response.css('ul#main-nav li'):
            if _selector.css('a::text').get().strip() in ['Produkter', 'Reservdelar']:
                # categories in selected sections
                _li_categories = _selector.css('ul.sub-menu.tf_scrollbar li[aria-haspopup="true"]')

                for _li in _li_categories:
                    href = _li.css('a').attrib.get('href')  # link of parent category
                    _children_categories = [li.css('a').attrib.get('href') for li in _li.css('ul.sub-menu li')]  # children category links

                    # case where parent url is #, yield only the child categories and save parent url as text
                    if href == '#':
                        for _child_url in _children_categories:
                            yield scrapy.Request(
                                url=_child_url,
                                callback=self.parse_category,
                                meta={
                                    'parent_url': ''.join(_li.css('::text').getall())
                                }
                            )
                    else:
                        yield scrapy.Request(
                            url=href,
                            callback=self.parse_category,
                            meta={
                                'child_category_urls': _children_categories
                            }
                        )

    def parse_category(self, response):
        parent_url = response.meta.get('parent_url')
        child_category_urls = response.meta.get('child_category_urls', [])
        category_item = response.meta.get('category_item')

        # populate category item with response data
        if not category_item:
            category_item = CategoryItem()
            category_item['scraper'] = self.name
            category_item['item_type'] = 'category'
            category_item['url'] = response.url
            category_item['title'] = response.css("div.product-info h1::text").get()
            category_item['image_urls'] = [response.css("div.product-thumbnail img").attrib.get("src")]
            category_item['breadcrumbs'] = '/'.join([a.css('::text').get() for a in response.css('nav.woocommerce-breadcrumb a')])
            category_item['parent_category_url'] = parent_url

            category_item['description_html'] = ' '.join(response.css("div.product-description").getall())
            category_item['child_product_urls'] = []
            category_item['child_category_urls'] = child_category_urls

            # fetch all children category urls from fn parse, store parent url as current page url
            for _child_url in child_category_urls:
                yield scrapy.Request(
                    url=_child_url,
                    callback=self.parse_category,
                    meta={
                        'parent_url': response.url
                    }
                )

        for li in response.css("div#content ul li.themify-category-loop"):
            child_product_url = li.css('a').attrib.get("href")
            category_item['child_product_urls'].append(child_product_url)
            # populate child product fields

        if response.css('a.load-more-button'):
            yield scrapy.Request(
                url=response.css('a.load-more-button').attrib.get('href'),
                callback=self.parse_category,
                meta={
                    'category_item': category_item
                }
            )
        else:
            yield category_item

        for product_url in category_item['child_product_urls']:
            yield scrapy.Request(
                url=product_url,
                callback=self.parse_product,
                meta={'parent_url': response.url}
            )

    def parse_product(self, response):
        parent_url = response.meta.get('parent_url')

        item = ProductItem()
        item['scraper'] = self.name
        item['item_type'] = 'product'
        item['parent_category_url'] = parent_url
        item['product_type'] = 'SIMPLE'
        item['url'] = response.url
        item['sku'] = response.css("div span.sku::text").get().strip()
        item['title'] = response.css("div h1.product_title.entry-title::text").get().strip()
        item['breadcrumbs'] = f"{'/'.join([a.css('::text').get() for a in response.css('nav.woocommerce-breadcrumb a')])}/{item['title']}"

        item['image_urls'] = [a.attrib.get('href') for a in response.css("figure.woocommerce-product-gallery__wrapper div a")]
        item['price_currency'] = 'SEK'

        if response.css("p.price span.woocommerce-Price-amount.amount"):
            item['price_value'] = response.css("p.price span.woocommerce-Price-amount.amount bdi::text").get().strip()
        elif response.css("div.product-description p"):
            item['price_value'] = response.css("div.product-description p strong::text").get().strip().replace('kr', '')
        else:
            pass

        if response.css("p.stock.in-stock"):
            item['stock_status_refined'] = 'IN_STOCK'
        else:
            item['stock_status_refined'] = 'DISCONTINUED'

        desc_text = ''
        desc_html = ''

        list_1 = response.css("div#tab-description h3::text").getall()
        list_2 = response.css("div#tab-description p::text").getall()
        description_text = list_1 + list_2

        list_3 = response.css("div#tab-description h3").getall()
        list_4 = response.css("div#tab-description p").getall()
        description_html = list_3 + list_4

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

        specs = []
        for li in response.css("div.product-description ul li"):
            if li.css('::text').get().strip() in specs:  # dupe filter for specs
                continue
            else:
                specs.append(li.css('::text').get().strip())

        _spec = ', '.join(specs)

        item['attributes'] = {
            'Specifications': _spec,
        }

        yield item
        # CHECK LINE 83 ON W.JSON... IT WASNT JUST THE USUAL PRODUCT PAGE
        # ALSO THE ERROR OF STOCK STATUS REFINED NOT SET TO ACCEPTED VALUE MUST BE LOOKED AT