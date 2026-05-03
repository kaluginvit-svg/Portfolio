-- ============================================================
-- Запрос 4: Накопленная сумма продаж по каждой аптеке
-- ============================================================
-- Используемые конструкции: оконная функция SUM() OVER (PARTITION BY ... ORDER BY ...)
-- Логика: для каждой строки заказа показываем аптеку, дату, сумму заказа
-- и накопленную сумму продаж внутри этой аптеки по дате (ORDER BY report_date).
-- ============================================================

SELECT 
    pharmacy_name AS аптека,
    report_date AS дата,
    (price * count) AS сумма_заказа_руб,
    SUM(price * count) OVER (
        PARTITION BY pharmacy_name 
        ORDER BY report_date, order_id
    ) AS накопленная_сумма_руб
FROM pharma_orders
ORDER BY pharmacy_name, report_date, order_id;
