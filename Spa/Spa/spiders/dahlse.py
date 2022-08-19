import scrapy
from ..helpers import *
from ..items import CategoryItem, ProductItem


class Dahl(scrapy.Spider):
    name = "dahl"
    base_url = "https://www.dahl.se/store/dahl"

    storeId = "10551"
    catalogId = "10002"
    langId = "46"

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

        yield scrapy.FormRequest(
            url="https://www.dahl.se/store/Logon",
            formdata={
                "storeId": self.storeId,
                "CatalogId": self.catalogId,
                "langId": self.langId,
                "reLogonURL": "https://www.dahl.se/store/dahl",
                "URL": f"/webapp/wcs/stores/servlet/dahl?"
                       f"mobile=loginType&"
                       f"catalogId={self.catalogId}&"
                       f"langId={self.langId}&"
                       f"storeId={self.storeId}",
                "logonId": username,
                "logonPassword": password,
                "Autologin": "True",
                "LoginAction": ""
            },
            callback=self.execute_search
        )

    def execute_search(self, response):
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
            url = f'https://www.dahl.se/store/AjaxCatalogSearchResultCompView?&' \
                  f'langId={self.langId}&' \
                  f'beginIndex=0&' \
                  f'storeId={self.storeId}&' \
                  f'catalogId={self.catalogId}&' \
                  f'categoryId=&' \
                  f'pageSize=48&' \
                  f'sType=SimpleSearch&' \
                  f'searchTerm={brand_name}&' \
                  f'searchType=102&' \
                  f'resultCatEntryType=1&' \
                  f'manufacturer=&' \
                  f'searchTermScope=&' \
                  f'showResultsPage=true&' \
                  f'coSearchSkuEnabled=true&' \
                  f'advancedSearchResult=false&' \
                  f'facet={facet}&' \
                  f'facet=field3%3A0.0&' \
                  f'container=items&' \
                  f'container=items&' \
                  f'commandName=SearchDisplay&' \
                  f'orderBy=0&' \
                  f'categoryHint=&' \
                  f'element=results'

            category_item = CategoryItem()
            category_item['scraper'] = self.name
            category_item['item_type'] = 'category'
            category_item['url'] = url
            category_item['title'] = brand_name
            yield category_item

            custom_request_delay(self)
            yield scrapy.Request(
                url=url,
                headers={
                    'x-requested-with': 'XMLHttpRequest',
                },
                meta={
                    'page': 1,
                    'brand_name': brand_name,
                    'facet': facet,
                    'category_url': url,
                },
                callback=self.parse_search_results,
            )

    def parse_search_results(self, response):
        page = response.meta.get('page')
        brand_name = response.meta.get('brand_name')
        facet = response.meta.get('facet')
        category_url = response.meta.get('category_url')

        print(f'Got {len(response.css("ul.order-item-list li.order-item-list__item.js-expand"))} products for {brand_name}')
        for li in response.css('ul.order-item-list li.order-item-list__item.js-expand'):
            product_id = li.attrib.get('data-catentryid')

            item = ProductItem()
            item['scraper'] = self.name
            item['item_type'] = 'product'
            item['parent_category_url'] = category_url
            item['url'] = response.url
            item['product_type'] = 'VARIANT_PARENT'
            item['sku'] = product_id
            item['title'] = li.css("div div.order-item-list__description a.order-item-list__title span h2.seo_h2::text").get()

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

    def parse_variants(self, response):
        item = response.meta.get('item')
        parent_sku = response.meta.get('parent_sku')

        variants = {}
        for tr in response.css("tbody.item-table__body tr"):
            variant_link = tr.css('td.item-table__cell.sku div a').attrib.get("href")
            if not variant_link:
                continue
            sku = tr.css('td.item-table__cell.sku div a::text').get()
            if sku not in variants:
                variants[sku] = variant_link

        # Simple product or variant products?
        if len(variants) == 0:
            log_error(self, f'Could not extract products for {parent_sku}')
        elif len(variants) == 1:
            sku = list(variants.keys())[0]
            yield scrapy.Request(
                    url=variants[sku],
                    meta={
                        'item': item,
                        'sku': sku,
                    },
                    callback=self.parse_product,
                )
        elif len(variants) > 1:
            item['variant_children_skus'] = []
            for sku, url in variants.items():
                # debug - This product (see URL below) should give us 5 variants but we only get 3...
                if item['sku'] == '285519':
                    print(item['sku'], sku, url)
                if sku not in item['variant_children_skus']:
                    item['variant_children_skus'].append(sku)
                    yield scrapy.Request(
                        url=url,
                        meta={
                            'item': item,
                            'parent_sku': parent_sku,
                            'sku': sku,
                        },
                        callback=self.parse_product,
                    )
        item['variant_attributes'] = self.variant_attrs[item["sku"]]
        yield item

    def parse_product(self, response):
        parent_sku = response.meta.get('parent_sku', None)
        sku = response.meta.get('sku')
        item = response.meta.get('item')

        variant_item = item.deepcopy()
        variant_item['variant_children_skus'] = None

        variant_item['scraper'] = self.name
        variant_item['item_type'] = 'product'

        if parent_sku is None:
            variant_item['product_type'] = 'SIMPLE'
            variant_item['variant_parent_sku'] = None
        else:
            variant_item['product_type'] = 'VARIANT_CHILD'
            variant_item['variant_parent_sku'] = parent_sku

        variant_item['url'] = response.url
        variant_item['sku'] = sku
        variant_item['title'] = response.css("div.header__title-box div h1::text").get().strip()
        variant_item['stock_status_refined'] = 'IN_STOCK'
        variant_item['price_value'] = -1
        variant_item['part_numbers'] = {}

        if 'attributes' not in variant_item:
            variant_item['attributes'] = {}
        for tr in response.css('div#info.content div table tbody tr'):
            try:
                key = tr.css("td")[0].css('::text').get()
                value = tr.css("td")[1].css('::text').get()
                variant_item['attributes'][key] = value
            except Exception:
                pass

        description_html = ''
        description_text = ' '

        for p in response.css('div.mb-30 p'):
            if p.css('::text').get():
                if p.css('::text').get().startswith('Art.'):
                    continue
                elif 'Lev. Art. nr' in p.css('::text').get():
                    val = p.css('::text').get().replace('Lev. Art. nr', '').strip()
                    variant_item['part_numbers'].update({
                        f'MPN_{val}': {
                            'type': 'MPN',
                            'id': val
                        }
                    })
                elif 'EAN. Art. nr.' in p.css('::text').get():
                    val = p.css('::text').get().replace('EAN. Art. nr.', '').strip()
                    variant_item['part_numbers'].update({
                        f'EAN_{val}': {
                            'type': 'EAN',
                            'id': val
                        }
                    })
                else:
                    description_text += p.css('::text').get()
                    description_html += p.get()

        variant_item['product_descriptions'] = {
            'SV': {
                'Product Description': {
                    'text': description_text,
                    'html': description_html
                }
            }
        }

        variant_item['file_urls'] = []
        for li in response.css("div ul#technicaldoc.list li"):
            if li.css("a").attrib.get("href"):
                m = li.css("a").attrib.get("href")
                if m.startswith("/"):
                    m = f"https://www.dahl.se{m}"
                variant_item['file_urls'].append(m)

        priority = len(variant_item['image_urls']) + 1
        for img in response.css("div.media_img a img#productMainImage"):
            img_url = img.attrib.get('src')
            if img_url is not None:
                img_url = f"https://content-eshop.dahl.se{img_url}"
                variant_item['image_urls'].append(img_url)
                variant_item['image_data'][img_url] = {
                    'priority': priority
                }
                priority += 1
        self.variant_attrs[item["sku"]].update({
            variant_item["sku"]: variant_item["attributes"]
        })
        yield variant_item
