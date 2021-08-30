import json
import logging
import re

from app import config
from app.types import ProductType


PRODUCT_LINK_FIX = re.compile(r'[\w\-\.]+(example)')
category_map = None


def split(l: list, chunks: int) -> list[list]:
    m, n = divmod(len(l), chunks)
    return [l[i*m+min(i, n):(i+1)*m+min(i+1, n)] for i in range(chunks)]


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f'example.{name}')
    handler = logging.FileHandler(
        filename=f'{config.LOGS_FOLDER}/{name}.log',
        encoding='utf-8'
    )
    formatter = logging.Formatter(
        '%(levelname)s:%(name)s:%(asctime)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def get_product_type(category_id: str) -> str:
    global category_map
    if not category_map:
        with open(config.CATEGORY_MAPS_FILE, 'r') as f:
            category_map = json.load(f)

    items = []
    while True:
        if item := category_map.get(category_id):
            items.append(item['name'])
            category_id = item.get('parent')
            if not category_id:
                break
        else:
            break
    
    return ' > '.join(items[::-1]) if items else 'unknown'


def convert_item(item: dict) -> ProductType:
    price = item['priceMax']
    sale_price = item['priceMin']
    return {
        'id': str(item['productId']),
        'title': item['title'],
        'link': PRODUCT_LINK_FIX.sub(r'www.\1', item['cpUrl']),
        'image_link': item['imgUrlList'],
        'availability': 'in stock',
        'price': f'{price} USD' if price else '1 USD',
        'sale_price': f'{sale_price} USD' if sale_price else '',
        'product_type': item['catalogStandardCid'],
        'brand': 'example.com',
        'identifier_exists': 'no',
        'condition': 'new',
        'adult': 'no',
        'has_price': bool(price)
    }
