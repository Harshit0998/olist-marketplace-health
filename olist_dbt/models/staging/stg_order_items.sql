with source as (
    select * from {{ source('raw', 'order_items') }}
),
renamed as (
    select
        order_id,
        order_item_id,                  -- line number within the order (1, 2, 3…)
        product_id,
        seller_id,
        shipping_limit_date             as shipping_limit_at,
        price,
        freight_value                   as freight,
        price + freight_value           as item_revenue
    from source
)
select * from renamed