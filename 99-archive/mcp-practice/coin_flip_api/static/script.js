// Глобальная статистика
let stats = {
    total: 0,
    heads: 0,
    tails: 0
};

// История последних результатов (максимум 50)
const history = [];
const MAX_HISTORY = 50;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    updateDisplay();
});

// Загрузить статистику из localStorage
function loadStats() {
    const saved = localStorage.getItem('coinFlipStats');
    if (saved) {
        stats = JSON.parse(saved);
    }
}

// Сохранить статистику в localStorage
function saveStats() {
    localStorage.setItem('coinFlipStats', JSON.stringify(stats));
}

// Подбросить монетку один раз
async function flipOnce() {
    try {
        const response = await fetch('/flip');
        const data = await response.json();
        
        animateCoin(data.result);
        updateStats(data.result, 1);
        addToHistory([data.result]);
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при подбрасывании монетки');
    }
}

// Подбросить монетку несколько раз
async function flipMultiple(count) {
    try {
        const response = await fetch(`/flip/${count}`);
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        // Анимируем последний результат
        const lastResult = data.results[data.results.length - 1];
        animateCoin(lastResult);
        
        // Обновляем статистику
        updateStatsFromMultiple(data.results);
        addToHistory(data.results);
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при подбрасывании монетки');
    }
}

// Анимация монетки
function animateCoin(result) {
    const coin = document.getElementById('coin');
    const coinFace = document.getElementById('coinFace');
    
    coin.classList.add('flipping');
    coinFace.textContent = '?';
    
    setTimeout(() => {
        coin.classList.remove('flipping');
        coinFace.textContent = result === 'орел' ? '🦅' : '🪙';
        coinFace.className = 'coin-face ' + (result === 'орел' ? 'heads' : 'tails');
    }, 600);
}

// Обновить статистику из одного результата
function updateStats(result, count = 1) {
    stats.total += count;
    if (result === 'орел') {
        stats.heads += count;
    } else {
        stats.tails += count;
    }
    saveStats();
    updateDisplay();
}

// Обновить статистику из нескольких результатов
function updateStatsFromMultiple(results) {
    const headsCount = results.filter(r => r === 'орел').length;
    const tailsCount = results.filter(r => r === 'решка').length;
    
    stats.total += results.length;
    stats.heads += headsCount;
    stats.tails += tailsCount;
    
    saveStats();
    updateDisplay();
}

// Добавить результаты в историю
function addToHistory(results) {
    // Добавляем новые результаты в начало
    results.reverse().forEach(result => {
        history.unshift(result);
    });
    
    // Ограничиваем размер истории
    if (history.length > MAX_HISTORY) {
        history.splice(MAX_HISTORY);
    }
    
    updateHistoryDisplay();
}

// Обновить отображение статистики
function updateDisplay() {
    document.getElementById('totalFlips').textContent = stats.total;
    document.getElementById('headsCount').textContent = stats.heads;
    document.getElementById('tailsCount').textContent = stats.tails;
    
    // Проценты
    const total = stats.total || 1;
    const headsPercent = ((stats.heads / total) * 100).toFixed(1);
    const tailsPercent = ((stats.tails / total) * 100).toFixed(1);
    
    document.getElementById('headsPercent').textContent = headsPercent + '%';
    document.getElementById('tailsPercent').textContent = tailsPercent + '%';
}

// Обновить отображение истории
function updateHistoryDisplay() {
    const historyDiv = document.getElementById('history');
    
    if (history.length === 0) {
        historyDiv.innerHTML = '<div class="history-empty">История пуста. Начните подбрасывать монетку!</div>';
        return;
    }
    
    historyDiv.innerHTML = history.map(result => {
        const className = result === 'орел' ? 'heads' : 'tails';
        const emoji = result === 'орел' ? '🦅' : '🪙';
        return `<div class="history-item ${className}">${emoji} ${result}</div>`;
    }).join('');
}

// Сбросить статистику
function resetStats() {
    if (confirm('Вы уверены, что хотите сбросить всю статистику?')) {
        stats = {
            total: 0,
            heads: 0,
            tails: 0
        };
        history.length = 0;
        saveStats();
        updateDisplay();
        updateHistoryDisplay();
        
        // Сбросить монетку
        const coinFace = document.getElementById('coinFace');
        coinFace.textContent = '?';
        coinFace.className = 'coin-face';
    }
}
