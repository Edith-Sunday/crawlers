# This file contains a bunch of helpers that are common for more than one spider...

import json
error_log = []

def fetch_ecombooster_credentials():
    try:
        with open('credentials.json') as f:
            data = json.load(f)

        url = data['ecombooster']['url']
        username = data['ecombooster']['username']
        password = data['ecombooster']['password']
    except Exception as err:
        print(f'FAILED to fetch credentials for ecombooster! {err}')
        raise err

    return url, username, password


def log_error(self, error):
    self.logger.error(error)


def fetch_spider_credentials(spider):
    try:
        with open('credentials.json') as f:
            data = json.load(f)

        username = data['scrapers'][spider]['username']
        password = data['scrapers'][spider]['password']
    except Exception as err:
        print(f'FAILED to fetch credentials for spider {spider}! {err}')
        raise err

    return username, password


# def logged_in(find_what, in_text, ):
#     if find_what not in in_text:
#         print('ERROR NOT LOGGED IN')
#         # open_in_browser(response)
#         self.login_failures += 1
#         if self.login_failures > 10:
#             print('ABORTING! Reached 10 pages where login check failed!')
#             exit()
#         return False
#     return True


# def create_webdriver(self):
#     """
#     Used to create a chrome driver for downloading pages...
#     :return: selenium.webdriver.Chrome object
#     """
#     # Creating Chrome Window
#     path_to_driver = 'C:/Users/tobbe/Documents/git-repos/scrapy_villaspa_se/villaspa_se/chromedriver.exe'
#     chrome_options = Options()
#     chrome_options.add_argument("--disable-notifications")
#     try:
#         driver = webdriver.Chrome(path_to_driver, options=chrome_options)
#         self.logger.info('Webdriver initiated...')
#     except Exception as err:
#         self.logger.error('Could not initiate webdriver the normal way...')
#         self.logger.exception(err)
#         driver = webdriver.Chrome(options=chrome_options)
#
#     sleep(1)
#     return driver


# def split_label_and_price(label):
#     # Split text like "With unions (+4,69€ HT)" into components: Label and Priceimpact
#
#     price_impact_text = None
#     price_impact_decimal = 0
#     if '(' in label and '€' in label and 'HT' in label:
#         price_impact_text = label[label.find('(') + 1:]
#         label = label[:label.find('(')].strip()
#         price_impact_text = price_impact_text.replace(')', '').strip()
#         price_impact_decimal = price_impact_text
#         try:
#             price_impact_decimal = price_impact_decimal.replace('€ HT', '')
#             price_impact_decimal = price_impact_decimal.replace(',', '.')
#             price_impact_decimal = Decimal(price_impact_decimal)
#         except InvalidOperation as err:
#             raise InvalidOperation(f'Failed to convert "{price_impact_decimal}" to Decimal!\n{err}')
#
#     return label, price_impact_text, price_impact_decimal
