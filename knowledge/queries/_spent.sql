-- raw sql results do not include filled-in values for 'day_level_db_purchase_spent.rec_updated_at_new_date'


WITH day_level_db_purchase_spent AS (with s1 as(select
                        date_trunc('day',(rec_updated_at + interval'330'minute))  as rec_updated_at_new,
                  count(distinct case when sportan_id is  null then customer_id end ) as public_users,
                            sum(case when sportan_id is  null then transaction_amount end) as public_db_spent
                        from (select a.*,b.userid as sportan_id from d11_transactions.dreambucks_account_ledger as a left join
                        (select userid from d11_stitch.sportan_userid_new) as b on a.customer_id = cast(b.userid as varchar))
                        where lower(transaction_type) = 'debit'
                        and date(rec_updated_at + interval'330'minute)   >=  date('2025-12-04')
                        group by 1
                        order by 1),
      s2 as (select date(rec_updated_at + interval'330'minute) as account_date, count(Distinct customer_id) as customers, sum(transaction_amount) as db_purchased from
      (select b.userid as sportan_id, a.* from
      (select * from d11_transactions.dreambucks_account_ledger
      where lower(transaction_type) = 'credit' and date(rec_updated_at + interval'330'minute)   >=  date('2025-12-04') and source_id = 3)
      as a
      left join
      d11_stitch.sportan_userid_new
      as b
       on cast(a.customer_id as varchar) = cast(b.userid as varchar))
       where  date(rec_updated_at + interval'330'minute)>= date('2025-12-04') and meta not in ('{"description": "DreamCoins converted to DreamBucks"}') and sportan_id is null
       group by 1)
       select cast(s1.rec_updated_at_new as timestamp) rec_updated_at_new,s1.public_users,s1.public_db_spent,s2.customers,s2.db_purchased
       from s1
       left join s2 on s1.rec_updated_at_new = s2.account_date )
SELECT
    (DATE_FORMAT((day_level_db_purchase_spent.rec_updated_at_new  AT TIME ZONE 'Asia/Kolkata'), '%Y-%m-%d')) AS "day_level_db_purchase_spent.rec_updated_at_new_date",
    COALESCE(SUM(CAST( day_level_db_purchase_spent.public_db_spent   AS DOUBLE)), 0) AS "total_db_spent",
    COALESCE(SUM(CAST( day_level_db_purchase_spent.db_purchased   AS DOUBLE)), 0) AS "total_db_purchased"
FROM day_level_db_purchase_spent
WHERE (day_level_db_purchase_spent.rec_updated_at_new ) >= ((CAST(CAST((FORMAT_DATETIME(DATE_ADD('day', -7, CAST(CAST(DATE_TRUNC('DAY', (NOW() AT TIME ZONE 'Asia/Kolkata')) AS DATE) AS TIMESTAMP)), 'yyyy-MM-dd HH:mm:ss.SSS') || ' Asia/Kolkata') AS TIMESTAMP WITH TIME ZONE) AT TIME ZONE 'UTC' AS TIMESTAMP)))
GROUP BY
    1
ORDER BY
    1 DESC
LIMIT 500