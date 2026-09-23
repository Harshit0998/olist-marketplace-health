with source as (
    select * from {{ source('raw', 'customers') }}
),
renamed as (
    select
        customer_id,                    -- one per ORDER
        customer_unique_id,             -- one per PERSON
        customer_zip_code_prefix        as zip_prefix,
        customer_city                   as city,
        customer_state                  as state
    from source
)
select * from renamed