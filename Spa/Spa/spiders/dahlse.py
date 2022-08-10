import scrapy
from ..helpers import log_error
from ..items import ProductItem


class Dahl(scrapy.Spider):
    name = "dahl"
    base_url = "https://www.dahl.se/store/dahl"
    no_of_requests = 0
    custom_delay_rules = {
        # Example: After 500 requests, do a paus for 180 seconds and so forth
        # 500: 180,
        # 200: 90,
        # 50: 30,
        20: 10,
        # 5: 1,
    }
    # crawled models
    crawled_models = []
    log_error = log_error
    brands = {
        "bosch": "",
    }

    def start_requests(self):
        username = 'robert.grip@homeonline.se'
        password = 'Tegnergatan28!'

        yield scrapy.FormRequest(
            url="https://www.dahl.se/store/Logon",
            formdata={
                "storeId": "10551",
                "CatalogId": "10002",
                "langId": "46",
                "reLogonURL": "https://www.dahl.se/store/dahl",
                "URL": "/webapp/wcs/stores/servlet/dahl?mobile=loginType&catalogId=10002&catalogId=10002&langId=46&langId=46&storeId=10551&storeId=10551",
                "logonId": username,
                "logonPassword": password,
                "Autologin": "True",
                "LoginAction": ""
            },
            callback=self.execute_search
        )

    def execute_search(self, response):
        brand_names = [
            "bosch"
        ]
        for brand_name in brand_names:
            facet = self.generate_brand_term(brand_name)
            yield scrapy.Request(
                url=f'https://www.dahl.se/store/AjaxCatalogSearchResultCompView?&langId=46&beginIndex=0&storeId=10551&catalogId=10002&categoryId=&pageSize=48&sType=SimpleSearch&searchTerm={brand_name}&searchType=102&resultCatEntryType=1&manufacturer=&searchTermScope=&showResultsPage=true&coSearchSkuEnabled=true&advancedSearchResult=false&facet={facet}&facet=field3%3A0.0&container=items&container=items&commandName=SearchDisplay&orderBy=0&categoryHint=&element=results',
                headers={
                    'x-requested-with': 'XMLHttpRequest',
                },
                callback=self.parse_search_results,
                meta={
                    'page': 1,
                    'brand_name': brand_name,
                    'facet': facet
                }
            )

    def parse_search_results(self, response):
        page = response.meta.get('page')
        brand_name = response.meta.get('brand_name')
        facet = response.meta.get('facet')

        for li in response.css('ul.order-item-list li.order-item-list__item.js-expand'):
            product_id = li.attrib.get('data-catentryid')

            item = ProductItem()
            item['scraper'] = self.name
            item['item_type'] = 'product'
            item['parent_category_url'] = ''
            item['product_type'] = 'VARIANT_PARENT'
            item['sku'] = product_id
            item['title'] = li.css("div div.order-item-list__description a.order-item-list__title span h2.seo_h2::text").get()
            item['image_urls'] = li.css('div div.order-item-list__img span img.img').attrib.get("src")
            item['variant_children_skus'] = []
            item['price_value'] = -1

            des_text = ''
            des_html = ''

            description_text = li.css("div.order-item-list__description div.order-item-list__short-desc span::text").get().strip()
            description_html = li.css("div.order-item-list__description div.order-item-list__short-desc span").get().strip()

            des_html += description_html
            des_text += description_text

            item['product_descriptions'] = {
                'SV': {
                    'Product Description': {
                        'text': des_text,
                        'html': des_html
                    }
                }
            }

            yield scrapy.Request(
                url=f'https://www.dahl.se/store/AjaxCatalogSearchResultCompView?langId=46&storeId=10551&catalogId=10002&categoryId=&pageSize=12&sType=SimpleSearch&searchTerm=&searchType=102&resultCatEntryType=1&manufacturer=&searchTermScope=&showResultsPage=true&coSearchSkuEnabled=&advancedSearchResult=false&facet=field3%3A0.0&productId={product_id}&element=articlelisting&requesttype=ajax',
                callback=self.parse_variants,
                meta={
                    'item': item,
                    'parent_sku': product_id,
                    'page': page,
                    'facet': facet,
                    'brand_name': brand_name,
                }
            )
        if 'Visa fler' in response.text:
            yield scrapy.Request(
                url=f'https://www.dahl.se/store/AjaxCatalogSearchResultCompView?pageSize={48*page}&langId=46&storeId=10551&catalogId=10002&categoryId=&pageSize=48&sType=SimpleSearch&searchTerm={brand_name}&searchType=102&resultCatEntryType=1&manufacturer=&searchTermScope=&showResultsPage=true&coSearchSkuEnabled=true&advancedSearchResult=false&facet={facet}&facet=field3%3A0.0&container=items&container=items&commandName=SearchDisplay&orderBy=0&categoryHint=&element=results',
                headers={
                    'x-requested-with': 'XMLHttpRequest',
                },
                callback=self.parse_search_results,
                meta={
                    'page': 1,
                    'brand_name': brand_name,
                    'facet': facet
                }
            )

    def parse_variants(self, response):
        item = response.meta.get('item')
        Parent_sku = response.meta.get('parent_sku')

        for tr in response.css("tbody.item-table__body tr"):
            variant_link = tr.css('td.item-table__cell.sku div a').attrib.get("href")
            sku = tr.css('td.item-table__cell.sku div a::text').get()

            item['variant_children_skus'].append(sku)
            yield scrapy.Request(
                url=variant_link,
                callback=self.parse_product,
                meta={
                    'item': item,
                    'parent_sku': Parent_sku,
                    'sku': sku,
                }
            )
        yield item

    def parse_product(self, response):
        parent_sku = response.meta.get('parent_sku')
        sku = response.meta.get('sku')
        item = response.meta.get('item')

        variant_item = item.deepcopy()
        variant_item['variant_children_skus'] = []

        variant_item['scraper'] = self.name
        variant_item['item_type'] = 'product'
        variant_item['parent_category_url'] = ''
        variant_item['variant_parent_sku'] = parent_sku
        variant_item['product_type'] = 'VARIANT_CHILD'
        variant_item['url'] = response.url
        variant_item['sku'] = sku
        variant_item['title'] = response.css("div.header__title-box div h1::text").get().strip()
        variant_item['stock_status_refined'] = 'IN_STOCK'
        variant_item['price_value'] = -1

        attributes = {}
        for tr in response.css('div#info.content div table tbody tr'):
            try:
                key = tr.css("td")[0].css('::text').get()
                value = tr.css("td")[1].css('::text').get()
            except Exception:
                pass
            attributes.update({key: value})

        variant_item['attributes'] = attributes

        desc_text = ''
        desc_html = ''

        description_html = ''.join(response.css('div.mb-30 p').getall()).strip()
        description_text = ' '.join(text.strip() for text in response.css('div.mb-30 p::text').getall()).replace('\xa0', '')

        desc_text += description_text
        desc_html += description_html

        variant_item['product_descriptions'] = {
            'SV': {
                'Product Description': {
                    'text': desc_text,
                    'html': desc_html
                }
            }
        }

        variant_item['image_urls'] = ''.join([img.attrib.get('src') for img in response.css("div.media_img a img#productMainImage")])
        item['variant_children_skus'].append(variant_item['sku'])

        yield variant_item



    @staticmethod
    def generate_brand_term(brand_name: str) -> str:
        return f'mfName_ntk_cs:{brand_name.upper()}'
