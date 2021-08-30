import asyncio
import json
import pickle
from typing import NoReturn

from app import config
from app.feed import FacebookFeed, GoogleAdsFeed, MerchantFeed
from app.parser import Parser
from app.utils import get_logger, split


logger = get_logger('main')


async def dump_category_map(concurrency: int = 8) -> NoReturn:
    logger.info(f'start to dump category map')

    parser = Parser()
    sub_category_links = await parser.parse_sub_categories()
    parsers = [Parser() for _ in range(concurrency)]
    chunks = split(sub_category_links, concurrency)
    results = await asyncio.gather(
        *[parser.batch_parse_category_map(links) for parser, links in zip(parsers, chunks)]
    )
    category_map = {}
    for result in results:
        category_map.update(result)
    
    with open(config.CATEGORY_MAPS_FILE, 'w') as f:
        json.dump(category_map, f, indent=4, sort_keys=True)
    
    logger.info(f'finished')


async def dump_company_links(concurrency: int = 8) -> NoReturn:
    logger.info(f'start to dump company links.')

    parser = Parser()
    category_ids = await parser.parse_category_ids()
    logger.info(f'collect {len(category_ids)} category ids')

    parsers = [Parser() for _ in range(concurrency)]
    chunks = split(category_ids, concurrency)
    results = await asyncio.gather(
        *[parser.batch_parse_company_links(ids) for parser, ids in zip(parsers, chunks)]
    )
    links = set()
    for result in results:
        links.update(result)
    
    with open(config.COMPANY_LINKS_FILE, 'wb') as f:
        pickle.dump(links, f)
    
    logger.info(f'finished.')


async def dump_companies(concurrency: int = 8) -> NoReturn:
    logger.info(f'start to dump company data.')

    try:
        f = open(config.COMPANY_LINKS_FILE, 'rb')
    except FileNotFoundError:
        logger.error('company links file was not found, please dump the file first.')
        return
    else:
        company_links = list(pickle.load(f))
        f.close()
        parsers = [Parser() for _ in range(concurrency)]
        chunks = split(company_links, concurrency)
        results = await asyncio.gather(
            *[parser.batch_parse_company(links) for parser, links in zip(parsers, chunks)]
        )
        companies = []
        for result in results:
            companies.extend(result)
        
        with open(config.COMPANIES_FILE, 'wb') as f:
            pickle.dump(companies, f)
        
        logger.info(f'finished.')


async def dump_feeds(concurrency: int = 8) -> NoReturn:
    logger.info(f'start to dump feeds.')

    try:
        f = open(config.COMPANIES_FILE, 'rb')
    except FileNotFoundError:
        logger.error('companies file was not found, please dump the file first.')
        return
    else:
        companies = pickle.load(f)
        f.close()
        parsers = [Parser() for _ in range(concurrency)]
        chunks = split(companies, concurrency)
        queue = asyncio.Queue()
        _ = [
            asyncio.create_task(parser.parse_product_worker(chunk, queue))
            for parser, chunk in zip(parsers, chunks)
        ]

        facebook = FacebookFeed()
        googleads = GoogleAdsFeed()
        merchant = MerchantFeed()
        uncompleted_tasks = concurrency
        while uncompleted_tasks > 0:
            item = await queue.get()
            if item is None:
                uncompleted_tasks -= 1
                queue.task_done()
                continue
            else:
                facebook.write(item)
                googleads.write(item)
                if item['has_price']:
                    merchant.write(item)
                queue.task_done()

        logger.info(f'finished.')

