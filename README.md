# The Parser

爬取某個貿易網站的商品，下載成各個渠道的商品目錄饋給。
此專案僅作於演示，實際的 API 皆已移除。

此專案使用 py37+ 執行。

```
usage: main.py [-h] [-c [concurrency]] command

Simply dump products from the website.

the command should be one of these:
  dump_category_map     to parse category map for resolve category standard id.
  dump_company_links    to parse all company links.
  dump_companies        to parse all company data from company_links data.
  dump_feeds            to parse all products from the saved companies data.

all the parsing results will be saved to the data folder.

positional arguments:
  command               command to dump data, see README.

optional arguments:
  -h, --help            show this help message and exit
  -c [concurrency], --concurrency [concurrency]
                        setup the concurrency of parsers, default is 8.
```

## 使用方式

但因為商品數量龐大，且爬取過程偏繁雜，所以將整個流程分成四個行為：

+ 下載類別地圖
+ 下載公司連結
+ 下載公司名單
+ 下載商品

可以依需求個別更新資料檔案，最終產出商品饋給。所有的下載資料皆放在 `data` 資料夾中。

#### 下載產品地圖

```
python main.py dump_category_map
```

產品地圖用來還原分類路徑，以 JSON 型式儲存以方便手動修改。**下載商品時必須要有類別地圖。**

#### 下載公司連結

```
python main.py dump_company_links
```

下載所有公司的首頁連結網址。**下載公司資訊時畢希要有連結檔案。**

#### 下載公司資訊

```
python main.py dump_companies
```

依照連結網址的檔案彙整出公司名單。**下載商品時必須要有公司名單。**

#### 下載商品

```
python main.py dump_feeds
```

依照公司名單跟分類地圖製作商品饋給。
