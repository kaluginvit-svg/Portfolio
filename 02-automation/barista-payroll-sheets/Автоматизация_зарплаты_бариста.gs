/**
 * Скрипт автоматизации таблицы "Зарплата_бариста_Декабрь_2025"
 * 
 * Описание: 
 * Полная автоматизация расчета зарплаты бариста в Google Sheets с использованием смысловых якорей.
 * Скрипт работает с заголовками колонок и названиями листов, а не с конкретными номерами ячеек,
 * что делает его масштабируемым и устойчивым к изменениям структуры таблицы.
 * 
 * Основные принципы:
 * 1. Не завязан на номера колонок - использует поиск по заголовкам
 * 2. Смысловые якоря - работает с названиями листов, заголовками, параметрами
 * 3. Пакетная обработка - обрабатывает диапазоны данных целиком
 * 4. Понятные сообщения - логирует все действия в лист "Логи"
 * 
 * Структура таблицы:
 * - Лист "Смены": Дата, Сотрудник, Время начала, Время завершения, Часы работы
 * - Листы месяцев ("декабрь", "январь" и т.д.): Дата, Сотрудник, Выручка
 * - Лист "Зарплата_период": Сотрудник, Часы работы, Выручка, Зарплата
 */

// Константы для названий листов и заголовков
const SHEET_NAMES = {
  SHIFTS: 'Смены',
  SALARY_PERIOD: 'Зарплата_период'
};

const COLUMN_NAMES = {
  DATE: 'Дата',
  EMPLOYEE: 'Сотрудник',
  START_TIME: 'Время начала',
  END_TIME: 'Время завершения',
  HOURS: 'Часы работы',
  REVENUE: 'Выручка',
  SALARY: 'Зарплата'
};

/**
 * Главная функция инициализации - запускается при открытии таблицы
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Автоматизация зарплаты')
    .addItem('Настроить таблицу', 'initializeTable')
    .addSeparator()
    .addItem('Создать лист месяца', 'createMonthSheet')
    .addItem('Добавить нового сотрудника', 'addNewEmployee')
    .addSeparator()
    .addItem('Обновить выпадающие списки', 'setupDataValidation')
    .addItem('Обновить формулы', 'setupFormulas')
    .addItem('Пересчитать зарплату', 'calculateSalary')
    .addToUi();
  
  logActivity('Меню автоматизации добавлено');
}

/**
 * Инициализация таблицы - настройка всех компонентов
 */
function initializeTable() {
  try {
    logActivity('Начало инициализации таблицы');
    
    // Проверка структуры таблицы
    const structureCheck = checkTableStructure();
    if (!structureCheck.isValid) {
      const message = 'Обнаружены проблемы со структурой таблицы:\n\n' + 
                     structureCheck.errors.join('\n') + 
                     '\n\nПродолжить настройку?';
      const ui = SpreadsheetApp.getUi();
      const response = ui.alert('Проверка структуры', message, ui.ButtonSet.YES_NO);
      if (response !== ui.Button.YES) {
        return;
      }
    }
    
    setupDataValidation();
    setupFormulas();
    updateEmployeeList();
    
    SpreadsheetApp.getUi().alert('Таблица успешно инициализирована!\n\nОбработано листов: ' + 
                                 structureCheck.sheetsFound + '\nНайдено сотрудников: ' + 
                                 getEmployeeList().length);
    logActivity('Инициализация завершена успешно');
  } catch (error) {
    logActivity('Ошибка при инициализации: ' + error.toString());
    SpreadsheetApp.getUi().alert('Ошибка: ' + error.toString());
  }
}

/**
 * Проверка структуры таблицы
 */
