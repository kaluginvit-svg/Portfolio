-- ============================================================
-- SQL-ЗАПРОСЫ ДЛЯ БАЗЫ ДАННЫХ СПОРТИВНОГО КЛУБА
-- ============================================================

-- 1. Кто сейчас имеет активный абонемент
-- (участники с оплаченным абонементом, период которого еще не истек)
-- ============================================================
SELECT 
    m.id,
    m.first_name || ' ' || m.last_name AS member_name,
    m.email,
    m.phone,
    p.amount AS payment_amount,
    p.period_start,
    p.period_end,
    p.payment_method,
    CASE 
        WHEN date(p.period_end) >= date('now') THEN 'Активен'
        ELSE 'Истек'
    END AS subscription_status
FROM members m
JOIN payments p ON m.id = p.member_id
WHERE p.status = 'Оплачено'
  AND date(p.period_end) >= date('now')
ORDER BY p.period_end DESC;


-- 2. Сколько людей записано на занятия по датам
-- (количество уникальных участников, записанных на каждую дату)
-- ============================================================
SELECT 
    v.visit_date,
    COUNT(DISTINCT v.member_id) AS unique_members_count,
    COUNT(v.id) AS total_visits,
    COUNT(CASE WHEN v.status = 'Посещено' THEN 1 END) AS visited_count,
    COUNT(CASE WHEN v.status = 'Пропущено' THEN 1 END) AS missed_count
FROM visits v
GROUP BY v.visit_date
ORDER BY v.visit_date DESC;


-- 3. Список тренеров и какие у них классы
-- (полная информация о тренерах и их занятиях)
-- ============================================================
SELECT 
    t.id AS trainer_id,
    t.first_name || ' ' || t.last_name AS trainer_name,
    t.specialization,
    t.experience_years,
    c.id AS class_id,
    c.name AS class_name,
    c.day_of_week,
    c.start_time,
    c.duration_minutes,
    c.max_participants,
    c.room,
    COUNT(DISTINCT v.member_id) AS enrolled_members
FROM trainers t
LEFT JOIN classes c ON t.id = c.trainer_id
LEFT JOIN visits v ON c.id = v.class_id AND v.status = 'Посещено'
GROUP BY t.id, t.first_name, t.last_name, t.specialization, t.experience_years,
         c.id, c.name, c.day_of_week, c.start_time, c.duration_minutes, 
         c.max_participants, c.room
ORDER BY t.last_name, t.first_name, c.day_of_week, c.start_time;


-- 4. Участники, которые давно не посещали клуб
-- (участники, которые не посещали занятия более 30 дней)
-- ============================================================
SELECT 
    m.id,
    m.first_name || ' ' || m.last_name AS member_name,
    m.email,
    m.phone,
    m.status AS member_status,
    MAX(v.visit_date) AS last_visit_date,
    CAST(julianday('now') - julianday(MAX(v.visit_date)) AS INTEGER) AS days_since_last_visit
FROM members m
LEFT JOIN visits v ON m.id = v.member_id AND v.status = 'Посещено'
WHERE m.status = 'Активный'
GROUP BY m.id, m.first_name, m.last_name, m.email, m.phone, m.status
HAVING MAX(v.visit_date) IS NULL 
    OR CAST(julianday('now') - julianday(MAX(v.visit_date)) AS INTEGER) > 30
ORDER BY days_since_last_visit DESC NULLS LAST;


-- 5. Топ-3 самых популярных занятий
-- (занятия с наибольшим количеством посещений)
-- ============================================================
SELECT 
    c.id,
    c.name AS class_name,
    t.first_name || ' ' || t.last_name AS trainer_name,
    c.day_of_week,
    c.start_time,
    COUNT(v.id) AS total_visits,
    COUNT(DISTINCT v.member_id) AS unique_members,
    c.max_participants,
    ROUND(COUNT(DISTINCT v.member_id) * 100.0 / c.max_participants, 1) AS occupancy_percent
FROM classes c
JOIN trainers t ON c.trainer_id = t.id
LEFT JOIN visits v ON c.id = v.class_id AND v.status = 'Посещено'
GROUP BY c.id, c.name, t.first_name, t.last_name, c.day_of_week, c.start_time, c.max_participants
ORDER BY total_visits DESC
LIMIT 3;


-- 6. Сколько клуб заработал по видам абонементов (сумма платежа)
-- (статистика доходов по сумме платежей)
-- ============================================================
SELECT 
    CASE 
        WHEN p.amount < 3500 THEN 'Базовый (до 3500 руб.)'
        WHEN p.amount < 4500 THEN 'Стандартный (3500-4500 руб.)'
        WHEN p.amount < 5500 THEN 'Премиум (4500-5500 руб.)'
        ELSE 'VIP (5500+ руб.)'
    END AS subscription_type,
    COUNT(*) AS subscriptions_count,
    SUM(p.amount) AS total_revenue,
    AVG(p.amount) AS avg_amount,
    MIN(p.amount) AS min_amount,
    MAX(p.amount) AS max_amount
