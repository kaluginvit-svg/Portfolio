-- ============================================================
-- RECIPES_QUERIES.SQL - ПРОВЕРОЧНЫЕ ЗАПРОСЫ
-- ============================================================
-- Запросы для проверки работы связи many-to-many
-- ============================================================

-- 1. Показать все рецепты с их продуктами
SELECT 
    r.name AS recipe_name,
    p.name AS product_name,
    rp.quantity,
    p.unit
FROM recipes r
JOIN recipe_products rp ON r.id = rp.recipe_id
JOIN products p ON rp.product_id = p.id
ORDER BY r.name, p.name;

-- 2. Показать все продукты, которые используются в рецепте "Борщ"
SELECT 
    p.name AS product_name,
    rp.quantity,
    p.unit
FROM products p
JOIN recipe_products rp ON p.id = rp.product_id
JOIN recipes r ON rp.recipe_id = r.id
WHERE r.name = 'Борщ'
ORDER BY p.name;

-- 3. Показать все рецепты, в которых используется продукт "Мука"
SELECT 
    r.name AS recipe_name,
    r.description,
    rp.quantity,
    p.unit
FROM recipes r
JOIN recipe_products rp ON r.id = rp.recipe_id
JOIN products p ON rp.product_id = p.id
WHERE p.name = 'Мука'
ORDER BY r.name;

-- 4. Подсчитать количество продуктов в каждом рецепте
SELECT 
    r.name AS recipe_name,
    COUNT(rp.product_id) AS products_count
FROM recipes r
LEFT JOIN recipe_products rp ON r.id = rp.recipe_id
GROUP BY r.id, r.name
ORDER BY products_count DESC;

-- 5. Показать рецепты, которые используют больше всего продуктов
SELECT 
    r.name AS recipe_name,
    COUNT(rp.product_id) AS products_count
FROM recipes r
JOIN recipe_products rp ON r.id = rp.recipe_id
GROUP BY r.id, r.name
HAVING COUNT(rp.product_id) >= 7
ORDER BY products_count DESC;

-- 6. Показать все продукты и количество рецептов, в которых они используются
SELECT 
    p.name AS product_name,
    COUNT(rp.recipe_id) AS recipes_count
FROM products p
LEFT JOIN recipe_products rp ON p.id = rp.product_id
GROUP BY p.id, p.name
ORDER BY recipes_count DESC, p.name;

-- 7. Показать рецепты с общим количеством ингредиентов (сумма всех количеств)
SELECT 
    r.name AS recipe_name,
    SUM(rp.quantity) AS total_quantity
FROM recipes r
JOIN recipe_products rp ON r.id = rp.recipe_id
GROUP BY r.id, r.name
ORDER BY total_quantity DESC;

-- 8. Найти продукты, которые используются во всех рецептах (или в большинстве)
SELECT 
    p.name AS product_name,
    COUNT(DISTINCT rp.recipe_id) AS recipes_count,
    (SELECT COUNT(*) FROM recipes) AS total_recipes
FROM products p
JOIN recipe_products rp ON p.id = rp.product_id
GROUP BY p.id, p.name
HAVING COUNT(DISTINCT rp.recipe_id) >= 3
ORDER BY recipes_count DESC;

-- 9. Показать полную информацию о рецепте "Блины"
SELECT 
    r.name AS recipe_name,
    r.description,
    r.cooking_time || ' минут' AS cooking_time,
    r.servings || ' порций' AS servings,
    p.name AS product_name,
    rp.quantity || ' ' || p.unit AS amount
FROM recipes r
JOIN recipe_products rp ON r.id = rp.recipe_id
JOIN products p ON rp.product_id = p.id
WHERE r.name = 'Блины'
ORDER BY p.name;

-- 10. Найти рецепты, которые можно приготовить, имея только определенные продукты
-- (например, если есть только: Мука, Яйца, Молоко, Сахар, Масло сливочное, Соль)
SELECT DISTINCT
    r.name AS recipe_name,
    r.description
FROM recipes r
WHERE NOT EXISTS (
    SELECT 1
    FROM recipe_products rp
    JOIN products p ON rp.product_id = p.id
    WHERE rp.recipe_id = r.id
    AND p.name NOT IN ('Мука', 'Яйца', 'Молоко', 'Сахар', 'Масло сливочное', 'Соль')
);

-- ============================================================
-- КОНЕЦ RECIPES_QUERIES.SQL
-- ============================================================