function checkTableStructure() {
  const result = {
    isValid: true,
    errors: [],
    warnings: [],
    sheetsFound: 0
  };
  
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheets = ss.getSheets();
  
  // Проверка наличия основных листов
  const shiftsSheet = ss.getSheetByName(SHEET_NAMES.SHIFTS);
  const salarySheet = ss.getSheetByName(SHEET_NAMES.SALARY_PERIOD);
  
  if (!shiftsSheet) {
    result.isValid = false;
    result.errors.push('Лист "' + SHEET_NAMES.SHIFTS + '" не найден');
  } else {
    result.sheetsFound++;
    const headers = findHeaders(shiftsSheet);
    if (!headers[COLUMN_NAMES.EMPLOYEE]) {
      result.errors.push('На листе "' + SHEET_NAMES.SHIFTS + '" не найдена колонка "' + COLUMN_NAMES.EMPLOYEE + '"');
      result.isValid = false;
    }
    if (!headers[COLUMN_NAMES.START_TIME]) {
      result.warnings.push('На листе "' + SHEET_NAMES.SHIFTS + '" не найдена колонка "' + COLUMN_NAMES.START_TIME + '"');
    }
    if (!headers[COLUMN_NAMES.END_TIME]) {
      result.warnings.push('На листе "' + SHEET_NAMES.SHIFTS + '" не найдена колонка "' + COLUMN_NAMES.END_TIME + '"');
    }
  }
  
  if (!salarySheet) {
    result.isValid = false;
    result.errors.push('Лист "' + SHEET_NAMES.SALARY_PERIOD + '" не найден');
  } else {
    result.sheetsFound++;
    const headers = findHeaders(salarySheet);
    if (!headers[COLUMN_NAMES.EMPLOYEE]) {
      result.errors.push('На листе "' + SHEET_NAMES.SALARY_PERIOD + '" не найдена колонка "' + COLUMN_NAMES.EMPLOYEE + '"');
      result.isValid = false;
    }
  }
  
  // Подсчет листов месяцев
  const monthSheets = getMonthSheets();
  result.sheetsFound += monthSheets.length;
  
  if (monthSheets.length === 0) {
    result.warnings.push('Не найдено листов с месяцами (декабрь, январь и т.д.)');
  }
  
  logActivity('Проверка структуры: найдено листов - ' + result.sheetsFound + 
              ', ошибок - ' + result.errors.length + 
              ', предупреждений - ' + result.warnings.length);
  
  return result;
}

/**
 * Настройка выпадающих списков на листе "Смены"
 * ВАЖНО: Только устанавливает валидацию данных (выпадающие списки).
 * Не удаляет и не перезаписывает существующие данные пользователя.
 */
function setupDataValidation() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const shiftsSheet = ss.getSheetByName(SHEET_NAMES.SHIFTS);
    
    if (!shiftsSheet) {
      throw new Error('Лист "' + SHEET_NAMES.SHIFTS + '" не найден');
    }
    
    logActivity('Настройка выпадающих списков на листе "' + SHEET_NAMES.SHIFTS + '"');
    
    // Находим заголовки
    const headers = findHeaders(shiftsSheet);
    const employeeCol = headers[COLUMN_NAMES.EMPLOYEE];
    const startTimeCol = headers[COLUMN_NAMES.START_TIME];
    const endTimeCol = headers[COLUMN_NAMES.END_TIME];
    
    if (!employeeCol || !startTimeCol || !endTimeCol) {
      throw new Error('Не найдены необходимые колонки: Сотрудник, Время начала, Время завершения');
    }
    
    // Получаем список сотрудников
    const employees = getEmployeeList();
    
    // Создаем список времени (с шагом 30 минут)
    const timeOptions = generateTimeOptions();
    
    // Определяем диапазон данных (исключая заголовок)
    let lastRow = shiftsSheet.getLastRow();
    if (lastRow < 2) {
      // Если данных нет, создаем заголовки и одну пустую строку
      ensureHeaders(shiftsSheet);
      lastRow = 2;
    }
    
    // Настройка валидации для колонки "Сотрудник"
    if (employees.length > 0) {
      // Применяем валидацию к существующим строкам и будущим (до 1000 строк)
      const maxRows = Math.max(lastRow - 1, 100);
      const employeeRange = shiftsSheet.getRange(2, employeeCol, maxRows, 1);
      const employeeRule = SpreadsheetApp.newDataValidation()
        .requireValueInList(employees, true)
        .setAllowInvalid(false)
        .build();
      employeeRange.setDataValidation(employeeRule);
      logActivity('Выпадающий список для сотрудников установлен в колонке ' + employeeCol + ' (строк: ' + maxRows + ')');
    } else {
      logActivity('Предупреждение: список сотрудников пуст. Добавьте сотрудников для работы выпадающих списков.');
    }
    
    // Настройка валидации для времени начала
    const maxRows = Math.max(lastRow - 1, 100);
    const startTimeRange = shiftsSheet.getRange(2, startTimeCol, maxRows, 1);
    const startTimeRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(timeOptions, true)
      .setAllowInvalid(false)
      .build();
    startTimeRange.setDataValidation(startTimeRule);
    logActivity('Выпадающий список для времени начала установлен в колонке ' + startTimeCol + ' (строк: ' + maxRows + ')');
    
    // Настройка валидации для времени завершения
    const endTimeRange = shiftsSheet.getRange(2, endTimeCol, maxRows, 1);
    const endTimeRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(timeOptions, true)
      .setAllowInvalid(false)
      .build();
    endTimeRange.setDataValidation(endTimeRule);
    logActivity('Выпадающий список для времени завершения установлен в колонке ' + endTimeCol + ' (строк: ' + maxRows + ')');
    
    logActivity('Выпадающие списки настроены. Обработано строк: ' + maxRows);
    
  } catch (error) {
    logActivity('Ошибка при настройке выпадающих списков: ' + error.toString());
    throw error;
  }
}

