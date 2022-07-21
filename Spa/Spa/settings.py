# Scrapy settings for scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'Spa'

SPIDER_MODULES = ['Spa.spiders']
NEWSPIDER_MODULE = 'Spa.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = ''

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'Spa.middlewares.SpaSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'Spa.middlewares.SpaDownloaderMiddleware': 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# # }

AWS_ACCESS_KEY_ID = 'AKIAXRKWTUSZ24PT6IXQ'
AWS_SECRET_ACCESS_KEY = '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'
IMAGES_STORE = f's3://ecombooster-scraped-files/{BOT_NAME}/scraped_images/'
FILES_STORE = f's3://ecombooster-scraped-files/{BOT_NAME}/scraped_files/'
IMAGES_STORE_S3_ACL = 'public-read'
FILES_STORE_S3_ACL = 'public-read'

IMAGES_STORE_LOCAL = f'scraped_images/'
FILES_STORE_LOCAL = f'scraped_files/'

IMAGES_THUMBS = {
    'small': (128, 128),
    'medium': (256, 256),
    'large': (512, 512),
}
IMAGES_MIN_HEIGHT = 150
IMAGES_MIN_WIDTH = 150
MEDIA_ALLOW_REDIRECTS = True

# Configure item pipelines
ITEM_PIPELINES = {
    'Spa.pipelines.MyImagesPipeline': 1,
    'Spa.pipelines.MyFilesPipeline': 1,
    # 'scraper.pipelines.MyLocalImagesPipeline': 2,
    # 'scraper.pipelines.MyLocalFilesPipeline': 2,
    'Spa.pipelines.SpaPipeline': 300,
}


#  Enable and configure the AutoThrottle extension (disabled by default)
#  See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
#  The initial download delay
AUTOTHROTTLE_START_DELAY = 5
#  The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
#  The average number of requests Scrapy should be sending in parallel to
#  each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.5
#  Enable showing throttling stats for every response received:
#  AUTOTHROTTLE_DEBUG = False

#  Enable and configure HTTP caching (disabled by default)
#  See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTP_ALLOW_ERROR_CODES = [401]
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600 * 12
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
