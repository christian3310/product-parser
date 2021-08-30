import pathlib

ROOT = pathlib.Path()

DATA_FOLDER = ROOT.joinpath('data')
CATEGORY_MAPS_FILE = DATA_FOLDER.joinpath('category_map.json')
COMPANY_LINKS_FILE = DATA_FOLDER.joinpath('company_links.pkl')
COMPANIES_FILE = DATA_FOLDER.joinpath('companies.pkl')
FACEBOOK_FEED = DATA_FOLDER.joinpath('facebook.csv')
GOOGLEADS_FEED = DATA_FOLDER.joinpath('googleads.csv')
MERCHANT_FEED = DATA_FOLDER.joinpath('merchant.tsv')

LOGS_FOLDER = ROOT.joinpath('logs')