/**
 * Получение списка всех сотрудников
 * ВАЖНО: Только читает данные из листов, не изменяет и не удаляет их.
 */
function getEmployeeList() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const shiftsSheet = ss.getSheetByName(SHEET_NAMES.SHIFTS);
  const salarySheet = ss.getSheetByName(SHEET_NAMES.SALARY_PERIOD);
  
  const employees = new Set();
  
  // Собираем сотрудников из листа "Смены"
  if (shiftsSheet) {
    const headers = findHeaders(shiftsSheet);
    const employeeCol = headers[COLUMN_NAMES.EMPLOYEE];
    
    if (employeeCol) {
      const lastRow = shiftsSheet.getLastRow();
      if (lastRow > 1) {
        const employeeRange = shiftsSheet.getRange(2, employeeCol, lastRow - 1, 1);
        const values = employeeRange.getValues();
        values.forEach(row => {
          if (row[0] && row[0].toString().trim() !== '') {
            employees.add(row[0].toString().trim());
          }
        });
      }
    }
  }
  
  // Собираем сотрудников из листа "Зарплата_период"
  if (salarySheet) {
    const headers = findHeaders(salarySheet);
    const employeeCol = headers[COLUMN_NAMES.EMPLOYEE];
    
    if (employeeCol) {
      const lastRow = salarySheet.getLastRow();
      if (lastRow > 1) {
        const employeeRange = salarySheet.getRange(2, employeeCol, lastRow - 1, 1);
        const values = employeeRange.getValues();
        values.forEach(row => {
          if (row[0] && row[0].toString().trim() !== '') {
            employees.add(row[0].toString().trim());
          }
        });
      }
    }
  }
  
  const employeeArray = Array.from(employees).sort();
  logActivity('Найдено сотрудников: ' + employeeArray.length);
  return employeeArray;
}

/**
 * Генерация списка времени с шагом 30 минут
 */
function generateTimeOptions() {
  const times = [];
  for (let hour = 0; hour < 24; hour++) {
    for (let minute = 0; minute < 60; minute += 30) {
      const timeStr = String(hour).padStart(2, '0') + ':' + String(minute).padStart(2, '0');
      times.push(timeStr);
    }
  }
  return times;
}

/**
 * Настройка формул на всех листах
 */
function setupFormulas() {
  try {
    logActivity('Начало настройки формул');
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    
    // Настройка формул на листе "Смены"
    setupShiftsFormulas();
    
    // Настройка формул на листах месяцев
    setupMonthSheetsFormulas();
    
    // Настройка формул на листе "Зарплата_период"
    setupSalaryPeriodFormulas();
    
    logActivity('Формулы настроены успешно');
    
  } catch (error) {
    logActivity('Ошибка при настройке формул: ' + error.toString());
    throw error;
  }
}

/**
 * Настройка формул на листе "Смены"
 * ВАЖНО: Обновляет только колонку "Часы работы" формулами расчета.
 * Не удаляет и не перезаписывает данные пользователя в других колонках.
 */