FROM payments p
WHERE p.status = 'Оплачено'
GROUP BY subscription_type
ORDER BY total_revenue DESC;


-- 7. Конфликты в расписании (когда у одного человека пересекаются занятия)
-- (участники, которые записаны на занятия, которые пересекаются по времени)
-- ============================================================
SELECT DISTINCT
    m.id AS member_id,
    m.first_name || ' ' || m.last_name AS member_name,
    v1.visit_date,
    c1.name AS class1_name,
    c1.start_time AS class1_start,
    c1.duration_minutes AS class1_duration,
    TIME(c1.start_time, '+' || c1.duration_minutes || ' minutes') AS class1_end,
    c2.name AS class2_name,
    c2.start_time AS class2_start,
    c2.duration_minutes AS class2_duration,
    TIME(c2.start_time, '+' || c2.duration_minutes || ' minutes') AS class2_end
FROM members m
JOIN visits v1 ON m.id = v1.member_id
JOIN classes c1 ON v1.class_id = c1.id
JOIN visits v2 ON m.id = v2.member_id AND v1.visit_date = v2.visit_date AND v1.id != v2.id
JOIN classes c2 ON v2.class_id = c2.id
WHERE v1.status = 'Посещено' 
  AND v2.status = 'Посещено'
  AND (
      -- Класс 2 начинается во время класса 1
      (c2.start_time >= c1.start_time AND c2.start_time < TIME(c1.start_time, '+' || c1.duration_minutes || ' minutes'))
      OR
      -- Класс 1 начинается во время класса 2
      (c1.start_time >= c2.start_time AND c1.start_time < TIME(c2.start_time, '+' || c2.duration_minutes || ' minutes'))
  )
ORDER BY m.last_name, m.first_name, v1.visit_date, c1.start_time;


-- 8. Дополнительный запрос: Статистика посещаемости по дням недели
-- (анализ популярности дней недели для занятий)
-- ============================================================
SELECT 
    c.day_of_week,
    COUNT(DISTINCT c.id) AS total_classes,
    COUNT(v.id) AS total_visits,
    COUNT(DISTINCT v.member_id) AS unique_visitors,
    COUNT(CASE WHEN v.status = 'Посещено' THEN 1 END) AS successful_visits,
    COUNT(CASE WHEN v.status = 'Пропущено' THEN 1 END) AS missed_visits,
    ROUND(COUNT(CASE WHEN v.status = 'Посещено' THEN 1 END) * 100.0 / COUNT(v.id), 1) AS attendance_rate
FROM classes c
LEFT JOIN visits v ON c.id = v.class_id
GROUP BY c.day_of_week
ORDER BY 
    CASE c.day_of_week
        WHEN 'Понедельник' THEN 1
        WHEN 'Вторник' THEN 2
        WHEN 'Среда' THEN 3
        WHEN 'Четверг' THEN 4
        WHEN 'Пятница' THEN 5
        WHEN 'Суббота' THEN 6
        WHEN 'Воскресенье' THEN 7
    END;


-- 9. Дополнительный запрос: Участники с истекающими абонементами (в течение 7 дней)
-- (для напоминаний о продлении)
-- ============================================================
SELECT 
    m.id,
    m.first_name || ' ' || m.last_name AS member_name,
    m.email,
    m.phone,
    p.period_end,
    CAST(julianday(p.period_end) - julianday('now') AS INTEGER) AS days_until_expiry,
    p.amount AS last_payment_amount
FROM members m
JOIN payments p ON m.id = p.member_id
WHERE p.status = 'Оплачено'
  AND date(p.period_end) >= date('now')
  AND date(p.period_end) <= date('now', '+7 days')
  AND p.id = (
      SELECT MAX(p2.id) 
      FROM payments p2 
      WHERE p2.member_id = m.id AND p2.status = 'Оплачено'
  )
ORDER BY p.period_end ASC;


-- 10. Дополнительный запрос: Рейтинг тренеров по посещаемости их занятий
-- (тренеры, чьи занятия наиболее популярны)
-- ============================================================
SELECT 
    t.id AS trainer_id,
    t.first_name || ' ' || t.last_name AS trainer_name,
    t.specialization,
    COUNT(DISTINCT c.id) AS total_classes,
    COUNT(v.id) AS total_visits,
    COUNT(DISTINCT v.member_id) AS unique_students,
    ROUND(AVG(CASE WHEN v.status = 'Посещено' THEN 1.0 ELSE 0.0 END) * 100, 1) AS attendance_rate,
    ROUND(SUM(CASE WHEN v.status = 'Посещено' THEN 1 ELSE 0 END) * 100.0 / COUNT(v.id), 1) AS success_rate
FROM trainers t
LEFT JOIN classes c ON t.id = c.trainer_id
LEFT JOIN visits v ON c.id = v.class_id
GROUP BY t.id, t.first_name, t.last_name, t.specialization
HAVING COUNT(v.id) > 0
ORDER BY total_visits DESC, attendance_rate DESC;
