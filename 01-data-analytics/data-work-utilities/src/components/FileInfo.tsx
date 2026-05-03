import React from 'react';
import { ExcelData } from '../types';
import { formatFileSize } from '../utils/excelParser';

interface FileInfoProps {
  data: ExcelData;
}

export const FileInfo: React.FC<FileInfoProps> = ({ data }) => {
  return (
    <section className="file-info">
      <h2>Информация о файле</h2>
      <div className="file-info-content">
        <p><strong>Имя файла:</strong> {data.fileName}</p>
        <p><strong>Размер файла:</strong> {formatFileSize(data.fileSize)}</p>
        <p><strong>Лист:</strong> {data.sheetName}</p>
        <p><strong>Всего строк:</strong> {data.totalRows}</p>
        <p><strong>Всего столбцов:</strong> {data.totalColumns}</p>
      </div>
    </section>
  );
};