function setupShiftsFormulas() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const shiftsSheet = ss.getSheetByName(SHEET_NAMES.SHIFTS);
  
  if (!shiftsSheet) return;
  
  const headers = findHeaders(shiftsSheet);
  const startTimeCol = headers[COLUMN_NAMES.START_TIME];
  const endTimeCol = headers[COLUMN_NAMES.END_TIME];
  const hoursCol = headers[COLUMN_NAMES.HOURS];
  
  if (!startTimeCol || !endTimeCol || !hoursCol) {
    logActivity('Не все необходимые колонки найдены на листе "Смены"');
    return;
  }
  
  const lastRow = shiftsSheet.getLastRow();
  if (lastRow <= 1) return;
  
  // Формула расчета часов работы
  // Формула: (Время завершения - Время начала) * 24 для перевода в часы
  // Использует поиск колонок по заголовкам через findHeaders(), а не жестко заданные номера
  // ВАЖНО: Обновляет только колонку "Часы работы", не затрагивает другие данные
  const hoursRange = shiftsSheet.getRange(2, hoursCol, lastRow - 1, 1);
  const formulas = [];
  for (let i = 2; i <= lastRow; i++) {
    // Формула проверяет наличие обоих значений времени перед расчетом
    const formula = `=IF(AND(${getColumnLetter(startTimeCol)}${i}<>"", ${getColumnLetter(endTimeCol)}${i}<>""), 
      (TIMEVALUE(${getColumnLetter(endTimeCol)}${i}) - TIMEVALUE(${getColumnLetter(startTimeCol)}${i})) * 24, "")`;
    formulas.push([formula]);
  }
  // Применяем формулы пакетно ко всем строкам сразу (принцип пакетной обработки)
  // ВАЖНО: Это обновляет только формулы в колонке "Часы работы", не удаляет данные пользователя
  hoursRange.setFormulas(formulas);
  
  logActivity('Формулы на листе "Смены" установлены. Обработано строк: ' + (lastRow - 1));
}

/**
 * Настройка формул на листах месяцев
 */
function setupMonthSheetsFormulas() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheets = ss.getSheets();
  const monthSheets = sheets.filter(sheet => {
    const name = sheet.getName().toLowerCase();
    return name !== SHEET_NAMES.SHIFTS.toLowerCase() && 
           name !== SHEET_NAMES.SALARY_PERIOD.toLowerCase();
  });
  
  monthSheets.forEach(sheet => {
    logActivity('Настройка формул на листе "' + sheet.getName() + '"');
    // Здесь можно добавить специфичные формулы для листов месяцев
    // Например, расчет выручки, суммирование и т.д.
  });
  
  logActivity('Обработано листов месяцев: ' + monthSheets.length);
}

/**
 * Настройка формул на листе "Зарплата_период"
 * ВАЖНО: Обновляет только колонки с формулами ("Часы работы", "Выручка", "Зарплата").
 * Не удаляет и не перезаписывает данные пользователя в колонке "Сотрудник" и других колонках.
 */
