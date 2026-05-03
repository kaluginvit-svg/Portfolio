(function () {
    const urlsInput = document.getElementById('urls');
    const analyzeBtn = document.getElementById('analyze');
    const logEl = document.getElementById('log');
    const resultEl = document.getElementById('result');

    function normalizeUrl(s) {
        s = (s || '').trim();
        if (!s) return '';
        return /^https?:\/\//i.test(s) ? s : 'https://' + s;
    }

    function parseUrls(text) {
        var raw = (text || '').split(/[\n,;\s]+/).map(function (s) { return s.trim(); }).filter(Boolean);
        var normalized = raw.map(normalizeUrl).filter(Boolean);
        return normalized.filter(function (v, i, a) { return a.indexOf(v) === i; });
    }

    function setRunning(running) {
        analyzeBtn.disabled = running;
        urlsInput.disabled = running;
    }

    function appendLog(text) {
        var line = document.createElement('div');
        line.className = 'line';
        line.textContent = text;
        logEl.appendChild(line);
        logEl.scrollTop = logEl.scrollHeight;
    }

    function setResult(text) {
        resultEl.textContent = text || '';
        if (text) resultEl.classList.add('has-content');
        else resultEl.classList.remove('has-content');
    }

    function handleSSEMessage(payload) {
        try {
            var data = JSON.parse(payload);
            var event = data.event;
            var msg = data.data;
            if (event === 'log') appendLog(msg);
            else if (event === 'result') {
                setResult(msg);
                setRunning(false);
                appendLog('Анализ завершён.');
                return true;
            }
        } catch (e) {
            appendLog('Ошибка разбора ответа: ' + e.message);
        }
        return false;
    }

    function streamSSE(response) {
        var reader = response.body.getReader();
        var decoder = new TextDecoder();
        var buf = '';
        function read() {
            reader.read().then(function (r) {
                if (r.done) {
                    if (analyzeBtn.disabled) setRunning(false);
                    return;
                }
                buf += decoder.decode(r.value, { stream: true });
                var parts = buf.split('\n\n');
                buf = parts.pop() || '';
                for (var i = 0; i < parts.length; i++) {
                    var line = parts[i];
                    if (line.startsWith('data: ')) {
                        if (handleSSEMessage(line.slice(6))) return;
                    }
                }
                read();
            }).catch(function (err) {
                appendLog('Ошибка чтения потока: ' + err.message);
                setRunning(false);
            });
        }
        read();
    }

    var apiBase = (typeof window !== 'undefined' && window.location && window.location.origin) ? window.location.origin : '';

    analyzeBtn.addEventListener('click', function () {
        var urls = parseUrls(urlsInput.value);
        if (!urls.length) {
            appendLog('Введите хотя бы один URL.');
            return;
        }

        logEl.innerHTML = '';
        setResult('');
        appendLog('Запуск анализа (' + urls.length + ' URL)...');
        setRunning(true);

        var url = apiBase + '/api/analyze';
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ urls: urls }),
        }).then(function (response) {
            if (!response.ok) {
                response.json().then(function (err) {
                    var d = err.detail;
                    var msg = typeof d === 'string' ? d : Array.isArray(d) ? (d[0] && d[0].msg) || JSON.stringify(d) : (d && d.msg) || response.statusText;
                    appendLog('Ошибка ' + response.status + ': ' + msg);
                }).catch(function () {
                    appendLog('Ошибка ' + response.status + ' ' + response.statusText);
                });
                setRunning(false);
                return;
            }
            streamSSE(response);
        }).catch(function (err) {
            appendLog('Ошибка запроса: ' + err.message);
            setRunning(false);
        });
    });

    urlsInput.addEventListener('input', function () {
        analyzeBtn.disabled = parseUrls(urlsInput.value).length === 0;
    });
})();
