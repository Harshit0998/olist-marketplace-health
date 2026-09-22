# Data profile — raw Olist tables

## raw.category_translation — 71 rows

| column_name                   | column_type   |   null_percentage |   approx_unique | min                        | max                   |
|:------------------------------|:--------------|------------------:|----------------:|:---------------------------|:----------------------|
| product_category_name         | VARCHAR       |                 0 |              62 | agro_industria_e_comercio  | utilidades_domesticas |
| product_category_name_english | VARCHAR       |                 0 |              76 | agro_industry_and_commerce | watches_gifts         |

## raw.customers — 99,441 rows

| column_name              | column_type   |   null_percentage |   approx_unique | min                              | max                              |
|:-------------------------|:--------------|------------------:|----------------:|:---------------------------------|:---------------------------------|
| customer_id              | VARCHAR       |                 0 |          101221 | 00012a2ce6f8dcda20d059ce98491703 | ffffe8b65bbe3087b653a978c870db99 |
| customer_unique_id       | VARCHAR       |                 0 |           93296 | 0000366f3b9a7992bf8c76cfdf3221e2 | ffffd2657e2aad2907e67c3e9daecbeb |
| customer_zip_code_prefix | VARCHAR       |                 0 |           13823 | 01003                            | 99990                            |
| customer_city            | VARCHAR       |                 0 |            5024 | abadia dos dourados              | zortea                           |
| customer_state           | VARCHAR       |                 0 |              28 | AC                               | TO                               |

## raw.geolocation — 1,000,163 rows

| column_name                 | column_type   |   null_percentage |   approx_unique | min                 | max                |
|:----------------------------|:--------------|------------------:|----------------:|:--------------------|:-------------------|
| geolocation_zip_code_prefix | VARCHAR       |                 0 |           16453 | 01001               | 99990              |
| geolocation_lat             | DOUBLE        |                 0 |          883419 | -36.6053744107061   | 45.06593318269697  |
| geolocation_lng             | DOUBLE        |                 0 |          852313 | -101.46676644931476 | 121.10539381057764 |
| geolocation_city            | VARCHAR       |                 0 |            8915 | * cidade            | óleo               |
| geolocation_state           | VARCHAR       |                 0 |              28 | AC                  | TO                 |

## raw.order_items — 112,650 rows

| column_name         | column_type   |   null_percentage |   approx_unique | min                              | max                              |
|:--------------------|:--------------|------------------:|----------------:|:---------------------------------|:---------------------------------|
| order_id            | VARCHAR       |                 0 |           87618 | 00010242fe8c5a6d1ba2dd792cb16214 | fffe41c64501cc87c801fd61db3f6244 |
| order_item_id       | BIGINT        |                 0 |              21 | 1                                | 21                               |
| product_id          | VARCHAR       |                 0 |           24292 | 00066f42aeeb9f3007548bb9d3f33c38 | fffe9eeff12fcbd74a2f2b007dde0c58 |
| seller_id           | VARCHAR       |                 0 |            3886 | 0015a82c2db000af6aaaf3ae2ecb0532 | ffff564a4f9085cd26170f4732393726 |
| shipping_limit_date | TIMESTAMP     |                 0 |           80774 | 2016-09-19 00:15:34              | 2020-04-09 22:35:08              |
| price               | DOUBLE        |                 0 |            6497 | 0.85                             | 6735.0                           |
| freight_value       | DOUBLE        |                 0 |            5665 | 0.0                              | 409.68                           |

## raw.order_payments — 103,886 rows

| column_name          | column_type   |   null_percentage |   approx_unique | min                              | max                              |
|:---------------------|:--------------|------------------:|----------------:|:---------------------------------|:---------------------------------|
| order_id             | VARCHAR       |                 0 |           87618 | 00010242fe8c5a6d1ba2dd792cb16214 | fffe41c64501cc87c801fd61db3f6244 |
| payment_sequential   | BIGINT        |                 0 |              27 | 1                                | 29                               |
| payment_type         | VARCHAR       |                 0 |               5 | boleto                           | voucher                          |
| payment_installments | BIGINT        |                 0 |              25 | 0                                | 24                               |
| payment_value        | DOUBLE        |                 0 |           31557 | 0.0                              | 13664.08                         |

## raw.order_reviews — 99,224 rows

