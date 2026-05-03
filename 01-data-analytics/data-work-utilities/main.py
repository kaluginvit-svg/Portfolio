from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import Dict, List, Any
from pydantic import BaseModel
import pdfplumber
import pandas as pd
import io
import json
from urllib.parse import quote
from ai_service import analyze_table_data
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

app = FastAPI(title="Data Analyzer API")

# Настройка CORS для работы с React фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Data Analyzer API is running"}


@app.post("/api/parse-file")
async def parse_file(file: UploadFile = File(...)):
    """
    Парсит загруженный файл (PDF, Excel, CSV) и возвращает данные в формате,
    совместимом с фронтендом
    """
    try:
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ''
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(status_code=400, detail="Файл пуст или не был загружен")
        
        if file_extension == 'pdf':
            return await parse_pdf(file_content, file.filename or 'unknown.pdf')
        elif file_extension in ['xlsx', 'xls']:
            return await parse_excel(file_content, file_extension)
        elif file_extension == 'csv':
            return await parse_csv(file_content, file.filename or 'unknown.csv')
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый формат файла: .{file_extension}. Поддерживаются: .pdf, .xlsx, .xls, .csv"
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Ошибка при обработке файла: {str(e)}"
        print(f"Ошибка parse_file: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_detail)


async def parse_pdf(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Парсит PDF файл с помощью pdfplumber и извлекает первую таблицу"""
    try:
        pdf_file = io.BytesIO(file_content)
        
        with pdfplumber.open(pdf_file) as pdf:
            if len(pdf.pages) == 0:
                raise HTTPException(status_code=400, detail="PDF файл не содержит страниц")
            
            # Получаем первую страницу
            first_page = pdf.pages[0]
            
            # Извлекаем первую таблицу
            tables = first_page.extract_tables()
            
            if not tables or len(tables) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="На первой странице PDF не найдено таблиц. Попробуйте другой файл или убедитесь, что таблица присутствует на первой странице."
                )
            
            # Берем первую таблицу
            table = tables[0]
            
            if not table or len(table) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Таблица пуста или имеет нестандартный формат"
                )
            
            # Преобразуем таблицу в нужный формат
            # Первая строка - заголовки
            headers = [str(cell).strip() if cell is not None else f"Column {i+1}" 
                      for i, cell in enumerate(table[0])]
            
            # Остальные строки - данные
            rows = []
            for row in table[1:]:
                row_obj = {}
                for i, header in enumerate(headers):
                    cell_value = row[i] if i < len(row) and row[i] is not None else None
                    # Преобразуем в число, если возможно
                    if cell_value is not None:
                        cell_str = str(cell_value).strip()
                        if cell_str:
                            try:
                                # Пытаемся преобразовать в число
                                num_value = float(cell_str.replace(',', '.'))
                                row_obj[header] = num_value
                            except (ValueError, AttributeError):
                                row_obj[header] = cell_str
                        else:
                            row_obj[header] = None
                    else:
                        row_obj[header] = None
                rows.append(row_obj)
            
            if len(headers) == 0 or len(rows) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Не удалось извлечь данные из таблицы. Таблица может быть пустой или иметь нестандартный формат."
                )
            
            return {
                "headers": headers,
                "rows": rows,
                "sheetName": "PDF Page 1"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при чтении PDF файла: {str(e)}")


async def parse_excel(file_content: bytes, file_extension: str) -> Dict[str, Any]:
    """Парсит Excel файл с помощью pandas"""
    try:
        # Определяем движок в зависимости от расширения
        engine = 'openpyxl' if file_extension == 'xlsx' else 'xlrd'
        
        excel_file = io.BytesIO(file_content)
        df = pd.read_excel(excel_file, engine=engine, sheet_name=0)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Файл пуст")
        
        # Получаем имя первого листа
        excel_file.seek(0)
        xls_file = pd.ExcelFile(excel_file, engine=engine)
        sheet_name = xls_file.sheet_names[0]
        
        # Преобразуем в нужный формат
        headers = [str(col) for col in df.columns]
        rows = []
        
        for _, row in df.iterrows():
            row_obj = {}
            for header in headers:
                value = row[header]
                # Преобразуем NaN в None и datetime в строки
                if pd.isna(value):
                    row_obj[header] = None
                elif isinstance(value, pd.Timestamp):
                    row_obj[header] = value.isoformat()
                elif hasattr(value, 'item'):  # numpy типы
                    row_obj[header] = value.item()
                else:
                    row_obj[header] = value
            rows.append(row_obj)
        
        return {
            "headers": headers,
            "rows": rows,
            "sheetName": sheet_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при чтении Excel файла: {str(e)}")


async def parse_csv(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Парсит CSV файл с помощью pandas"""
    try:
        # Определяем кодировку (пробуем utf-8, затем cp1251 для русских файлов)
        encodings = ['utf-8', 'cp1251', 'latin-1', 'iso-8859-1']
        df = None
        last_error = None
        
        for encoding in encodings:
            try:
                csv_file = io.BytesIO(file_content)
                # Пробуем разные варианты разделителей
                try:
                    df = pd.read_csv(csv_file, encoding=encoding, sep=',', on_bad_lines='skip')
                except Exception:
                    csv_file.seek(0)
                    try:
                        df = pd.read_csv(csv_file, encoding=encoding, sep=';', on_bad_lines='skip')
                    except Exception:
                        csv_file.seek(0)
                        df = pd.read_csv(csv_file, encoding=encoding, sep='\t', on_bad_lines='skip')
                break
            except UnicodeDecodeError as e:
                last_error = e
                continue
            except Exception as e:
                last_error = e
                continue
        
        if df is None:
            error_msg = f"Не удалось определить кодировку CSV файла"
            if last_error:
                error_msg += f": {str(last_error)}"
            raise HTTPException(status_code=400, detail=error_msg)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Файл пуст или не содержит данных")
        
        # Преобразуем в нужный формат
        headers = [str(col) for col in df.columns]
        rows = []
        
        for _, row in df.iterrows():
            row_obj = {}
            for header in headers:
                value = row[header]
                # Преобразуем NaN в None и datetime в строки
                if pd.isna(value):
                    row_obj[header] = None
                elif isinstance(value, pd.Timestamp):
                    row_obj[header] = value.isoformat()
                elif hasattr(value, 'item'):  # numpy типы
                    row_obj[header] = value.item()
                else:
                    row_obj[header] = value
            rows.append(row_obj)
        
        return {
            "headers": headers,
            "rows": rows,
            "sheetName": "CSV"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при чтении CSV файла: {str(e)}")


# Модель для запроса анализа данных
class AnalyzeDataRequest(BaseModel):
    headers: List[str]
    rows: List[Dict[str, Any]]


@app.post("/api/analyze-data")
async def analyze_data(request: AnalyzeDataRequest = Body(...)):
    """
    Анализирует табличные данные с помощью AI (GigaChat и OpenRouter)
    Принимает первые 50 строк таблицы и возвращает аналитические ответы от обоих агентов
    """
    try:
        headers = request.headers
        rows = request.rows
        
        if not headers or not rows:
            raise HTTPException(status_code=400, detail="Заголовки и строки данных не могут быть пустыми")
        
        # Отправляем данные в AI для анализа (получаем оба анализа)
        analysis_results = await analyze_table_data(headers, rows, max_rows=50)
        
        return {
            "gigachat": analysis_results.get("gigachat", ""),
            "openrouter": analysis_results.get("openrouter", "")
        }
        
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе данных: {str(e)}")


class GeneratePdfRequest(BaseModel):
    title: str
    content: str


@app.post("/api/generate-pdf")
async def generate_pdf(request: GeneratePdfRequest = Body(...)):
    """
    Генерирует PDF файл из текста анализа
    """
    try:
        # Создаем PDF в памяти
        pdf_bytes = io.BytesIO()
        doc = SimpleDocTemplate(pdf_bytes, pagesize=A4,
                               rightMargin=20*mm, leftMargin=20*mm,
                               topMargin=20*mm, bottomMargin=20*mm)
        
        # Получаем стили
        styles = getSampleStyleSheet()
        
        # Для поддержки кириллицы используем стандартные шрифты reportlab
        # Они поддерживают Unicode через встроенную обработку
        
        # Создаем кастомные стили
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            textColor='#000000'
        )
        
        date_style = ParagraphStyle(
            'CustomDate',
            parent=styles['Normal'],
            fontSize=10,
            textColor='#666666',
            spaceAfter=20
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            textColor='#000000',
            alignment=4  # JUSTIFY
        )
        
        # Строим содержимое PDF
        story = []
        
        # Функция для экранирования текста для Paragraph
        def escape_for_paragraph(text):
            """Экранирует текст для использования в Paragraph"""
            # Экранируем HTML-сущности
            text = xml_escape(text, {'"': '&quot;', "'": '&apos;'})
            return text
        
        # Заголовок
        story.append(Paragraph(escape_for_paragraph(request.title), title_style))
        story.append(Spacer(1, 6*mm))
        
        # Дата
        date_str = datetime.now().strftime("%Y-%m-%d")
        story.append(Paragraph(escape_for_paragraph(f"Дата создания: {date_str}"), date_style))
        story.append(Spacer(1, 6*mm))
        
        # Обрабатываем текст
        normalized_text = request.content.replace('\r\n', '\n').replace('\r', '\n')
        paragraphs = normalized_text.split('\n\n')
        
        for para in paragraphs:
            if para.strip():
                # Разбиваем абзац на строки
                lines = para.split('\n')
                for line in lines:
                    if line.strip():
                        # Экранируем текст для Paragraph
                        escaped_line = escape_for_paragraph(line.strip())
                        story.append(Paragraph(escaped_line, body_style))
                story.append(Spacer(1, 3*mm))
        
        # Генерируем PDF
        doc.build(story)
        pdf_bytes.seek(0)
        
        # Формируем имя файла (безопасное для URL, только латиница и цифры)
        safe_title = "".join(c if c.isalnum() or c in ('-', '_') else '-' for c in request.title[:50])
        filename = f"{safe_title}-{date_str}.pdf"
        
        return Response(
            content=pdf_bytes.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании PDF: {str(e)}")
