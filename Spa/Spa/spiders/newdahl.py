import scrapy
from ..helpers import *
from ..items import CategoryItem, ProductItem
from scrapy.http import JsonRequest


class Dahl(scrapy.Spider):
    name = "dahlbeta"
    base_url = "https://beta.dahl.se/"

    # storeId = "10551"
    # catalogId = "10002"
    # langId = "46"

    no_of_requests = 0
    custom_delay_rules = {
        # Example: After 500 requests, do a paus for 180 seconds and so forth
        # 500: 180,
        # 200: 90,
        50: 10,
        # 20: 10,
        10: 2,
    }

    log_error = log_error
    error_log = []

    # crawled models
    urls = {}
    variant_attrs = {}

    def start_requests(self):
        username, password = fetch_spider_credentials(self.name)

        yield JsonRequest(
            url="https://prd-api.dahl.se/auth-service/sessions",
            data={
                "username": username,
                "password": password
            },
            callback=self.execute_search
        )

    def execute_search(self, response):
        data = response.json()
        self.access_token = data.get('AuthenticationResult').get('AccessToken')

        brand_names = [
            # "ALTERNA",
            # "DURAVIT",
            # "GROHE SVERIGE",
            # "IFÖ",
            # "GUSTAVSBERG",
            # "PAX",
            # "GEBERIT",
            # "MORA",
            "ORAS",
        ]
        for brand_name in brand_names:
            facet = f'mfName_ntk_cs:{brand_name.upper()}'
            url = 'https://sgds-dahl-prd.54proxy.com/search'

            category_item = CategoryItem()
            category_item['scraper'] = self.name
            category_item['item_type'] = 'category'
            category_item['url'] = url
            category_item['title'] = brand_name
            yield category_item

            custom_request_delay(self)
            yield JsonRequest(
                url=url,
                data={
                    "resultsOptions":{
                        "skip":0,
                        "take":20,
                        "sortBy":[],
                        "filter":{
                            "type":"attribute",
                            "attributeName":"assortmentIds",
                            "value":"GG Butikssortiment",
                            "comparisonMode":"contains"
                        },
                        "facets":[
                            {
                                "attributeName":"brand"
                            },
                            {
                                "attributeName":"classificationName"
                            },
                            {
                                "attributeName":"Område"
                            }
                        ]
                    },
                    "query": brand_name,
                    "customData": {"directSearch": False}
                },
                meta={
                    'skip': 20,
                    'brand_name': brand_name,
                    'category_url': url,
                },
                callback=self.parse_search_results,
            )

    def parse_search_results(self, response):
        skip = response.meta.get('skip')
        data = response.json()
        total = data.get("results", {}).get("count", 50)

        for _item in data.get("results", {}).get("items", []):



            item = ProductItem()
            item['scraper'] = self.name
            item['item_type'] = 'product'
            item['parent_category_url'] = response.meta.get("category_url")
            item['url'] = response.url
            item['product_type'] = 'VARIANT_PARENT'
            item['sku'] = product_id
            item['title'] =

            item['image_urls'] = []
            item['image_data'] = {}
            priority = 1
            for img in li.css('div div.order-item-list__img span img.img'):
                img_url = img.attrib.get("data-src")
                if img_url is not None:
                    item['image_urls'].append(img_url)
                    item['image_data'][img_url] = {
                        'priority': priority
                    }
                    priority += 1

            item['price_value'] = -1
            item["price_currency"] = "SEK"

            description_text = ''.join([text.strip() for text in li.css('span[itemprop="description"]::text').getall()]).strip()
            description_html = li.css('span[itemprop="description"]').get().strip()
            item['product_descriptions'] = {
                'SV': {
                    'Product Description': {
                        'text': description_text,
                        'html': description_html
                    }
                }
            }

            item['attributes'] = {
                'Brand': brand_name,
            }
            item["variant_attributes"] = {}
            self.variant_attrs[item["sku"]] = {}

            custom_request_delay(self)
            url = f'https://www.dahl.se/store/AjaxCatalogSearchResultCompView?'\
                  f'langId={self.langId}&'\
                  f'storeId={self.storeId}&'\
                  f'catalogId={self.catalogId}&'\
                  f'categoryId=&'\
                  f'pageSize=12&'\
                  f'sType=SimpleSearch&'\
                  f'searchTerm=&'\
                  f'searchType=102&'\
                  f'resultCatEntryType=1&'\
                  f'manufacturer=&'\
                  f'searchTermScope=&'\
                  f'showResultsPage=true&'\
                  f'coSearchSkuEnabled=&'\
                  f'advancedSearchResult=false&'\
                  f'facet=field3%3A0.0&'\
                  f'productId={product_id}&'\
                  f'element=articlelisting&'\
                  f'requesttype=ajax'
            yield scrapy.Request(
                url=url,
                meta={
                    'item': item,
                    'parent_sku': product_id,
                    'page': page,
                    'facet': facet,
                    'brand_name': brand_name,
                },
                callback=self.parse_variants,
            )

        if 'Visa fler' in response.text:
            custom_request_delay(self)
            url = f'https://www.dahl.se/store/AjaxCatalogSearchResultCompView?'\
                  f'pageSize={48*page}&'\
                  f'langId={self.langId}&'\
                  f'storeId={self.storeId}&'\
                  f'catalogId={self.catalogId}&'\
                  f'categoryId=&'\
                  f'pageSize=48&'\
                  f'sType=SimpleSearch&'\
                  f'searchTerm={brand_name}&'\
                  f'searchType=102&'\
                  f'resultCatEntryType=1&'\
                  f'manufacturer=&'\
                  f'searchTermScope=&'\
                  f'showResultsPage=true&'\
                  f'coSearchSkuEnabled=true&'\
                  f'advancedSearchResult=false&'\
                  f'facet={facet}&'\
                  f'facet=field3%3A0.0&'\
                  f'container=items&'\
                  f'container=items&'\
                  f'commandName=SearchDisplay&'\
                  f'orderBy=0&'\
                  f'categoryHint=&'\
                  'element=results'
            yield scrapy.Request(
                url=url,
                headers={
                    'x-requested-with': 'XMLHttpRequest',
                },
                meta={
                    'page': 1,
                    'brand_name': brand_name,
                    'facet': facet
                },
                callback=self.parse_search_results,
            )



    @staticmethod
    def clean_item_attributes(item):
        attr_item = {}
        for attr in item.get("")