| column_name             | column_type   |   null_percentage |   approx_unique | min                              | max                                   |
|:------------------------|:--------------|------------------:|----------------:|:---------------------------------|:--------------------------------------|
| review_id               | VARCHAR       |              0    |           96866 | 0001239bc1de2e33cb583967c2ca4c67 | fffefe7a48d22f7b32046421062219d1      |
| order_id                | VARCHAR       |              0    |           87618 | 00010242fe8c5a6d1ba2dd792cb16214 | fffe41c64501cc87c801fd61db3f6244      |
| review_score            | BIGINT        |              0    |               5 | 1                                | 5                                     |
| review_comment_title    | VARCHAR       |             88.34 |            5951 |                                  | 🔟                                    |
| review_comment_message  | VARCHAR       |             58.7  |           45787 |                                  | 😡😡😡😡😡👎👎👎👎👎                  |
|                         |               |                   |                 |                                  | Empresa sem compromisso com o cliente |
| review_creation_date    | TIMESTAMP     |              0    |             585 | 2016-10-02 00:00:00              | 2018-08-31 00:00:00                   |
| review_answer_timestamp | TIMESTAMP     |              0    |          104442 | 2016-10-07 18:32:28              | 2018-10-29 12:27:35                   |

## raw.orders — 99,441 rows

| column_name                   | column_type   |   null_percentage |   approx_unique | min                              | max                              |
|:------------------------------|:--------------|------------------:|----------------:|:---------------------------------|:---------------------------------|
| order_id                      | VARCHAR       |              0    |           87618 | 00010242fe8c5a6d1ba2dd792cb16214 | fffe41c64501cc87c801fd61db3f6244 |
| customer_id                   | VARCHAR       |              0    |          101221 | 00012a2ce6f8dcda20d059ce98491703 | ffffe8b65bbe3087b653a978c870db99 |
| order_status                  | VARCHAR       |              0    |               9 | approved                         | unavailable                      |
| order_purchase_timestamp      | TIMESTAMP     |              0    |           93884 | 2016-09-04 21:15:19              | 2018-10-17 17:30:18              |
| order_approved_at             | TIMESTAMP     |              0.16 |          100122 | 2016-09-15 12:16:38              | 2018-09-03 17:40:06              |
| order_delivered_carrier_date  | TIMESTAMP     |              1.79 |           79693 | 2016-10-08 10:34:01              | 2018-09-11 19:48:28              |
| order_delivered_customer_date | TIMESTAMP     |              2.98 |           89604 | 2016-10-11 13:46:32              | 2018-10-17 13:22:46              |
| order_estimated_delivery_date | TIMESTAMP     |              0    |             440 | 2016-09-30 00:00:00              | 2018-11-12 00:00:00              |

## raw.products — 32,951 rows

| column_name                | column_type   |   null_percentage |   approx_unique | min                              | max                              |
|:---------------------------|:--------------|------------------:|----------------:|:---------------------------------|:---------------------------------|
| product_id                 | VARCHAR       |              0    |           24292 | 00066f42aeeb9f3007548bb9d3f33c38 | fffe9eeff12fcbd74a2f2b007dde0c58 |
| product_category_name      | VARCHAR       |              1.85 |              66 | agro_industria_e_comercio        | utilidades_domesticas            |
| product_name_lenght        | BIGINT        |              1.85 |              64 | 5                                | 76                               |
| product_description_lenght | BIGINT        |              1.85 |            2781 | 4                                | 3992                             |
| product_photos_qty         | BIGINT        |              1.85 |              20 | 1                                | 20                               |
| product_weight_g           | BIGINT        |              0.01 |            2155 | 0                                | 40425                            |
| product_length_cm          | BIGINT        |              0.01 |              97 | 7                                | 105                              |
| product_height_cm          | BIGINT        |              0.01 |              99 | 2                                | 105                              |
| product_width_cm           | BIGINT        |              0.01 |              92 | 6                                | 118                              |

## raw.sellers — 3,095 rows

| column_name            | column_type   |   null_percentage |   approx_unique | min                              | max                              |
|:-----------------------|:--------------|------------------:|----------------:|:---------------------------------|:---------------------------------|
| seller_id              | VARCHAR       |                 0 |            3886 | 0015a82c2db000af6aaaf3ae2ecb0532 | ffff564a4f9085cd26170f4732393726 |
| seller_zip_code_prefix | VARCHAR       |                 0 |            2547 | 01001                            | 99730                            |
| seller_city            | VARCHAR       |                 0 |             746 | 04482255                         | xaxim                            |
| seller_state           | VARCHAR       |                 0 |              24 | AC                               | SP                               |

## Targeted checks

| Check | Result |
|---|---|
| 1 orders: duplicate order_id | 0 |
| 2 customers: distinct customer_id vs distinct customer_unique_id | 3,345 |
| 3 customers: people with more than one order | 2,997 |
| 4 order_items: orphan rows (order not in orders) | 0 |
| 5 reviews: duplicate review_id | 814 |
| 6 orders with more than one review | 547 |
| 7 delivered orders with no delivery date | 8 |
| 8 delivered before purchased | 0 |
| 9 products whose category has no English name | 2 |
| 10 orders where payments differ from items + freight by more than 1 | 249 |