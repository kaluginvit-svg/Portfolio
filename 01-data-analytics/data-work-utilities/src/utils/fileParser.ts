import { parseExcelFile, parseCSVFile, Row } from './excelParser';
import { parsePDFFile } from './pdfParser';

export function parseFile(file: File): Promise<{ headers: string[]; rows: Row[]; sheetName: string }> {
  const fileName = file.name.toLowerCase();
  const extension = fileName.substring(fileName.lastIndexOf('.'));
  
  if (extension === '.csv') {
    return parseCSVFile(file);
  } else if (extension === '.xlsx' || extension === '.xls') {
    return parseExcelFile(file);
  } else if (extension === '.pdf') {
    return parsePDFFile(file);
  } else {
    return Promise.reject(new Error('Неподдерживаемый формат файла. Поддерживаются: .csv, .xlsx, .xls, .pdf'));
  }
}

export { parseExcelFile, parseCSVFile } from './excelParser';
export { parsePDFFile } from './pdfParser';
export { detectColumnTypes, parseDate, formatDate, formatFileSize, formatCellValue } from './excelParser';
export type { Row, ColumnTypes } from '../types';
