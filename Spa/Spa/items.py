import scrapy

# We should strive at having a streamlined structure for the Items so that they can be seamlessly imported into
# ecombooster.io.
# For all fields that we add below, we need to make sure that the output is consistent with the expected types


class CategoryItem(scrapy.Item):
    # Should be set to the name of the scraper/supplier. Should be the same name that is used in ecombooster.io.
    scraper = scrapy.Field()                    # Mandatory

    # Should be set to 'category'
    item_type = scrapy.Field()                  # Mandatory

    # List of errors that occurred during the scraping or processing of the item. The errors are strings.
    errors = scrapy.Field()                     # Optional

    # Optional, not used on many sites. String.
    id = scrapy.Field()                         # Optional

    # The URL to the scraped category page. In case there is pagination, the category should only be stored as
    # one (1) item. In the examples below, the first URL should be used as "baseline" for the category.
    # https://demo.se/cirkulationspumpar/ and https://demo.se/cirkulationspumpar/page/2/
    # https://www.demo.eu/latestproducts and https://www.demo.eu/latestproducts?p=2
    # The URL is seen as the main identifier for categories.
    # This should preferably be dealt with in the scraper, by setting the base URL when yielding the scraping
    # of the paginated URL. If that is not possible, it needs to be fixed in the pipeline.
    url = scrapy.Field()                        # Mandatory

    # This is the title / name of the category. String.
    title = scrapy.Field()                      # Mandatory

    # This is the breadcrumbs of the category. String.
    breadcrumbs = scrapy.Field()                # Optional, but available in almost 100% of the cases

    # This is the URL to the parent category. String.
    parent_category_url = scrapy.Field()        # Mandatory. If None, this is a root category...

    # These fields are lists containing URLs to child categories and child products
    child_category_urls = scrapy.Field()        # Optional
    child_product_urls = scrapy.Field()         # Optional

    # This field contains a list of URLs to related categories. Not used often.
    related_category_urls = scrapy.Field        # Optional

    # These fields contains the category description in html. They are not always available.
    description_html = scrapy.Field()           # Optional
    description_excerpt_html = scrapy.Field()   # Optional

    # image_urls is populated in the scraping process, contains a list of URLs to images.
    # image_details is optional and can be used to store additional information about images. The image_url shall
    #  be used as identifier. Example of data that can be stored here are "type of image", e.g. main image,
    #  scenario image, mechanical drawing etc. Most likely not used for categories at all...
    # images is populated by scrapy when the images are downloaded.
    image_urls = scrapy.Field()                 # Optional
    image_details = scrapy.Field()              # Optional
    images = scrapy.Field()                     # Added by the Pipeline
    import_export_taric_code_eu = scrapy.Field()
    import_export_country_of_origin = scrapy.Field()
    brand = scrapy.Field()
    series = scrapy.Field()
    unique_selling_points = scrapy.Field()
    model = scrapy.Field()

