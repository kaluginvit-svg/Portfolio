-- ============================================================
-- Запрос 6: Топ-10 клиентов по сумме заказов (с ранжированием)
-- ============================================================
-- Используемые конструкции: JOIN, GROUP BY, SUM, ROW_NUMBER() OVER, подзапрос, LIMIT
-- Логика: соединяем заказы и клиентов, считаем сумму заказов по клиенту,
-- нумеруем строки по убыванию суммы (ROW_NUMBER), во внешнем запросе берём топ-10.
-- ============================================================

SELECT 
    customer_id,
    фио,
    сумма_заказов_руб,
    место
FROM (
    SELECT 
        p.customer_id,
        TRIM(c.first_name || ' ' || c.last_name || ' ' || COALESCE(c.second_name, '')) AS фио,
        SUM(p.price * p.count) AS сумма_заказов_руб,
        ROW_NUMBER() OVER (ORDER BY SUM(p.price * p.count) DESC) AS место
    FROM pharma_orders p
    JOIN customers c ON p.customer_id = c.customer_id
    GROUP BY p.customer_id, c.first_name, c.last_name, c.second_name
) ranked
WHERE место <= 10
ORDER BY место;
