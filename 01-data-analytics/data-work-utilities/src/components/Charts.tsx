import React, { useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { Line, Bar, Pie, Scatter } from 'react-chartjs-2';
import { Row, ColumnTypes } from '../types';
import { parseDate, formatDate } from '../utils/excelParser';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface ChartsProps {
  headers: string[];
  rows: Row[];
  columnTypes: ColumnTypes;
}

type ChartType = 'bar' | 'line' | 'pie' | 'scatter';

interface ChartConfig {
  type: ChartType;
  xColumn: string;
  yColumn: string;
  label: string;
}

export const Charts: React.FC<ChartsProps> = ({ headers, rows, columnTypes }) => {
  const [chartConfigs, setChartConfigs] = useState<ChartConfig[]>([]);

  const numericColumns = headers.filter((h) => columnTypes[h] === 'number');
  const dateColumns = headers.filter((h) => columnTypes[h] === 'date');
  const stringColumns = headers.filter((h) => columnTypes[h] === 'string');

  // Добавляем новый график
  const addChart = () => {
    const defaultXCol = dateColumns[0] || stringColumns[0] || headers[0];
    const defaultYCol = numericColumns[0] || headers[1] || headers[0];
    
    setChartConfigs([
      ...chartConfigs,
      {
        type: 'bar',
        xColumn: defaultXCol || headers[0],
        yColumn: defaultYCol || headers[1] || headers[0],
        label: `График ${chartConfigs.length + 1}`,
      },
    ]);
  };

  // Удаляем график
  const removeChart = (index: number) => {
    setChartConfigs(chartConfigs.filter((_, i) => i !== index));
  };

  // Обновляем конфигурацию графика
  const updateChartConfig = (index: number, updates: Partial<ChartConfig>) => {
    const updated = [...chartConfigs];
    updated[index] = { ...updated[index], ...updates };
    setChartConfigs(updated);
  };

  // Рендерим график по конфигурации
  const renderChart = (config: ChartConfig, index: number) => {
    const { type, xColumn, yColumn } = config;

    if (type === 'pie') {
      // Для pie chart нужны категории и значения
      const grouped: { [key: string]: number } = {};
      rows.forEach((row) => {
        const category = String(row[xColumn]).trim();
        const value = parseFloat(String(row[yColumn]));
        if (category && !isNaN(value)) {
          grouped[category] = (grouped[category] || 0) + value;
        }
      });

      const labels = Object.keys(grouped).slice(0, 20); // Ограничиваем 20 категориями
      const values = labels.map((cat) => grouped[cat]);

      if (labels.length === 0) return null;

      const data = {
        labels,
        datasets: [
          {
            label: yColumn,
            data: values,
            backgroundColor: [
              '#667eea',
              '#f093fb',
              '#4facfe',
              '#43e97b',
              '#fa709a',
              '#fee140',
              '#30cfd0',
              '#a8edea',
              '#fed6e3',
              '#ff9a9e',
              '#fecfef',
              '#fecfef',
              '#fad0c4',
              '#ffd1ff',
              '#a1c4fd',
              '#c2e9fb',
              '#ffecd2',
              '#fcb69f',
              '#ff8a80',
              '#ffb74d',
            ].slice(0, labels.length),
          },
        ],
      };

      return <Pie data={data} options={getPieOptions()} />;
    }

    if (type === 'scatter') {
      // Для scatter chart нужны две числовые оси
      const data = rows
        .map((row) => ({
          x: parseFloat(String(row[xColumn])),
          y: parseFloat(String(row[yColumn])),
        }))
        .filter((d) => !isNaN(d.x) && !isNaN(d.y))
        .slice(0, 1000); // Ограничиваем для производительности

      if (data.length === 0) return null;

      const scatterData = {
        datasets: [
          {
            label: `${yColumn} vs ${xColumn}`,
            data: data,
            backgroundColor: 'rgba(102, 126, 234, 0.6)',
            borderColor: '#667eea',
          },
        ],
      };

      return <Scatter data={scatterData} options={getScatterOptions()} />;
    }

    if (type === 'line') {
      // Для line chart нужна дата/категория и значение
      const isDate = dateColumns.includes(xColumn);
      const data = rows
        .map((row) => ({
          x: isDate ? parseDate(row[xColumn]) : String(row[xColumn]).trim(),
          y: parseFloat(String(row[yColumn])),
        }))
        .filter((d) => d.x && !isNaN(d.y))
        .sort((a, b) => {
          if (isDate) {
            return (a.x as Date).getTime() - (b.x as Date).getTime();
          }
          return String(a.x).localeCompare(String(b.x));
        });

      if (data.length === 0) return null;

      const lineData = {
        labels: data.map((d) => (isDate ? formatDate(d.x as Date) : String(d.x))),
        datasets: [
          {
            label: yColumn,
            data: data.map((d) => d.y),
            borderColor: '#1e3a8a',
            backgroundColor: 'rgba(30, 58, 138, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
          },
        ],
      };

      return <Line data={lineData} options={getLineOptions()} />;
    }

    // Bar chart (по умолчанию)
    if (type === 'bar') {
      const isDate = dateColumns.includes(xColumn);
      
      if (isDate) {
        // Для дат группируем по датам
        const grouped: { [key: string]: number } = {};
        rows.forEach((row) => {
          const date = parseDate(row[xColumn]);
          const value = parseFloat(String(row[yColumn]));
          if (date && !isNaN(value)) {
            const dateStr = formatDate(date);
            grouped[dateStr] = (grouped[dateStr] || 0) + value;
          }
        });

        const labels = Object.keys(grouped).sort();
        const values = labels.map((label) => grouped[label]);

        if (labels.length === 0) return null;

        const barData = {
          labels,
          datasets: [
            {
              label: yColumn,
              data: values,
              backgroundColor: '#4facfe',
              borderColor: '#00f2fe',
              borderWidth: 1,
            },
          ],
        };

        return <Bar data={barData} options={getBarOptions()} />;
      } else {
        // Для категорий
        const grouped: { [key: string]: number } = {};
        rows.forEach((row) => {
          const category = String(row[xColumn]).trim();
          const value = parseFloat(String(row[yColumn]));
          if (category && !isNaN(value)) {
            grouped[category] = (grouped[category] || 0) + value;
          }
        });

        const labels = Object.keys(grouped).sort().slice(0, 50); // Ограничиваем 50 категориями
        const values = labels.map((cat) => grouped[cat]);

        if (labels.length === 0) return null;

        const barData = {
          labels,
          datasets: [
            {
              label: yColumn,
              data: values,
              backgroundColor: '#4facfe',
              borderColor: '#00f2fe',
              borderWidth: 1,
            },
          ],
        };

        return <Bar data={barData} options={getBarOptions()} />;
      }
    }

    return null;
  };

  const getBarOptions = (): ChartOptions<'bar'> => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  });

  const getLineOptions = (): ChartOptions<'line'> => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: false,
      },
    },
  });

  const getPieOptions = (): ChartOptions<'pie'> => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'right' as const,
      },
    },
  });

  const getScatterOptions = (): ChartOptions<'scatter'> => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
      },
    },
    scales: {
      x: {
        type: 'linear',
        position: 'bottom',
      },
      y: {
        beginAtZero: false,
      },
    },
  });

  return (
    <section className="charts-section">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Визуализация данных</h2>
        <button className="btn btn-primary" onClick={addChart}>
          + Добавить график
        </button>
      </div>

      {chartConfigs.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          <p>Нажмите "Добавить график" чтобы создать визуализацию</p>
        </div>
      )}

      <div className="charts-container">
        {chartConfigs.map((config, index) => (
          <div key={index} className="chart-wrapper">
            <div style={{ marginBottom: '15px' }}>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '10px' }}>
                <div style={{ flex: '1', minWidth: '150px' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9em', color: '#666' }}>
                    Тип графика:
                  </label>
                  <select
                    value={config.type}
                    onChange={(e) => updateChartConfig(index, { type: e.target.value as ChartType })}
                    style={{
                      width: '100%',
                      padding: '8px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontFamily: 'Georgia, serif',
                    }}
                  >
                    <option value="bar">Гистограмма (Bar)</option>
                    <option value="line">Линейный (Line)</option>
                    <option value="pie">Круговая диаграмма (Pie)</option>
                    <option value="scatter">Точечная (Scatter)</option>
                  </select>
                </div>

                <div style={{ flex: '1', minWidth: '150px' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9em', color: '#666' }}>
                    {config.type === 'scatter' ? 'Ось X:' : config.type === 'pie' ? 'Категории:' : 'Ось X:'}
                  </label>
                  <select
                    value={config.xColumn}
                    onChange={(e) => updateChartConfig(index, { xColumn: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '8px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontFamily: 'Georgia, serif',
                    }}
                  >
                    {headers.map((header) => (
                      <option key={header} value={header}>
                        {header}
                      </option>
                    ))}
                  </select>
                </div>

                <div style={{ flex: '1', minWidth: '150px' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9em', color: '#666' }}>
                    {config.type === 'scatter' ? 'Ось Y:' : config.type === 'pie' ? 'Значения:' : 'Ось Y:'}
                  </label>
                  <select
                    value={config.yColumn}
                    onChange={(e) => updateChartConfig(index, { yColumn: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '8px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontFamily: 'Georgia, serif',
                    }}
                  >
                    {numericColumns.length > 0 ? (
                      numericColumns.map((header) => (
                        <option key={header} value={header}>
                          {header}
                        </option>
                      ))
                    ) : (
                      headers.map((header) => (
                        <option key={header} value={header}>
                          {header}
                        </option>
                      ))
                    )}
                  </select>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                  <button
                    className="btn"
                    onClick={() => removeChart(index)}
                    style={{
                      backgroundColor: '#dc2626',
                      color: '#fff',
                      padding: '8px 16px',
                    }}
                  >
                    Удалить
                  </button>
                </div>
              </div>
            </div>
            <div className="chart-container">{renderChart(config, index)}</div>
          </div>
        ))}
      </div>
    </section>
  );
};