class ProductItem(scrapy.Item):
    """
    This Item is used for all products.
    Each Product (Simple, Variant etc) is an Item of itself.
    Variant Child products are linked / related to Variant Parent products.
    For Variant products,
     - keep all data that is common for all the Children in the Parent Product
     - use the Child Item to record the unique parts of the product as well as the relation to the Variant Parent
    """

    # Should be set to the name of the scraper/supplier. Should be the same name that is used in ecombooster.io.
    scraper = scrapy.Field()                    # Mandatory

    # Should be set to 'product'
    item_type = scrapy.Field()                  # Mandatory

    # List of errors that occurred during the scraping or processing of the item. The errors are strings.
    errors = scrapy.Field()                     # Optional

    # Optional. Can in some cases be the same as the sku. String.
    id = scrapy.Field()                         # Optional

    # The products part number (Stock Keeping Unit). String.
    # The SKU is seen as the main identifier for products.
    sku = scrapy.Field()                        # Mandatory, validation exists

    # The URL to the scraped product page.
    url = scrapy.Field()                        # Mandatory, validation exists

    # title - the title / name of the product. String.
    # sub_title - In some cases, e.g. when there are variation products, this field is used to store the
    #  name of the variant.
    title = scrapy.Field()                      # Mandatory, validation exists
    sub_title = scrapy.Field()                  # Optional

    # This is the breadcrumbs of the product. String.
    breadcrumbs = scrapy.Field()                # Optional, but available in almost 100% of the cases

    # This is the URL to the parent category. String.
    parent_category_url = scrapy.Field()        # Mandatory, validation exists

    # product type is one of the following:
    # SIMPLE - Used for stand-alone products
    # VARIANT_PARENT - Used for the parent in variant products
    # VARIANT_CHILD - Used for children in variant products
    product_type = scrapy.Field()               # Mandatory, validation exists

    # Shall be set when product_type == 'VARIANT_CHILD'
    variant_parent_sku = scrapy.Field()         # Mandatory when product_type=='VARIANT_CHILD', validation exists

    # A list of SKUs, shall be set when product_type == 'VARIANT_PARENT'
    variant_children_skus = scrapy.Field()      # Mandatory when product_type=='VARIANT_PARENT'

    # There can be different (types of) product descriptions. Do manage this, we store them in a dict.
    # One example can be found here:
    # https://www.hydrospares.co.uk/hot-tub-spares/whirlpool-bath-parts/control/1-function-control-/hydroair-classic-line-control-box-20-0243.htm
    # There COULD potentially be product descriptions in different languages, so start by storing the actual
    # language code, e.g. EN.
    # In the example, there are three tabs named "Product Description", "Downloads & Articles" and "More info".
    # Each of these tabs would go into a separate dict in this case.
    # For now, we will use the heading (or name of the tab) to specify the 'type'. In the long run, we will strive
    # towards specifying a number of types that we can manage.
    # Example:
    #   products_descriptions = {
    #     'EN': {
    #       'Product Description':
    #         'text': 'the raw text without html...',
    #         'html': 'the html text...' },
    #       'Downloads & Articles': {
    #         'text': 'the raw text without html...',
    #         'html': 'the html text...' },
    #       'More Info': {
    #         'text': 'the raw text without html...',
    #         'html': 'the html text...' },
    #     }
    #   }
    product_descriptions = scrapy.Field()       # Optional, but available in almost 100% of the cases, validation exists

    # Attributes or characteristics contains e.g. technical data about the product. It can also be data related
    # to packaging or pricing that does NOT fit into other sections in the ProductItem. The dict can potentially
    # consist of several levels. If we look at the example on this page:
    # https://www.hydrospares.co.uk/hot-tub-spares/equipment/pumps-parts/two-speed-pumps/aqua-flo-flo-master-xp2e-2-speed-pump-1-5hp-2-speed.htm
    # The attributes are found in the tab "Product Description" and consists of (in this particular case) four (4)
    # tables at the end of the section. Using this as an example, the structure would be:
    #   attributes = {
    #     'Model Information': {
    #       'Dimensions L x W x H': '378x200x203mm',
    #       'Type': '2 Speed - Circ + Boost' },
    #     'Flow': {
    #       'HEAD - H max': '12.5 / 3m',
    #       'HEAD - Q max': '300 L/min' },
    #   }
    # Another scenario is that the attributes are only stored in a flat hierarchy, e.g.
    #   attributes = {
    #     'Dimensions L x W x H': '378x200x203mm',
    #     'Type': '2 Speed - Circ + Boost',
    #     'HEAD - H max': '12.5 / 3m',
    #     'HEAD - Q max': '300 L/min',
    #   }
    attributes = scrapy.Field()                 # Optional
    variant_attributes = scrapy.Field()

    # image_urls is populated in the scraping process, contains a list of URLs to images.
    # image_details is optional and can be used to store additional information about images. The image_url shall
    #  be used as identifier. Example of data that can be stored here are "type of image", e.g. main image,
    #  scenario image, mechanical drawing etc.
    # images is populated by scrapy when the images are downloaded.
    image_urls = scrapy.Field()                 # Optional
    image_data = scrapy.Field()                 # Optional
    images = scrapy.Field()                     # Added by the Pipeline

    # video_urls is populated in the scraping process, contains a list of URLs to videos.
    video_urls = scrapy.Field()                 # Optional

    # file_urls is populated in the scraping process, contains a list of URLs to files.
    # file_details is optional and can be used to store additional information about files. The file_url shall
    #  be used as identifier. Example of data that can be stored here are "type of file", e.g. technical manual,
    #  mechanical drawing etc.
    # files is populated by scrapy when the files are downloaded.
    file_urls = scrapy.Field()                  # Optional
    file_data = scrapy.Field()                  # Optional
    files = scrapy.Field()                      # Added by the Pipeline

    # stock_status_raw - extracting the text from the webpage without any refinement
    # stock_status_refined - shall be one of the following:
    #  'IN_STOCK' - In stock
    #  'BACKORDER' - Backorders accepted
    #  'LAST_AVAILABLE' - Last available, i.e. will be phased out
    #  'DISCONTINUED' - Discontinued, i.e. not available anymore
    #  'BUILT_ON_ORDER' - Built on order, i.e. the supplier builds this when it is ordered
    #  'SPECIALORDER' - Special order, e.g. can be specifically ordered by the supplier but not
    #    something that they normally have in stock
    #  'COMING_SOON' - Coming soon, about to be introduced
    #  'NA' - Not applicable, used for e.g. variant parents
    #  'UNKNOWN' - Unknown, e.g. did not match anyone of the above scenarios
    # stock_status_quantity - contains the no of items in stock (int)
    # stock_status_eta - if product not in stock, this is the date for estimated arrival to suppliers warehouse.
    #  eta stands for estimated time of arrival
    stock_status_raw = scrapy.Field()           # Optional
    stock_status_refined = scrapy.Field()       # Mandatory, validation exists
    stock_status_quantity = scrapy.Field()      # Optional
    stock_status_eta = scrapy.Field()           # Optional, validation exists

    # order_package_quantity - how many items are there in each package?
    # order_minimum_order_quantity - indicates the smallest amount of items that can be ordered
    order_package_quantity = scrapy.Field()                 # Optional, if not possible to determine, assumption is 1
    order_package_minimum_order_quantity = scrapy.Field()   # Optional, if not possible to determine, assumption is 1

    # price_raw - extracting the text from the webpage without any refinement
    # price_value - Decimal value. Should be given excluding VAT.
    # price_currency - abbreviation for currency, e.g. SEK, EUR, USD
    # price_vat - applicable values: 'EXCL', 'INCL', 'UNKNOWN'
    # price_percentage - Decimal value, e.g. 0.25
    # price_per_unit - indicates how pricing is set. Applicable values:
    #  'PER_EACH'- i.e. if the price is 10, it means the price is 10/unit
    #  'PER_PACKAGE' - i.e. if the price is 10 and the order_package_quantity is 5, the price is 10/5 = 2/unit
    price_raw = scrapy.Field()                  # Optional, will not be stored in ecombooster
    price_value = scrapy.Field()                # Mandatory, in case not possible to determine, set to -1
    price_currency = scrapy.Field()             # Mandatory, validation exists
    price_vat = scrapy.Field()                  # Mandatory
    price_vat_percentage = scrapy.Field()       # Optional
    price_per_unit = scrapy.Field()             # Mandatory, default value 'PER_EACH'

    # price_discount_raw - extracting the text from the webpage without any refinement
    # price_discount_value - Decimal value. If the discount ONLY is given in percentage, let the scraper calculate
    #  the actual price_discount_value
    # price_discount_start_date - if there is a start date, it is added here. Format YYYY-MM-DD.
    # price_discount_end_date - if there is an end date, it is added here. Format YYYY-MM-DD.
    # Assumption: Currency and VAT follows the values in price_ above.
    price_discount_raw = scrapy.Field()         # Optional, will not be stored in ecombooster
    price_discount_value = scrapy.Field()       # Optional
    price_discount_start_date = scrapy.Field()  # Optional
    price_discount_end_date = scrapy.Field()    # Optional

    # rrp stands for recommended retail price
    # price_rrp_raw - extracting the text from the webpage without any refinement.
    # price_rrp_value - Decimal value. Should be given excluding VAT.
    # Assumption: Currency and VAT follows the values in price_ above.
    rrp_raw = scrapy.Field()                    # Optional
    rrp_value = scrapy.Field()                  # Optional

    # A list of dicts containing relations to other products, either by SKU (1st choice) or URL (if SKU is
    # not possible), together with a classification of type of relationship. Currently supported relationships
    # are:
    # - RELATED_PRODUCT -> Product A is related to Product B
    # - UP_SELL -> Upselling is the practice of encouraging customers to purchase a comparable higher-end
    #     product than the one in question, e.g. Product B is a better (more expensive) variant compatible
    #     with Product A
    # - HAS_PARTS -> Product A has / consists of a number of parts, e.g. Product B and Product C.
    #     Mirrored by the type PART_OF
    # - PART_OF -> Product A is included in other products, e.g. Product B and Product C.
    #     Mirrored by the type HAS_PARTS
    # - RECOMMENDED_REPLACEMENT -> Product A is discountined, but Product B is defined as recommended replacement
    # - OPTIONAL_PART - Product A has one or more optional parts (Product B)
    # Example:
    #   related_products = [
    #     { 'sku': 'SKU123',
    #       'relation: 'RELATED_PRODUCT' },
    #     { 'url': 'https://example.com/product123',
    #       'relation: 'UP_SELL' }
    #   ]
    related_products = scrapy.Field()           # Optional, validation exists

    # A dict containing the type of part number (type) and the actual part number (id). This means that there could
    # be several part numbers with the same type.
    # Identifier is set as type_id
    # Example:
    #   part_numbers = {
    #     "SKU_ABC123": {
    #        "type": "SKU",
    #        "id": "ABC123" },
    #     "SKU_DEF456": {
    #        "type": "SKU",
    #        "id": "DEF456" },
    #     "EAN_7332793176529": {
    #        "type": "EAN",
    #        "id": "7332793176529" }
    #     }
    part_numbers = scrapy.Field()               # Optional, validation exists
    import_export_taric_code_eu = scrapy.Field()
    import_export_country_of_origin = scrapy.Field()                  #
    brand = scrapy.Field()
    series = scrapy.Field()
    unique_selling_points = scrapy.Field()
    model = scrapy.Field()                  #

    # TODO - Things that might be added in the future...
    # This is used for products that have a parent, e.g.
    # parent_product_sku = scrapy.Field()
    # parent_product_reference = scrapy.Field()
