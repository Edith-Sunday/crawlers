import scrapy
from openpyxl import load_workbook
from decimal import Decimal

from ..helpers import log_error
from ..items import CategoryItem, ProductItem


class DuschbyggarnaSQARP(scrapy.Spider):
    name = "duschbyggarna"
    error_log = []
    log_error = log_error

    def start_requests(self):
        yield scrapy.Request(
            "https://example.com",
            callback=self.parse
        )

    def parse(self, response):
        # work_book = self.read_file('data_input/duschbyggarna_sqarp_base.xlsx')
        work_book = self.read_file('base.xlsx')


        if not self.is_valid(work_book['Document Overview']):
            print('Received invalid document')
            return

        ws = work_book['Product Base Data']

        categories = {}

        for row in ws.iter_rows(min_row=5, max_row=2896):

            category_name = row[6].value
            category_item = categories.get(category_name)
            if not category_item:
                category_item = CategoryItem()
                # TODO - Why does title have https appended?
                #  why was not url set for the category?
                category_item['title'] = category_name.lower()
                category_item['url'] = f'https://{category_name.lower()}'
                category_item['child_product_urls'] = []

            item = ProductItem()
            item['sku'] = row[1].value
            item['scraper'] = row[2].value
            item['title'] = f"{item['scraper']}-{item['sku']}"
            item['url'] = row[3].value
            item['import_export_taric_code_eu'] = row[4].value
            item['import_export_country_of_origin'] = row[5].value
            item['product_type'] = row[7].value
            item['brand'] = row[8].value
            item['series'] = row[9].value
            item['unique_selling_points'] = row[10].value
            item['model'] = row[11].value
            # item['variant_name : variant_group_variables'] = f'{row[12].value} : {row[15].value}'
            item['attributes'] = {}
            item['attributes']["ecombooster_sku"] = row[0].value
            item['attributes']["name_of_variant_group"] = row[13].value
            item["attributes"]['variant_group_id'] = row[14].value

            # TODO - Not right format for this field!!
            item['product_descriptions'] = {
                'EN': {
                    'Product Description': {
                        'text': row[16].value,
                        'html': row[16].value,
                    }
                }
            }

            # TODO - NEVER use float, use Decimal for all prices...
            #  int can be used when that is possible for other numeric fields
            item['rrp_value'] = Decimal(row[17].value)

            ean_code = str(row[18].value)
            item['part_numbers'] = {
                f'EAN_{ean_code}': {
                    'type': 'EAN',
                    'id': ean_code,
                }
            }

            item['parent_category_url'] = category_item['url']

            category_item['child_product_urls'].append(item['url'])
            categories[category_name] = category_item
            yield item

        for name, category_item in categories.items():
            yield category_item

    @staticmethod
    def read_file(filename: str):
        wb = load_workbook(filename)
        return {sheet: wb[sheet] for sheet in wb.sheetnames}

    @staticmethod
    def is_valid(worksheet) -> bool:
        # checks if the field exists after reading file
        export_config = {
            "Table format for relational data": "One relation per row",
            "Data on inspirational entities included": True,
            "Include html mark-up for descriptions": False,
            "Language": "sv",
            "Selected multi-value separator": ";"
        }

        input_config = {}

        for i in range(27, 33):
            e_value = f"E{i}"
            f_value = f"F{i}"

            if not worksheet[e_value].value and not worksheet[f_value].value:
                continue
            input_config.update({
                worksheet[e_value].value: worksheet[f_value].value,
            })

        return export_config == input_config
