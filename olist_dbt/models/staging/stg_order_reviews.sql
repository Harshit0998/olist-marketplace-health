with source as (
    select * from {{ source('raw', 'order_reviews') }}
),
ranked as (
    select
        review_id,
        order_id,
        review_score,
        review_creation_date            as created_at,
        review_answer_timestamp         as answered_at,
        row_number() over(partition by order_id order by review_answer_timestamp desc, order_id) as rn

    from source
),
deduplicated as (
    select review_id, order_id, review_score, created_at, answered_at
    from ranked
    where rn = 1
)
select * from deduplicated