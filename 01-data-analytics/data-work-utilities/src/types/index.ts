export interface ExcelData {
  fileName: string;
  fileSize: number;
  sheetName: string;
  totalRows: number;
  totalColumns: number;
}

export interface Row {
  [key: string]: string | number | null;
}

export type ColumnType = 'number' | 'date' | 'string';

export interface ColumnTypes {
  [key: string]: ColumnType;
}

export interface ChartData {
  labels: string[];
  values: number[];
  label: string;
}
