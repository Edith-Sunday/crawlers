import scrapy
from ..helpers import *
from ..items import CategoryItem, ProductItem


class AstralPool(scrapy.Spider):
    name = "astralpool"
    base_url = "https://www.astralpool.com/"

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
        category_urls = [li.css('a').attrib.get('href') for li in response.css("div div.genux-left.genux-header-products1.genux-abd-5 ul li")]
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
        category_item['title'] = ''.join(response.css("div.genux-abd-20.genux-asd-20 h1::text").getall())
        category_item['parent_category_url'] = parent_url

        breadcrumb = ''
        for a in response.css("div.genux-breadcrump a"):
            breadcrumb = f"{breadcrumb}/{a.css('::text').get().strip()}"
        for span in response.css("div.genux-breadcrump span"):
            breadcrumb = f"{breadcrumb}/{span.css('::text').get().strip()}"

        category_item['breadcrumbs'] = breadcrumb
        category_item['child_product_urls'] = []
        category_item['child_category_urls'] = []
        category_item['image_urls'] = [response.css("div.genux-gallery div.item img.genux-product-image").attrib.get("src")]
        category_item['description_html'] = ' '.join(response.css("div.genux-abd-20.genux-asd-20.genux-hierarchy-desc p").getall())

        for div in response.css("div#genux-category-products div.genux-related-product-img"):
            href = div.css('div a').attrib.get('href')
            if response.css('ul.genux-product-title span') and response.css('ul.genux-product-title span::text').get().strip() == 'Productos':
                category_item['child_product_urls'].append(href)
                yield scrapy.Request(
                    url=href,
                    callback=self.parse_product,
                    meta={'parent_url': category_item['url']}
                )
            else:
                category_item['child_category_urls'].append(href)
                yield scrapy.Request(
                    url=href,
                    callback=self.parse_category,
                    meta={'parent_url': category_item['url']}
                )
        yield category_item

    def parse_product(self, response):
        parent_url = response.meta.get('parent_url')
        variant_parent_sku = response.meta.get('variant_parent_sku')
        item_sku = response.meta.get('item_sku')

        item = ProductItem()
        item['scraper'] = self.name
        item['item_type'] = 'product'
        item['breadcrumbs'] = response.url.replace(self.base_url, '')
        item['parent_category_url'] = parent_url
        item['file_urls'] = []
        item['file_data'] = []

        item['price_value'] = -1
        item['price_currency'] = 'SEK'

        item['stock_status_refined'] = 'IN_STOCK'

        item['product_type'] = 'VARIANT_PARENT'
        item['variant_children_skus'] = []

        if variant_parent_sku:
            item['product_type'] = 'VARIANT_CHILD'
            item['variant_parent_sku'] = variant_parent_sku

        item['url'] = response.url
        item['title'] = response.css("h1 span::text").get()
        item['sku'] = item_sku if item_sku else item['title']
        item['image_urls'] = [img.attrib.get('src') for img in response.css("div.item a img.genux-product-image")]
        item['related_products'] = []

        for a in response.css("div.genux-product-related div div a"):
            _rel_prod_url = a.attrib.get('href')
            item['related_products'].append({
                'relation': 'RELATED_PRODUCT',
                'url': _rel_prod_url
            })

        desc_text = ''
        desc_html = ''

        desc_text += ''.join([text.strip() for text in response.css("div.genux-product-desc p::text").getall()])
        desc_html += ''.join([text.strip() for text in response.css("div.genux-product-desc p").getall()])

        item['product_descriptions'] = {
            'SV': {
                'Product Description': {
                    'text': desc_text,
                    'html': desc_html
                }
            }
        }
        for tr in response.css('table.genux-asd-hide tbody tr'):
            if tr.css('td') and tr.css('td')[0].css('a') and tr.css('td')[0].css('a').attrib.get('href'):
                href = tr.css('td')[0].css('a').attrib.get('href')
                item['variant_children_skus'].append(href)
                yield scrapy.Request(
                    url=href,
                    callback=self.parse_product,
                    meta={
                        'parent_url': parent_url,
                        'variant_parent_sku': item['sku'],
                        'item_sku': tr.css('td')[0].css('a::text').get()
                    }
                )
        for div in response.css('div.genux-product-document'):
            href = div.css('a').attrib.get('href')
            text = div.css('a::text').get()
            if not href:
                continue
            item['file_urls'].append(href)
            item['file_data'].append({
                'name': text
            })
        yield item
