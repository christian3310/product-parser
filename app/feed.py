import logging
from typing import NoReturn

from app import config
from app.types import ProductType


class Feed(object):
    name: str = ''
    path: str = ''
    delimiter: str = ','
    mapping: dict = {}

    def __init__(self):
        self.logger = logging.getLogger(f'taiwantrade.feed.{self.name}')
        self.logger.addHandler(logging.FileHandler(
            filename=self.path,
            encoding='utf-8',
            mode='w'
        ))
        self.logger.setLevel(logging.INFO)
        self.logger.info(self.delimiter.join(self.mapping.keys()))
    
    def write(self, item: ProductType) -> NoReturn:
        row = self.delimiter.join(item[key] for key in self.mapping.values())
        self.logger.info(row)


class FacebookFeed(Feed):
    name = 'facebook'
    path = config.FACEBOOK_FEED
    mapping = {
        'id'                : 'id',
        'title'             : 'title',
        'description'       : 'title',
        'availability'      : 'availability',
        'condition'         : 'condition',
        'price'             : 'price',
        'link'              : 'link',
        'image_link'        : 'image_link',
        'brand'             : 'brand',
        'product_type'      : 'product_type',
        'sale_price'        : 'sale_price'
    }


class GoogleAdsFeed(Feed):
    name = 'googleads'
    path = config.GOOGLEADS_FEED
    mapping = {
        'ID'                : 'id',
        'Item title'        : 'title',
        'Final URL'         : 'link',
        'Image URL'         : 'image_link',
        'Item description'  : 'title',
        'Item Category'     : 'product_type',
        'Price'             : 'price',
        'Sale Price'        : 'sale_price'
    }


class MerchantFeed(Feed):
    name = 'merchant'
    path = config.MERCHANT_FEED
    delimiter = '\t'
    mapping = {
        'id'                : 'id',
        'title'             : 'title',
        'description'       : 'title',
        'link'              : 'link',
        'image_link'        : 'image_link',
        'availability'      : 'availability',
        'price'             : 'price',
        'sale_price'        : 'sale_price',
        'product_type'      : 'product_type',
        'brand'             : 'brand',
        'identifier_exists' : 'identifier_exists',
        'condition'         : 'condition',
        'adult'             : 'adult'
    }
