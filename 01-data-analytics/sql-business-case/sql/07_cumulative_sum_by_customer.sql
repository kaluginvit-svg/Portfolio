-- ============================================================
-- Запрос 7: Накопленная сумма по каждому клиенту
-- ============================================================
-- Используемые конструкции: JOIN, конкатенация строк (ФИО), 
-- SUM() OVER (PARTITION BY customer_id ORDER BY ...)
-- Логика: соединяем заказы и клиентов, собираем ФИО в одно поле,
-- для каждой строки заказа считаем накопленную сумму по этому клиенту.
-- ============================================================

SELECT 
    p.customer_id,
    TRIM(c.first_name || ' ' || c.last_name || ' ' || COALESCE(c.second_name, '')) AS фио,
    p.report_date AS дата_заказа,
    (p.price * p.count) AS сумма_заказа_руб,
    SUM(p.price * p.count) OVER (
        PARTITION BY p.customer_id 
        ORDER BY p.report_date, p.order_id
    ) AS накопленная_сумма_руб
FROM pharma_orders p
JOIN customers c ON p.customer_id = c.customer_id
ORDER BY p.customer_id, p.report_date, p.order_id;