function setupSalaryPeriodFormulas() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const salarySheet = ss.getSheetByName(SHEET_NAMES.SALARY_PERIOD);
  
  if (!salarySheet) {
    logActivity('Лист "' + SHEET_NAMES.SALARY_PERIOD + '" не найден');
    return;
  }
  
  const headers = findHeaders(salarySheet);
  const employeeCol = headers[COLUMN_NAMES.EMPLOYEE];
  const hoursCol = headers[COLUMN_NAMES.HOURS];
  const revenueCol = headers[COLUMN_NAMES.REVENUE];
  const salaryCol = headers[COLUMN_NAMES.SALARY];
  
  if (!employeeCol) {
    logActivity('Колонка "Сотрудник" не найдена на листе "Зарплата_период"');
    return;
  }
  
  const lastRow = salarySheet.getLastRow();
  if (lastRow <= 1) return;
  
  // Формула для суммирования часов из листа "Смены"
  // ВАЖНО: Обновляет только колонку "Часы работы", не затрагивает данные пользователя
  if (hoursCol) {
    const shiftsSheet = ss.getSheetByName(SHEET_NAMES.SHIFTS);
    if (shiftsSheet) {
      const shiftsHeaders = findHeaders(shiftsSheet);
      const shiftsEmployeeCol = shiftsHeaders[COLUMN_NAMES.EMPLOYEE];
      const shiftsHoursCol = shiftsHeaders[COLUMN_NAMES.HOURS];
      
      if (shiftsEmployeeCol && shiftsHoursCol) {
        // Используем SUMIF для суммирования часов по сотруднику
        // Формула работает с названиями колонок, а не с конкретными ячейками
        // ВАЖНО: Только читает данные из листа "Смены", не изменяет их
        const formulas = [];
        for (let i = 2; i <= lastRow; i++) {
          const employeeCell = getColumnLetter(employeeCol) + i;
          // SUMIF ищет все совпадения имени сотрудника и суммирует соответствующие часы
          const formula = `=SUMIF('${SHEET_NAMES.SHIFTS}'!${getColumnLetter(shiftsEmployeeCol)}:${getColumnLetter(shiftsEmployeeCol)}, 
            ${employeeCell}, '${SHEET_NAMES.SHIFTS}'!${getColumnLetter(shiftsHoursCol)}:${getColumnLetter(shiftsHoursCol)})`;
          formulas.push([formula]);
        }
        // Применяем формулы пакетно - обновляет только формулы, не удаляет данные
        salarySheet.getRange(2, hoursCol, lastRow - 1, 1).setFormulas(formulas);
        logActivity('Формулы для часов установлены. Обработано строк: ' + (lastRow - 1));
      }
    }
  }
  
  // Формула для суммирования выручки из всех листов месяцев
  // Динамически собирает формулу из всех найденных листов месяцев
  // При добавлении нового месяца автоматически включается в расчет
  // ВАЖНО: Только читает данные из листов месяцев, не изменяет их
  if (revenueCol) {
    const monthSheets = getMonthSheets();
    const formulas = [];
    for (let i = 2; i <= lastRow; i++) {
      const employeeCell = getColumnLetter(employeeCol) + i;
      let formula = '=';
      let formulaParts = [];
      
      monthSheets.forEach((monthSheet) => {
        const monthHeaders = findHeaders(monthSheet);
        const monthEmployeeCol = monthHeaders[COLUMN_NAMES.EMPLOYEE];
        const monthRevenueCol = monthHeaders[COLUMN_NAMES.REVENUE];
        
        if (monthEmployeeCol && monthRevenueCol) {
          // Для каждого листа месяца добавляем SUMIF
          // ВАЖНО: Только читает данные, не изменяет их
          formulaParts.push(`SUMIF('${monthSheet.getName()}'!${getColumnLetter(monthEmployeeCol)}:${getColumnLetter(monthEmployeeCol)}, 
            ${employeeCell}, '${monthSheet.getName()}'!${getColumnLetter(monthRevenueCol)}:${getColumnLetter(monthRevenueCol)})`);
        }
      });
      
      // Объединяем все части формулы через +
      formula += formulaParts.join('+');
      formulas.push([formula]);
    }
    
    // Применяем формулы пакетно - обновляет только формулы, не удаляет данные пользователя
    salarySheet.getRange(2, revenueCol, lastRow - 1, 1).setFormulas(formulas);
    logActivity('Формулы для выручки установлены. Обработано листов месяцев: ' + monthSheets.length + ', строк: ' + (lastRow - 1));
  }
  
  // Формула для расчета зарплаты (если есть)
  if (salaryCol && hoursCol) {
    const formulas = [];
    const headers = findHeaders(salarySheet);
    const rateCol = headers['Ставка'] || headers['ставка'] || headers['Ставка за час'] || headers['ставка за час'];
    
    for (let i = 2; i <= lastRow; i++) {
      const hoursCell = getColumnLetter(hoursCol) + i;
      let formula;
      
      if (rateCol) {
        // Если есть колонка со ставкой, используем её
        const rateCell = getColumnLetter(rateCol) + i;
        formula = `=IF(${hoursCell}<>"", ${hoursCell} * ${rateCell}, "")`;
      } else {
        // Иначе используем фиксированную ставку (можно изменить)
        formula = `=IF(${hoursCell}<>"", ${hoursCell} * 500, "")`;
      }
      formulas.push([formula]);
    }
    salarySheet.getRange(2, salaryCol, lastRow - 1, 1).setFormulas(formulas);
    logActivity('Формулы для зарплаты установлены');
  }
  
  logActivity('Формулы на листе "Зарплата_период" установлены. Обработано строк: ' + (lastRow - 1));
}

/**
 * Получение списка листов месяцев
 */
function getMonthSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheets = ss.getSheets();
  return sheets.filter(sheet => {
    const name = sheet.getName().toLowerCase();
    return name !== SHEET_NAMES.SHIFTS.toLowerCase() && 
           name !== SHEET_NAMES.SALARY_PERIOD.toLowerCase();
  });
}

/**
 * Поиск заголовков на листе (с учетом различных вариантов написания)
 * ВАЖНО: Только читает первую строку листа, не изменяет данные.
 */
