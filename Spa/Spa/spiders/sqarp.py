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

        packages = self.read_packages(ws)
        specs = self.read_specs(ws)
        _supplier = self.supplier_data(ws)

        categories = {}

        for row in ws.iter_rows(min_row=5, max_row=2896):

            category_name = row[6].value
            category_item = categories.get(category_name)
            if not category_item:
                category_item = CategoryItem()
                # TODO - Why does title have https appended?z
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
            item['product_descriptions'] = {
                'EN': {
                    'Product Description': {
                        'text': row[16].value,
                        'html': row[16].value,
                    }
                }
            }
            item['rrp_value'] = Decimal(row[17].value)

            ean_code = str(row[18].value)
            item['part_numbers'] = {
                f'EAN_{ean_code}': {
                    'type': 'EAN',
                    'id': ean_code,
                }
            }
            item['parent_category_url'] = category_item['url']

            package_data = packages.get(item['sku'])
            if package_data:
                item['attributes'].update(package_data)

            spec_data = specs.get(item['sku'])
            if spec_data:
                item['attributes'].update(spec_data)

            category_item['child_product_urls'].append(item['url'])
            categories[category_name] = category_item
            yield item

        for name, category_item in categories.items():
            yield


    @staticmethod
    def check_sheets(filename: str):
        wb = load_workbook(filename)
        # this should print the name of the sheets in the workbook and compare to the sheetnames we have originally written
        sheet_names = ['Document Overview', 'Product Base Data', 'Packages', 'Product Attributes', 'Supplier Data', 'Product Images', 'Product Documents', 'Product Videos', 'Related Products']

        for name in wb.sheetnames:
            if name in sheet_names:
                continue
            else:
                print(f"{name} was added to workbook.")

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

    @staticmethod
    def read_packages(ws):
        attr = {}

        if ws.max_column > 8:
            print('There seems to be more columns')

        for row in ws.iter_rows(min_row=5, max_row=-1):

            temp_attr = {
                'package_depth_mm': row[3].value,
                'package_height_mm': row[4].value,
                'package_width_mm': row[5].value,
                'package_volume_m3': row[6].value,
                'package_weight_kg': row[7].value,
            }
            attr.update({row[0].value: temp_attr})
        return attr

    @staticmethod
    def read_specs(ws):
        attr = {}

        specs_columns = [cell.value for row in ws.iter_rows(min_row=3, max_row=3) for cell in row]
        title_columns = [cell.value for row in ws.iter_rows(min_row=4, max_row=4) for cell in row]

        for row in ws.iter_rows(min_row=5, max_row=-1):
            specs = {}
            for idx, cell in enumerate(row):
                if specs_columns[idx] == 'Specifikationer':
                    # add cell.value to attributes
                    specs.update({title_columns[idx]: cell.value})
                    continue
            attr.update({"specifications": specs})
        return attr

    @staticmethod
    def read_doc(ws):

     # ws = wb["Product Documents"]
        documents = {}

        if ws.max_column > 6:
            # check that the max column is actually 6
            print('There seems to be more columns for Product Documents')

        for row in ws.iter_rows(min_row=5, max_row=-1):
            file_data = {}
            file_url = row[3].value
            language = row[4].value
            document_type = row[5].value

            file_data[file_url] = {
                'Language': language,
                'document_type': document_type,
            }
            documents.update({row[0].value: file_data})
            # print(documents)
        return documents

    @staticmethod
    def read_video(ws):
        # ws = wb["Product Videos"]
        videos = {}

        if ws.max_column > 7:
            # check that the max column is actually 7
            print('There seems to be more columns for Product Videos')

        for row in ws.iter_rows(min_row=5, max_row=-1):
            video_data = {}
            video_url = row[3].value
            video_host = row[4].value
            language = row[5].value
            video_type = row[6].value

            video_data[video_url] = {
                'video_host': video_host,
                'Language': language,
                'video_type': video_type,
            }
            videos.update({row[0].value: video_data})
            # print(videos)
        return videos

    @staticmethod
    def read_images(ws):
        images = {}
        # ws = wb["Product Images"]

        if ws.max_column > 6:
            # check that the max column is actually 6
            print('There seems to be more columns for Product Images')

        for row in ws.iter_rows(min_row=5, max_row=-1):
            item_image_value = images.get(row[0].value)
            if not item_image_value:
                item_image_value = {
                    'image_urls': [],
                    'image_data': {},
                    'priority': 0
                }

            image_url = row[4].value
            filename = row[5].value
            title = ''

            if filename.endswith('.jpg'):
                filename = filename
            else:
                filename = title

            item_image_value['image_urls'].append(image_url)
            item_image_value['image_data'][image_url] = {
                'priority': item_image_value['priority'] + 1,
                'title': title,
                'filename': filename,
            }
            item_image_value['priority'] = item_image_value['priority'] + 1

            images.update({
                row[0].value: item_image_value
            })
        return images

    @staticmethod
    def related_product(ws):
        # ws = wb["Related Products"]
        related_products = {}

        if ws.max_column > 10:
            # check that the max column is actually 10
            print('There seems to be more columns for Related Products')

        for row in ws.iter_rows(min_row=5, max_row=-1):
            rel_prod_data = {}
            sku = row[6].value
            relation = row[4].value
            quantity = row[5].value

            if quantity == '':
                quantity == 1

            rel_prod_data = {
                "sku": sku,
                "relation": relation,
                "quantity": quantity,
            }
            related_products.update({row[0].value: rel_prod_data})
            print(related_products)
            #NEED HELP HERE he said something about a list whats that about? so the related products is supposed to be a list not a dictionary
        return related_products

    @staticmethod
    def supplier_data(ws):
        # ws = wb["Supplier Data"]
        Supplier = {}

        if ws.max_column > 10:
            print('There seems to be more columns for Supplier Data')
            # ensure max column is actually 10
        item = ProductItem()

        for row in ws.iter_rows(min_row=5, max_row=-1):
            supplier_info = {}

            supplier_name = row[3].value
            supplier_id = row[4].value
            product_title = row[5].value
            product_url = row[6].value
            list_price = Decimal(row[8].value)
            # HELPPPPPP!!!!! the output is not as i wrote from here to line 324
            stock_status_max_delivery_time_business_days = row[9].value

            if stock_status_max_delivery_time_business_days is not None:
                stock_status_max_delivery_time_business_days = Decimal(row[9].value)
            else:
                stock_status_max_delivery_time_business_days == -1

            order_package_unit = row[7].value

            if order_package_unit == 'st':
                order_package_unit == 1

            price = list_price * Decimal(1.25)
            if price != parse.get(item['rrp_value']):
                print("Error with list price")
            # does the above make sense? how do i link it since i can't use self?
            # MATCHING TO DO
        # make sure that supplier id and sku are same
        # make sure that name and url too are same as the data from product base data
        # make sure rrp value and list price as multiples as written above


            supplier_info = {
                "supplier_name": supplier_name,
                "supplier_id": supplier_id,
                "product_title": product_title,
                "product_url": product_url,
                item["order_package_unit"]: order_package_unit,
                "list_price": list_price,
                item["stock_status_max_delivery_time_business_days"]: stock_status_max_delivery_time_business_days,


            }
            Supplier.update({row[0].value: supplier_info})
            print(Supplier)

        return Supplier

