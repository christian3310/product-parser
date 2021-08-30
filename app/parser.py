import asyncio
import json
import re
from typing import Set

import httpx
from lxml import html

from app.types import CategoryMapItemType, CompanyType, ProductType
from app.utils import convert_item, get_product_type, get_logger


CATEGORY_VIEW = 'CATEGROY_VIEW_LINK'
CATEGORY_SITEMAP = 'CATEGORY_SITEMAP_LINK'
CATEGORY_LINK = 'CATEGROY_LINK?PAGE={page}&CATE={cate}'
CATEGORY_ID_SEARCH = re.compile(r'cate_standard=(\d+)$')
COMPANY_HREF_SEARCH = re.compile(r'company_name"\shref="([^"]+)"')
COMPANY_LINK_PATTERN = re.compile(r'-(\d+)\.html$')
COMPANY_ID_SEARCH = re.compile(r'name="CompanyID"\scontent="(\d+)"')
COMPANY_NAME_SEARCH = re.compile(r'name="CompanyName"\scontent="([^"]+)"')
PRODUCTS_API = 'PRODUCT_API?COMPANYID={company_id}&START={start}&END={end}'
PRODUCT_LINK_FIX = re.compile(r'[\w\-\.]+(example)')


logger = get_logger('parser')
req_logger = get_logger('request')


class Parser(object):
    async def fetch(self, link):
        for _ in range(8):
            req_logger.info(f'fetch {link}')
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.get(link, timeout=30)
                except (httpx.ConnectError, httpx.ReadError):
                    req_logger.error(f'request {link} failed')
                    await asyncio.sleep(5)
                except (httpx.ConnectTimeout, httpx.ReadTimeout):
                    req_logger.error(f'request {link} time out')
                    await asyncio.sleep(5)
                else:
                    if resp.status_code != 200:
                        req_logger.warn(f'got resp {resp.status_code} on {link}')
                        await asyncio.sleep(10)
                    else:
                        return resp
        
        raise RuntimeError(f'request {link} failed')
    
    async def parse_category_ids(self) -> list[str]:
        resp = await self.fetch(CATEGORY_SITEMAP)
        return re.findall(r'(\d+)-cateSupplier', resp.content.decode())
    
    async def parse_company_links(self, category_id: str) -> Set[str]:
        logger.info(f'parse category {category_id}')
        results = set()
        page = 1
        while True:
            link = CATEGORY_LINK.format(cate=category_id, page=page)
            try:
                resp = await self.fetch(link)
            except RuntimeError:
                page += 1
            else:
                resp_body = resp.content.decode()
                if links := COMPANY_HREF_SEARCH.findall(resp_body):
                    results.update(set(links))
                    page += 1
                else:
                    break

        return results
    
    async def batch_parse_company_links(self, category_ids: list[str]) -> Set[str]:
        logger.info(f'parse {len(category_ids)} categories')
        results = set()
        for category_id in category_ids:
            links = await self.parse_company_links(category_id)
            logger.info(f'get {len(links)} links')
            results.update(links)
        
        return results
    
    async def parse_company(self, company_link: str) -> CompanyType:
        if matched := COMPANY_LINK_PATTERN.search(company_link):
            name = COMPANY_LINK_PATTERN.sub('', company_link).split('/')[-1]
            return {
                'id': matched.group(1),
                'link': company_link,
                'name': ' '.join(map(str.capitalize, name.split('-')))
            }
        else:
            resp = await self.fetch(company_link)
            resp_body = resp.content.decode()
            company_id = COMPANY_ID_SEARCH.findall(resp_body)
            if not company_id:
                logger.error(f'company {company_link} does not have company_id')
                return None
            else:
                return {
                    'id': company_id[0],
                    'link': company_link,
                    'name': COMPANY_NAME_SEARCH.findall(resp_body)[0]
                }
    
    async def batch_parse_company(self, company_links: list[str]) -> list[CompanyType]:
        companies = []
        for link in company_links:
            if company := await self.parse_company(link):
                companies.append(company)

        return companies

    async def parse_products(self, company_id: str) -> list[ProductType]:
        logger.info(f'parse products from company {company_id}')
        step = 500
        items = []
        for i in range(5):
            link = PRODUCTS_API.format(
                company_id=company_id,
                start=i*step+1,
                end=(i+1)*step
            )
            try:
                resp = await self.fetch(link)
                result = json.loads(resp.content.decode())
            except RuntimeError:
                break
            except json.JSONDecodeError:
                logger.error(f'decode company {company_id} products failed')
                break
            else:
                for item in result['rows']:
                    items.append(convert_item(item))
                if len(result['rows']) < 500:
                    break

        return items 

    async def parse_product_worker(self, companies: list[CompanyType], out_q: asyncio.Queue):
        for company in companies:
            items = await self.parse_products(company['id'])
            for item in items:
                item['brand'] = company['name']
                item['product_type'] = get_product_type(item['product_type'])
                out_q.put_nowait(item)

            await asyncio.sleep(1)
        
        out_q.put_nowait(None)

    async def parse_sub_categories(self) -> list[str]:
        resp = await self.fetch(CATEGORY_VIEW)
        document = html.document_fromstring(resp.content.decode())
        anchors = document.cssselect('a.link')
        return [
            f'https://www.example.com{a.attrib.get("href")}'
            for a in anchors[2:]
        ]
    
    async def parse_category_map(self, category_link: str) -> dict[str, CategoryMapItemType]:
        logger.info(f'parse {category_link}')
        resp = await self.fetch(category_link)
        document = html.document_fromstring(resp.content.decode())
        results = {}
        if items := document.cssselect('a.column_list_txt'):
            resp = await self.fetch(items[0].attrib.get('href'))
            document = html.document_fromstring(resp.content.decode())
            if breadcrumb := document.cssselect('a[itemprop="item"]'):
                rb = breadcrumb[::-1]
                for category, parent in zip(rb, rb[1:]):
                    link = category.attrib.get('href')
                    parent_link = parent.attrib.get('href')
                    if search := CATEGORY_ID_SEARCH.search(link):
                        parent_id = CATEGORY_ID_SEARCH.search(parent_link)
                        results[search.group(1)] = {
                            'name': category.getchildren()[0].text,
                            'parent': parent_id.group(1) if parent_id else '0'
                        }
        else:
            logger.warn(f'caegory {category_link} does not have products')

        return results

    async def batch_parse_category_map(self, category_links: list[str]) -> dict[str, CategoryMapItemType]:
        category_map = {'0': {'name': 'Home'}}
        for category_link in category_links:
            try:
                sub_map = await self.parse_category_map(category_link)
            except Exception as e:
                logger.error(f'parse {category_link} failed')
                logger.exception(e)
            else:
                category_map.update(sub_map)
            finally:
                await asyncio.sleep(2)

        return category_map
