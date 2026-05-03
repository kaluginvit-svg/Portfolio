import React, { useState, useEffect } from 'react';
import { Row } from '../types';
import { formatCellValue } from '../utils/excelParser';

interface DataTableProps {
  headers: string[];
  rows: Row[];
}

const ROWS_PER_PAGE = 100;

export const DataTable: React.FC<DataTableProps> = ({ headers, rows }) => {
  const [displayedRows, setDisplayedRows] = useState(ROWS_PER_PAGE);

  useEffect(() => {
    setDisplayedRows(ROWS_PER_PAGE);
  }, [rows]);

  const handleLoadMore = () => {
    setDisplayedRows((prev) => Math.min(prev + ROWS_PER_PAGE, rows.length));
  };

  const visibleRows = rows.slice(0, displayedRows);
  const hasMore = displayedRows < rows.length;

  return (
    <section className="table-section">
      <h2>Данные</h2>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              {headers.map((header, index) => (
                <th key={index}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleRows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {headers.map((header, colIndex) => (
                  <td key={colIndex}>{formatCellValue(row[header])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="table-controls">
        {hasMore && (
          <button className="btn btn-primary" onClick={handleLoadMore}>
            Показать ещё 100 строк
          </button>
        )}
        <div className="rows-info">
          Показано {displayedRows} из {rows.length} строк
        </div>
      </div>
    </section>
  );
};
