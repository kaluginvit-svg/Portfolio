import React, { useState, useEffect } from 'react';
import { FileUpload } from './components/FileUpload';
import { FileInfo } from './components/FileInfo';
import { DataTable } from './components/DataTable';
import { Analytics } from './components/Analytics';
import { Charts } from './components/Charts';
import { AISection } from './components/AISection';
import { ExcelData, Row, ColumnTypes } from './types';
import { parseFile, analyzeData } from './utils/api';
import { detectColumnTypes } from './utils/fileParser';

function App() {
  const [excelData, setExcelData] = useState<ExcelData | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [rows, setRows] = useState<Row[]>([]);
  const [columnTypes, setColumnTypes] = useState<ColumnTypes>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [gigachatAnalysis, setGigachatAnalysis] = useState<string>('');
  const [openrouterAnalysis, setOpenrouterAnalysis] = useState<string>('');
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const handleFileSelect = async (file: File) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('Загрузка файла:', file.name, file.size, 'bytes');
      const { headers: fileHeaders, rows: fileRows, sheetName } = await parseFile(file);
      console.log('Файл загружен. Строк:', fileRows.length, 'Столбцов:', fileHeaders.length);
      
      const types = detectColumnTypes(fileHeaders, fileRows);

      setHeaders(fileHeaders);
      setRows(fileRows);
      setColumnTypes(types);
      
      setExcelData({
        fileName: file.name,
        fileSize: file.size,
        sheetName,
        totalRows: fileRows.length,
        totalColumns: fileHeaders.length,
      });

      // Автоматически запускаем анализ AI после загрузки данных
      await fetchAiAnalysis(fileHeaders, fileRows);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.error('Ошибка при чтении файла:', error);
      setError(errorMessage);
      alert('Ошибка при чтении файла: ' + errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAiAnalysis = async (headers: string[], rows: Row[]) => {
    setIsAiLoading(true);
    setAiError(null);
    setGigachatAnalysis('');
    setOpenrouterAnalysis('');
    
    try {
      const { gigachat, openrouter } = await analyzeData(headers, rows);
      setGigachatAnalysis(gigachat);
      // После получения первого анализа запускаем второй
      if (gigachat) {
        setOpenrouterAnalysis(openrouter);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.error('Ошибка при анализе AI:', error);
      setAiError(errorMessage);
    } finally {
      setIsAiLoading(false);
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch((err) => {
        console.error('Ошибка при входе в полноэкранный режим:', err);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      }).catch((err) => {
        console.error('Ошибка при выходе из полноэкранного режима:', err);
      });
    }
  };

  // Отслеживаем изменения полноэкранного режима
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  return (
    <div className={isFullscreen ? 'fullscreen-mode' : ''}>
      <header>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
          <div style={{ flex: 1 }}>
            <h1>Анализ данных</h1>
            <p className="subtitle">Загрузите CSV, Excel или PDF файл для просмотра и анализа данных</p>
          </div>
          <button 
            onClick={toggleFullscreen}
            className="btn btn-fullscreen"
            title={isFullscreen ? 'Выйти из полноэкранного режима (F11)' : 'Полноэкранный режим (F11)'}
          >
            {isFullscreen ? '⤓ Выйти из полноэкрана' : '⤢ Полный экран'}
          </button>
        </div>
      </header>

      <main>
        <FileUpload onFileSelect={handleFileSelect} />

        {isLoading && (
          <section className="upload-section" style={{ textAlign: 'center', padding: '40px' }}>
            <p>Загрузка и обработка файла...</p>
          </section>
        )}

        {error && (
          <section className="upload-section" style={{ textAlign: 'center', padding: '20px', backgroundColor: '#fee', borderColor: '#fcc' }}>
            <p style={{ color: '#c33' }}>Ошибка: {error}</p>
          </section>
        )}

        {excelData && <FileInfo data={excelData} />}

        {headers.length > 0 && rows.length > 0 && (
          <>
            <DataTable headers={headers} rows={rows} />
            <Analytics headers={headers} rows={rows} columnTypes={columnTypes} />
            <Charts headers={headers} rows={rows} columnTypes={columnTypes} />
          </>
        )}

        {(excelData || headers.length > 0) && (
          <>
            <AISection 
              title="Анализ от GigaChat"
              analysis={gigachatAnalysis}
              isLoading={isAiLoading && !gigachatAnalysis}
              error={aiError}
            />
            {gigachatAnalysis && (
              <AISection 
                title="Анализ от OpenRouter"
                analysis={openrouterAnalysis}
                isLoading={isAiLoading && !openrouterAnalysis}
                error={null}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
