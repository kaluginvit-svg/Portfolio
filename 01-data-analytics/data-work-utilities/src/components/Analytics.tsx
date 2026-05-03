import React from 'react';
import { Row, ColumnTypes } from '../types';

interface AnalyticsProps {
  headers: string[];
  rows: Row[];
  columnTypes: ColumnTypes;
}

export const Analytics: React.FC<AnalyticsProps> = ({ headers, rows, columnTypes }) => {
  // Подсчет сумм по числовым столбцам
  const numericColumns = headers.filter((h) => columnTypes[h] === 'number');
  
  const numericSums = numericColumns.map((col) => {
    const sum = rows.reduce((acc, row) => {
      const val = parseFloat(String(row[col]));
      return acc + (isNaN(val) ? 0 : val);
    }, 0);
    return { column: col, sum };
  });

  // Подсчет уникальных значений
  const uniqueCounts = headers.map((col) => {
    const uniqueValues = new Set(
      rows.map((row) => String(row[col]).trim()).filter((v) => v !== '')
    );
    return { column: col, count: uniqueValues.size };
  });

  return (
    <section className="analytics-section">
      <h2>Базовая аналитика</h2>
      <div className="analytics-content">
        {numericSums.length > 0 && (
          <div className="analytics-item">
            <h3>Суммы по числовым столбцам</h3>
            <table>
              <tbody>
                {numericSums.map(({ column, sum }) => (
                  <tr key={column}>
                    <td>{column}</td>
                    <td>
                      {sum.toLocaleString('ru-RU', { maximumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="analytics-item">
          <h3>Уникальные значения по столбцам</h3>
          <table>
            <tbody>
              {uniqueCounts.map(({ column, count }) => (
                <tr key={column}>
                  <td>{column}</td>
                  <td>{count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
};
