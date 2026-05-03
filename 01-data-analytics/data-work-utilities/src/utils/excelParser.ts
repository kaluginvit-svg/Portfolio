import * as XLSX from 'xlsx';
import { Row, ColumnType, ColumnTypes } from '../types';

export function parseCSVFile(file: File): Promise<{ headers: string[]; rows: Row[]; sheetName: string }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        
        if (!text || text.trim() === '') {
          reject(new Error('Файл пуст'));
          return;
        }
        
        // Используем XLSX для парсинга CSV - более надежно
        const workbook = XLSX.read(text, { type: 'string', sheetRows: 0 });
        
        if (workbook.SheetNames.length === 0) {
          reject(new Error('Не удалось прочитать CSV файл'));
          return;
        }
        
        const worksheet = workbook.Sheets[workbook.SheetNames[0]];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' }) as any[][];
        
        if (jsonData.length === 0) {
          reject(new Error('Файл пуст'));
          return;
        }
        
        const headers = jsonData[0].map(String);
        const rows: Row[] = jsonData.slice(1).map((row) => {
          const obj: Row = {};
          headers.forEach((header, index) => {
            obj[header] = row[index] !== undefined ? row[index] : null;
          });
          return obj;
        });
        
        resolve({ headers, rows, sheetName: 'CSV' });
      } catch (error) {
        reject(error);
      }
    };
    
    reader.onerror = () => reject(new Error('Ошибка чтения файла'));
    reader.readAsText(file, 'UTF-8');
  });
}

export function parseExcelFile(file: File): Promise<{ headers: string[]; rows: Row[]; sheetName: string }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: 'array' });
        
        const firstSheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheetName];
        
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' }) as any[][];
        
        if (jsonData.length === 0) {
          reject(new Error('Файл пуст'));
          return;
        }
        
        const headers = jsonData[0].map(String);
        const rows: Row[] = jsonData.slice(1).map((row) => {
          const obj: Row = {};
          headers.forEach((header, index) => {
            obj[header] = row[index] !== undefined ? row[index] : null;
          });
          return obj;
        });
        
        resolve({ headers, rows, sheetName: firstSheetName });
      } catch (error) {
        reject(error);
      }
    };
    
    reader.onerror = () => reject(new Error('Ошибка чтения файла'));
    reader.readAsArrayBuffer(file);
  });
}

export function detectColumnTypes(headers: string[], rows: Row[]): ColumnTypes {
  const types: ColumnTypes = {};
  
  headers.forEach((header) => {
    const values = rows.slice(0, Math.min(100, rows.length)).map((row) => row[header]);
    const nonEmptyValues = values.filter((v) => v !== '' && v !== null && v !== undefined);
    
    if (nonEmptyValues.length === 0) {
      types[header] = 'string';
      return;
    }
    
    // Проверяем на числа
    const numericCount = nonEmptyValues.filter((v) => {
      const num = parseFloat(String(v));
      return !isNaN(num) && isFinite(num);
    }).length;
    
    // Проверяем на даты
    const dateCount = nonEmptyValues.filter((v) => {
      if (typeof v === 'number' && v > 25569 && v < 100000) return true;
      const date = new Date(String(v));
      return !isNaN(date.getTime()) && String(v).match(/\d{4}[-\/]\d{2}[-\/]\d{2}/);
    }).length;
    
    if (dateCount / nonEmptyValues.length > 0.5) {
      types[header] = 'date';
    } else if (numericCount / nonEmptyValues.length > 0.7) {
      types[header] = 'number';
    } else {
      types[header] = 'string';
    }
  });
  
  return types;
}

export function parseDate(value: string | number | null): Date | null {
  if (!value) return null;
  
  // Если это число Excel (дни с 1900-01-01)
  // Excel date serial number 1 = 1900-01-01
  // JavaScript Date использует миллисекунды с 1970-01-01
  // Разница: примерно 25569 дней (учитывая баг Excel с 1900 годом)
  if (typeof value === 'number' && value > 25569 && value < 100000) {
    // Конвертируем Excel date serial в JavaScript Date
    // Excel считает 1900 високосным (баг), поэтому используем 25568.875
    const excelEpoch = new Date(1899, 11, 30); // 1899-12-30 в JavaScript (1900-01-00 в Excel)
    const jsDate = new Date(excelEpoch.getTime() + (value - 1) * 86400000);
    return jsDate;
  }
  
  // Пробуем распарсить как дату
  const date = new Date(String(value));
  if (!isNaN(date.getTime())) {
    return date;
  }
  
  return null;
}

export function formatDate(date: Date): string {
  return date.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

export function formatCellValue(value: string | number | null): string {
  if (value === null || value === undefined || value === '') return '';
  if (typeof value === 'number') {
    // Проверяем, является ли это датой в числовом формате Excel
    if (value > 25569 && value < 100000) {
      const date = parseDate(value);
      if (date) {
        return date.toLocaleDateString('ru-RU');
      }
    }
    // Форматируем числа с разделителями тысяч
    return value.toLocaleString('ru-RU', { maximumFractionDigits: 2 });
  }
  return String(value);
}
