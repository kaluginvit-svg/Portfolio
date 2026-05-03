import React from 'react';
import { generatePdf } from '../utils/api';

interface AISectionProps {
  title?: string;
  analysis?: string;
  isLoading?: boolean;
  error?: string | null;
}

const downloadAnalysisPDF = async (analysis: string, title: string = 'Анализ от нейросети') => {
  try {
    await generatePdf(title, analysis);
  } catch (error) {
    console.error('Ошибка при создании PDF:', error);
    const errorMessage = error instanceof Error ? error.message : 'Неизвестная ошибка';
    alert(`Ошибка при создании PDF файла: ${errorMessage}`);
  }
};

export const AISection: React.FC<AISectionProps> = ({ title = 'Анализ от нейросети', analysis, isLoading, error }) => {
  return (
    <section className="ai-section">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
        <h2>{title}</h2>
        {analysis && !isLoading && !error && (
          <button
            onClick={() => downloadAnalysisPDF(analysis, title)}
            style={{
              padding: '8px 16px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#45a049'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#4CAF50'}
          >
            📄 Скачать PDF
          </button>
        )}
      </div>
      <div className="ai-content">
        {isLoading && (
          <div className="ai-loading">Анализ данных нейросетью...</div>
        )}
        {error && (
          <div className="ai-error" style={{ color: '#c33', padding: '10px', backgroundColor: '#fee' }}>
            Ошибка: {error}
          </div>
        )}
        {!isLoading && !error && analysis && (
          <div className="ai-analysis" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
            {analysis}
          </div>
        )}
        {!isLoading && !error && !analysis && (
          <div className="ai-placeholder">Здесь появится вывод от нейросети</div>
        )}
      </div>
    </section>
  );
};
