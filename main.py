import asyncio
import argparse

from app import main


COMMANDS = [
    'dump_category_map',
    'dump_company_links',
    'dump_companies',
    'dump_feeds'
]
HELPS = '''
Simply dump products from the website.

the command should be one of these:
  dump_category_map     to parse category map for resolve category standard id.
  dump_company_links    to parse all company links.
  dump_companies        to parse all company data from company_links data.
  dump_feeds            to parse all products from the saved companies data.

all the parsing results will be saved to the data folder.
'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=HELPS)
    parser.add_argument('cmd', metavar='command', nargs=1, type=str, choices=COMMANDS, help='command to dump data, see README.')
    parser.add_argument('-c', '--concurrency', metavar='concurrency', nargs='?', type=int, default=8, help='setup the concurrency of parsers, default is 8.')
    args = parser.parse_args()
    func = getattr(main, args.cmd[0])
    asyncio.run(func(args.concurrency))
