import { Row } from '../types';

// Используем относительный URL, так как Vite проксирует /api на backend
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export interface ParseFileResponse {
  headers: string[];
  rows: Row[];
  sheetName: string;
}

export interface AnalyzeDataResponse {
  gigachat: string;
  openrouter: string;
}

export interface GeneratePdfRequest {
  title: string;
  content: string;
}

/**
 * Отправляет файл на бэкенд для парсинга
 */
export async function parseFile(file: File): Promise<ParseFileResponse> {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${API_BASE_URL}/api/parse-file`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('Ошибка при отправке файла на сервер');
  }
}

/**
 * Отправляет данные таблицы на бэкенд для анализа AI
 */
export async function analyzeData(headers: string[], rows: Row[]): Promise<AnalyzeDataResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        headers,
        rows: rows.slice(0, 50), // Берем первые 50 строк
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('Ошибка при отправке данных для анализа');
  }
}

/**
 * Генерирует PDF файл на бэкенде и скачивает его
 */
export async function generatePdf(title: string, content: string): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/generate-pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title,
        content,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    // Получаем blob и скачиваем файл
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    
    // Формируем имя файла
    const date = new Date().toISOString().split('T')[0];
    const safeTitle = title.replace(/[^\w\s-]/g, '').replace(/\s+/g, '-').substring(0, 50);
    a.download = `${safeTitle}-${date}.pdf`;
    
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('Ошибка при генерации PDF файла');
  }
}
