with source as (
    select * from {{ source('raw', 'category_translation') }}
),
renamed as (
    select
        product_category_name           as category_pt,
        product_category_name_english   as category_en
    from source
)
select * from renamed