function findHeaders(sheet) {
  const headers = {};
  const lastCol = sheet.getLastColumn();
  
  if (lastCol === 0) {
    logActivity('Лист "' + sheet.getName() + '" пуст');
    return headers;
  }
  
  const headerRow = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  
  headerRow.forEach((header, index) => {
    if (header && header.toString().trim() !== '') {
      const headerName = header.toString().trim();
      // Сохраняем оригинальное название
      headers[headerName] = index + 1;
      // Также сохраняем вариант в нижнем регистре для поиска
      headers[headerName.toLowerCase()] = index + 1;
    }
  });
  
  // Поиск по синонимам (если точное совпадение не найдено)
  const synonyms = {
    'сотрудник': ['employee', 'работник', 'бариста', 'имя'],
    'дата': ['date', 'день'],
    'время начала': ['start time', 'начало', 'начало смены'],
    'время завершения': ['end time', 'конец', 'конец смены', 'завершение'],
    'часы работы': ['hours', 'часы', 'отработано часов', 'время работы'],
    'выручка': ['revenue', 'доход', 'продажи'],
    'зарплата': ['salary', 'оплата', 'заработная плата']
  };
  
  // Если не найдено точное совпадение, ищем по синонимам
  Object.keys(COLUMN_NAMES).forEach(key => {
    const columnName = COLUMN_NAMES[key].toLowerCase();
    if (!headers[columnName] && synonyms[columnName]) {
      synonyms[columnName].forEach(synonym => {
        if (headers[synonym.toLowerCase()]) {
          headers[columnName] = headers[synonym.toLowerCase()];
        }
      });
    }
  });
  
  return headers;
}

/**
 * Получение буквы колонки по номеру (поддерживает колонки до ZZZ)
 */
