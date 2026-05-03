-- ============================================================
-- Запрос 8: Топ-10 самых частых клиентов аптек Горздрав и Здравсити (объединение)
-- ============================================================
-- Используемые конструкции: WITH (CTE), JOIN, GROUP BY, ROW_NUMBER, подзапрос, UNION
-- Логика:
--   a) Две временные таблицы: заказы Горздрав и Здравсити с JOIN к клиентам.
--   b) В каждой считаем по клиенту количество заказов, ранжируем (топ-10).
--   c) UNION объединяет два набора: столбцы (аптека, клиент, кол_заказов, место).
-- ============================================================

WITH gorzdrav_orders AS (
    SELECT 
        p.customer_id,
        TRIM(c.first_name || ' ' || c.last_name || ' ' || COALESCE(c.second_name, '')) AS фио,
        COUNT(*) AS кол_заказов
    FROM pharma_orders p
    JOIN customers c ON p.customer_id = c.customer_id
    WHERE p.pharmacy_name = 'Горздрав'
    GROUP BY p.customer_id, c.first_name, c.last_name, c.second_name
),
gorzdrav_top AS (
    SELECT 
        'Горздрав' AS аптека,
        фио,
        кол_заказов,
        ROW_NUMBER() OVER (ORDER BY кол_заказов DESC) AS место
    FROM gorzdrav_orders
),
zdravcity_orders AS (
    SELECT 
        p.customer_id,
        TRIM(c.first_name || ' ' || c.last_name || ' ' || COALESCE(c.second_name, '')) AS фио,
        COUNT(*) AS кол_заказов
    FROM pharma_orders p
    JOIN customers c ON p.customer_id = c.customer_id
    WHERE p.pharmacy_name = 'Здравсити'
    GROUP BY p.customer_id, c.first_name, c.last_name, c.second_name
),
zdravcity_top AS (
    SELECT 
        'Здравсити' AS аптека,
        фио,
        кол_заказов,
        ROW_NUMBER() OVER (ORDER BY кол_заказов DESC) AS место
    FROM zdravcity_orders
)
SELECT аптека, фио, кол_заказов, место
FROM (
    SELECT * FROM gorzdrav_top WHERE место <= 10
    UNION ALL
    SELECT * FROM zdravcity_top WHERE место <= 10
)
ORDER BY аптека, место;
