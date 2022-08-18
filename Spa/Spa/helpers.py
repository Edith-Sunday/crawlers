# This file contains a bunch of helpers that are common for more than one spider...

import json
from time import sleep
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


def custom_request_delay(spider):
    spider.no_of_requests += 1

    try:
        custom_delay_rules = spider.custom_delay_rules
    except Exception:
        custom_delay_rules = {
            # Example: After 500 requests, do a paus for 180 seconds and so forth
            500: 180,
            200: 90,
            50: 30,
            20: 10,
            5: 1,
        }

    for count, sleep_seconds in custom_delay_rules.items():
        if spider.no_of_requests % count == 0:
            spider.logger.debug(f'Done {spider.no_of_requests} requests, pausing for {sleep_seconds} seconds...')
            sleep(sleep_seconds)
            continue


def log_error(spider, error, severity='ERROR', classification='UNDEFINED'):
    try:
        if classification not in spider.error_log:
            spider.error_log[classification] = {}
        if severity not in spider.error_log[classification]:
            spider.error_log[classification][severity] = []
        spider.error_log[classification][severity].append(error)
        spider.logger.error(error)
    except Exception as err:
        spider.logger.error(f'Failed to write error message: {error} due to {err}')