function getColumnLetter(columnNumber) {
  let result = '';
  let temp = columnNumber;
  while (temp > 0) {
    const remainder = (temp - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    temp = Math.floor((temp - 1) / 26);
  }
  return result || 'A';
}

/**
 * Обновление списка сотрудников
 */
function updateEmployeeList() {
  try {
    logActivity('Обновление списка сотрудников');
    const employees = getEmployeeList();
    logActivity('Список сотрудников обновлен. Всего: ' + employees.length);
    return employees;
  } catch (error) {
    logActivity('Ошибка при обновлении списка сотрудников: ' + error.toString());
    throw error;
  }
}

/**
 * Добавление нового сотрудника
 */
function addNewEmployee() {
  try {
    const ui = SpreadsheetApp.getUi();
    const response = ui.prompt('Добавить нового сотрудника', 'Введите имя сотрудника:', ui.ButtonSet.OK_CANCEL);
    
    if (response.getSelectedButton() !== ui.Button.OK) {
      return;
    }
    
    const employeeName = response.getResponseText().trim();
    if (!employeeName) {
      ui.alert('Имя сотрудника не может быть пустым');
      return;
    }
    
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const salarySheet = ss.getSheetByName(SHEET_NAMES.SALARY_PERIOD);
    
    if (!salarySheet) {
      throw new Error('Лист "' + SHEET_NAMES.SALARY_PERIOD + '" не найден');
    }
    
    const headers = findHeaders(salarySheet);
    const employeeCol = headers[COLUMN_NAMES.EMPLOYEE];
    
    if (!employeeCol) {
      throw new Error('Колонка "Сотрудник" не найдена');
    }
    
    // Добавляем новую строку
    const lastRow = salarySheet.getLastRow();
    const newRow = lastRow + 1;
    salarySheet.insertRowAfter(lastRow);
    
    // Вставляем имя сотрудника
    salarySheet.getRange(newRow, employeeCol).setValue(employeeName);
    
    // Копируем формулы из предыдущей строки
    if (lastRow >= 2) {
      const sourceRange = salarySheet.getRange(lastRow, 1, 1, salarySheet.getLastColumn());
      const targetRange = salarySheet.getRange(newRow, 1, 1, salarySheet.getLastColumn());
      sourceRange.copyTo(targetRange, {formatOnly: false});
      // Возвращаем имя сотрудника (так как оно скопировалось)
      salarySheet.getRange(newRow, employeeCol).setValue(employeeName);
    }
    
    // Обновляем выпадающие списки
    setupDataValidation();
    
    logActivity('Добавлен новый сотрудник: ' + employeeName + ' в строку ' + newRow);
    ui.alert('Сотрудник "' + employeeName + '" успешно добавлен!');
    
  } catch (error) {
    logActivity('Ошибка при добавлении сотрудника: ' + error.toString());
    SpreadsheetApp.getUi().alert('Ошибка: ' + error.toString());
  }
}

/**
 * Создание нового листа месяца
 * Создает лист с заголовками для учета выручки за месяц
 * и автоматически обновляет формулы на листе "Зарплата_период"
 */
function createMonthSheet() {
  try {
    const ui = SpreadsheetApp.getUi();
    
    // Список месяцев для подсказки
    const months = [
      'январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
      'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь'
    ];
    
    // Запрашиваем название месяца
    const response = ui.prompt(
      'Создать лист месяца', 
      'Введите название месяца (например: февраль, март, апрель):\n\n' +
      'Доступные месяцы: ' + months.join(', '), 
      ui.ButtonSet.OK_CANCEL
    );
    
    if (response.getSelectedButton() !== ui.Button.OK) {
      return;
    }
    
    let monthName = response.getResponseText().trim();
    if (!monthName) {
      ui.alert('Название месяца не может быть пустым');
      return;
    }
    
    // Приводим к нижнему регистру для единообразия
    monthName = monthName.toLowerCase();
    
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    
    // Проверяем, не существует ли уже лист с таким названием
    // ВАЖНО: Удаление существующего листа происходит ТОЛЬКО с явного подтверждения пользователя
    const existingSheet = ss.getSheetByName(monthName);
    if (existingSheet) {
      const overwrite = ui.alert(
        'Лист уже существует',
        'Лист "' + monthName + '" уже существует. Пересоздать его? (все данные будут удалены)',
        ui.ButtonSet.YES_NO
      );
      
      if (overwrite === ui.Button.YES) {
        // ВАЖНО: Удаление происходит только после подтверждения пользователя
        ss.deleteSheet(existingSheet);
        logActivity('Удален существующий лист "' + monthName + '" по запросу пользователя');
      } else {
        ui.alert('Операция отменена');
        logActivity('Создание листа "' + monthName + '" отменено пользователем');
        return;
      }
    }
    
    logActivity('Создание листа месяца: ' + monthName);
    
    // Создаем новый лист
    const newSheet = ss.insertSheet(monthName);
    
    // Устанавливаем заголовки для листа месяца
    const headers = [COLUMN_NAMES.DATE, COLUMN_NAMES.EMPLOYEE, COLUMN_NAMES.REVENUE];
    const headerRange = newSheet.getRange(1, 1, 1, headers.length);
    headerRange.setValues([headers]);
    headerRange.setFontWeight('bold');
    headerRange.setBackground('#e6f3ff');
    
    // Настраиваем ширину колонок для удобства
    newSheet.setColumnWidth(1, 100); // Дата
    newSheet.setColumnWidth(2, 150); // Сотрудник
    newSheet.setColumnWidth(3, 120); // Выручка
    
    // Замораживаем первую строку (заголовки)
    newSheet.setFrozenRows(1);
    
    logActivity('Лист "' + monthName + '" создан с заголовками: ' + headers.join(', '));
    
    // Обновляем формулы на листе "Зарплата_период", чтобы включить новый месяц
    setupSalaryPeriodFormulas();
    
    // Показываем сообщение об успехе
    ui.alert(
      'Лист месяца создан!',
      'Лист "' + monthName + '" успешно создан.\n\n' +
      'Заголовки установлены: ' + headers.join(', ') + '\n\n' +
      'Формулы на листе "Зарплата_период" обновлены для учета нового месяца.',
      ui.ButtonSet.OK
    );
    
    logActivity('Лист месяца "' + monthName + '" успешно создан и подключен к расчетам');
    
  } catch (error) {
    logActivity('Ошибка при создании листа месяца: ' + error.toString());
    SpreadsheetApp.getUi().alert('Ошибка: ' + error.toString());
  }
}

/**
 * Пересчет зарплаты
 */
function calculateSalary() {
  try {
    logActivity('Начало пересчета зарплаты');
    
    setupFormulas();
    updateEmployeeList();
    
    logActivity('Пересчет зарплаты завершен');
    SpreadsheetApp.getUi().alert('Зарплата пересчитана успешно!');
    
  } catch (error) {
    logActivity('Ошибка при пересчете зарплаты: ' + error.toString());
    SpreadsheetApp.getUi().alert('Ошибка: ' + error.toString());
  }
}

/**
 * Автоматическое применение формул при изменении данных
 */
function onEdit(e) {
  try {
    const sheet = e.source.getActiveSheet();
    const sheetName = sheet.getName();
    const row = e.range.getRow();
    const col = e.range.getColumn();
    
    // Если редактируется лист "Зарплата_период" и добавляется новая строка
    if (sheetName === SHEET_NAMES.SALARY_PERIOD && row > 1) {
      const headers = findHeaders(sheet);
      const employeeCol = headers[COLUMN_NAMES.EMPLOYEE];
      
      // Если редактируется колонка сотрудника и это новая строка
      if (employeeCol && col === employeeCol && row === sheet.getLastRow()) {
        // Копируем формулы из предыдущей строки
        const prevRow = row - 1;
        if (prevRow >= 2) {
          const sourceRange = sheet.getRange(prevRow, 1, 1, sheet.getLastColumn());
          const targetRange = sheet.getRange(row, 1, 1, sheet.getLastColumn());
          sourceRange.copyTo(targetRange, {formatOnly: false});
          // Возвращаем имя сотрудника
          const employeeName = sheet.getRange(row, employeeCol).getValue();
          sheet.getRange(row, employeeCol).setValue(employeeName);
          logActivity('Автоматически применены формулы для новой строки ' + row);
        }
      }
    }
    
    // Если редактируется лист "Смены" и меняется сотрудник
    if (sheetName === SHEET_NAMES.SHIFTS) {
      const headers = findHeaders(sheet);
      const employeeCol = headers[COLUMN_NAMES.EMPLOYEE];
      
      if (employeeCol && col === employeeCol) {
        // Обновляем список сотрудников для выпадающих списков
        setupDataValidation();
      }
    }
    
  } catch (error) {
    logActivity('Ошибка в onEdit: ' + error.toString());
  }
}

/**
 * Создание заголовков, если их нет
 * ВАЖНО: Создает заголовки ТОЛЬКО если их нет (первая строка пустая).
 * Не перезаписывает существующие заголовки или данные пользователя.
 */
function ensureHeaders(sheet) {
  const lastCol = sheet.getLastColumn();
  const headerRow = sheet.getRange(1, 1, 1, lastCol || 10).getValues()[0];
  const hasHeaders = headerRow.some(cell => cell && cell.toString().trim() !== '');
  
  // ВАЖНО: Создаем заголовки только если их действительно нет
  if (!hasHeaders) {
    // Определяем какие заголовки нужны в зависимости от листа
    const sheetName = sheet.getName();
    let headers = [];
    
    if (sheetName === SHEET_NAMES.SHIFTS) {
      headers = [COLUMN_NAMES.DATE, COLUMN_NAMES.EMPLOYEE, COLUMN_NAMES.START_TIME, 
                 COLUMN_NAMES.END_TIME, COLUMN_NAMES.HOURS];
    } else if (sheetName === SHEET_NAMES.SALARY_PERIOD) {
      headers = [COLUMN_NAMES.EMPLOYEE, COLUMN_NAMES.HOURS, COLUMN_NAMES.REVENUE, COLUMN_NAMES.SALARY];
    } else {
      // Для листов месяцев
      headers = [COLUMN_NAMES.DATE, COLUMN_NAMES.EMPLOYEE, COLUMN_NAMES.REVENUE];
    }
    
    // Устанавливаем заголовки
    const headerRange = sheet.getRange(1, 1, 1, headers.length);
    headerRange.setValues([headers]);
    headerRange.setFontWeight('bold');
    headerRange.setBackground('#e6f3ff');
    
    logActivity('Созданы заголовки на листе "' + sheetName + '": ' + headers.join(', '));
  }
}

/**
 * Логирование действий
 */
function logActivity(message) {
  const timestamp = new Date().toLocaleString('ru-RU');
  console.log('[' + timestamp + '] ' + message);
  
  // Опционально: можно записывать логи в отдельный лист
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let logSheet = ss.getSheetByName('Логи');
    
    if (!logSheet) {
      logSheet = ss.insertSheet('Логи');
      logSheet.getRange(1, 1, 1, 2).setValues([['Время', 'Сообщение']]);
      logSheet.getRange(1, 1, 1, 2).setFontWeight('bold');
    }
    
    const lastRow = logSheet.getLastRow();
    logSheet.getRange(lastRow + 1, 1, 1, 2).setValues([[timestamp, message]]);
    
    // Ограничиваем количество строк в логах (последние 1000)
    if (lastRow > 1000) {
      logSheet.deleteRows(2, lastRow - 1000);
    }
  } catch (error) {
    // Игнорируем ошибки логирования
  }
}
