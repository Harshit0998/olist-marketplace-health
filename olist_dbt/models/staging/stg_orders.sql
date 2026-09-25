with source as (

    select * from {{ source('raw', 'orders') }}

),

renamed as (

    select
        order_id,
        customer_id,
        order_status,
        order_purchase_timestamp                                as purchased_at,
        order_approved_at                                       as approved_at,
        order_delivered_carrier_date                            as shipped_at,
        order_delivered_customer_date                           as delivered_at,
        order_estimated_delivery_date                           as estimated_delivery_at,

        order_delivered_customer_date > estimated_delivery_at   as is_late,
        
        date_diff('day', order_purchase_timestamp,
                         order_delivered_customer_date)         as delivery_days,

        date_diff('day', order_estimated_delivery_date,
                         order_delivered_customer_date)         as delay_days

    from source

)

select * from renamed