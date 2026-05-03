import logging
import json
import os
import sys
import ast
import re
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from openai import OpenAI

# Load environment variables from .env file in current directory
env_path = Path.cwd() / ".env"
if not env_path.exists():
    print(f"⚠️  ERROR: .env file not found at {env_path}")
    print("Please create .env file from .env.example:")
    print("  cp .env.example .env")
    print("Then update it with your API credentials.")
    sys.exit(1)

load_dotenv(dotenv_path=env_path, verbose=True)

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize LLM
def get_llm():
    api_key = os.getenv("PROXY_API")
    base_url = os.getenv("URL")
    model_name = os.getenv("MODEL_NAME", "gpt-5.1")
    temperature = float(os.getenv("TEMPERATURE", "0.2"))
    
    if not all([api_key, base_url, model_name]):
        raise ValueError("Missing required environment variables: PROXY_API, URL, MODEL_NAME")
    
    logger.info(f"Initializing LLM: {model_name} at {base_url}")
    
    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
        temperature=temperature
    )

def get_review_llm():
    api_key = os.getenv("PROXY_API")
    base_url = os.getenv("URL")
    model_name = os.getenv("REVIEW_MODEL_NAME", "gpt-5-pro")
    temperature = float(os.getenv("REVIEW_TEMPERATURE", "0"))
    
    if not all([api_key, base_url, model_name]):
        raise ValueError("Missing required environment variables: PROXY_API, URL, REVIEW_MODEL_NAME")
    
    logger.info(f"Initializing Review LLM: {model_name} at {base_url}")
    
    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
        temperature=temperature
    )

def strip_code_fences(text):
    """Remove code fence markers from text"""
    text = re.sub(r'```python\n?', '', text)
    text = re.sub(r'```\n?', '', text)
    return text.strip()

def extract_json(text):
    """Extract JSON from text, handling code fences"""
    text = strip_code_fences(text)
    
    # Try to find JSON object in text
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Try direct parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise ValueError(f"Invalid JSON response: {text[:200]}")

def validate_python_syntax(code):
    """Validate Python code syntax using ast"""
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, str(e)

def is_fastapi_code_complete(code):
    """Check if code looks like a complete FastAPI app"""
    if not code or not code.strip():
        return False
    essential_checks = ["FastAPI(", "app =", "@app."]
    return all(check in code for check in essential_checks)

def validate_fastapi_code(code):
    """Validate syntax + minimal FastAPI app structure"""
    is_valid_syntax, syntax_error = validate_python_syntax(code)
    if not is_valid_syntax:
        return False, f"Python syntax error: {syntax_error}"
    if not is_fastapi_code_complete(code):
        return False, "Code is incomplete: missing required FastAPI app markers (FastAPI(, app =, @app.)"
    return True, None

def run_review_via_responses_api(review_prompt, code):
    """Fallback review call via /v1/responses for responses-only models"""
    api_key = os.getenv("PROXY_API")
    base_url = os.getenv("URL")
    model_name = os.getenv("REVIEW_MODEL_NAME", "gpt-5-pro")
    temperature = float(os.getenv("REVIEW_TEMPERATURE", "0"))

    client = OpenAI(api_key=api_key, base_url=base_url)
    input_text = review_prompt.format(code=code)
    response = client.responses.create(
        model=model_name,
        temperature=temperature,
        input=input_text
    )
    return response.output_text

def stage_1_analyze_task(llm, task_description):
    """Stage 1: Task Analysis"""
    logger.info("Stage 1: Analyzing task...")
    
    prompt = PromptTemplate(
        input_variables=["task"],
        template="""Analyze the following task for creating a FastAPI service and return a JSON object with this exact structure:
{{
    "service_name": "string",
    "main_goal": "string",
    "entities": ["list of main entities"],
    "endpoints": ["list of endpoint paths"],
    "request_schemas": {{"endpoint": "description"}},
    "response_schemas": {{"endpoint": "description"}},
    "database_required": boolean,
    "auth_required": boolean,
    "business_rules": ["list of rules"],
    "validation_rules": ["list of validation rules"],
    "edge_cases": ["list of edge cases"]
}}

Task: {task}

Return only valid JSON, no additional text."""
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.run(task=task_description)
    
    analysis = extract_json(response)
    logger.info(f"Task analysis completed: {analysis['service_name']}")
    return analysis

def stage_2_select_tools(llm, analysis):
    """Stage 2: Tool Selection"""
    logger.info("Stage 2: Selecting tools...")
    
    prompt = PromptTemplate(
        input_variables=["analysis"],
        template="""Based on this task analysis, select appropriate tools and frameworks for the FastAPI service:
{analysis}

Return a JSON object with this exact structure:
{{
    "framework": "FastAPI",
    "data_validation": "Pydantic",
    "orm": "SQLAlchemy or null",
    "database": "SQLite or PostgreSQL or null",
    "server": "uvicorn",
    "project_layout": "standard or modular",
    "extra_dependencies": ["list of additional packages"],
    "reasoning_short": "brief explanation"
}}

Return only valid JSON, no additional text."""
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.run(analysis=json.dumps(analysis))
    
    tools = extract_json(response)
    logger.info(f"Tools selected: {tools['framework']}, ORM: {tools['orm']}")
    return tools

def stage_3_generate_code(llm, analysis, tools):
    """Stage 3: Code Generation"""
    logger.info("Stage 3: Generating FastAPI service code...")
    
    database_section = ""
    if analysis.get("database_required"):
        database_section = """
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:///./service.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ServiceDB:
    def __init__(self):
        Base.metadata.create_all(bind=engine)

db = ServiceDB()
"""
    
    auth_section = ""
    if analysis.get("auth_required"):
        auth_section = """
from fastapi.security import HTTPBearer, HTTPAuthCredentials
security = HTTPBearer()
"""
    
    prompt = PromptTemplate(
        input_variables=["analysis", "tools", "db_section", "auth_section"],
        template="""Generate a complete, production-ready FastAPI service code based on this analysis and tools:

Analysis: {analysis}
Tools: {tools}

Database initialization (if needed):
{db_section}

Auth initialization (if needed):
{auth_section}

Requirements:
1. Create a complete, runnable FastAPI service (Python 3.11+)
2. Use Pydantic for request/response validation
3. Implement all endpoints from the analysis
4. Include proper error handling
5. Include type hints
6. No TODO comments, no placeholders
7. Must run without manual modifications
8. Include proper imports
9. Include main execution block with uvicorn.run()

IMPORTANT: return the FULL contents of a single runnable main.py file
- do not summarize
- do not omit parts of the code
- do not replace code with comments
- return only Python code

Return complete, ready-to-run Python code. Start with imports, then models, then app initialization, then routes, then main section.
No code fences, no markdown formatting."""
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    code = chain.run(
        analysis=json.dumps(analysis),
        tools=json.dumps(tools),
        db_section=database_section,
        auth_section=auth_section
    )
    
    code = strip_code_fences(code)
    logger.info("Code generation completed")
    return code

def stage_4_review_code(review_llm, code):
    """Stage 4: Code Review and Correction"""
    logger.info("Stage 4: Reviewing and validating code...")
    
    # First, check generated code locally before review
    is_valid, error = validate_fastapi_code(code)
    if not is_valid:
        logger.warning(f"Generated code validation warning before review: {error}")
    
    prompt = PromptTemplate(
        input_variables=["code"],
        template="""Review and fix this FastAPI service code. Check for:
1. Python syntax errors
2. Missing imports
3. FastAPI app initialization
4. API routes definition
5. Request/response models
6. Main execution block
7. Any logical errors

IMPORTANT: You MUST return the FULL, COMPLETE Python code.
- If the code is correct, return the full original code without any omissions or summaries.
- If the code has issues, fix them and return the full corrected code.
- NEVER return only a comment, only a note, only a summary, or only a validation message.
- If you add a comment like "# Code validated successfully", it can only be the first line BEFORE the full code.
- Return ONLY Python code, no markdown, no code fences, no explanations.

Code to review:
{code}

Return the full Python code:"""
    )
    
    chain = LLMChain(llm=review_llm, prompt=prompt)
    try:
        reviewed_code = chain.run(code=code)
    except Exception as e:
        error_text = str(e)
        if "only supported in v1/responses" in error_text:
            logger.warning("Review model requires /v1/responses. Retrying review via responses API.")
            reviewed_code = run_review_via_responses_api(prompt.template, code)
        else:
            raise
    
    reviewed_code = strip_code_fences(reviewed_code)
    
    # Validate reviewed code and fallback when review output is incomplete
    is_valid_reviewed, reviewed_error = validate_fastapi_code(reviewed_code)
    if not is_valid_reviewed:
        logger.warning(f"Review returned invalid or incomplete code ({reviewed_error}). Falling back to generated code.")
        is_valid_generated, generated_error = validate_fastapi_code(code)
        if is_valid_generated:
            logger.info("Fallback to stage 3 generated code succeeded")
            reviewed_code = code
        else:
            logger.error(f"Both reviewed and generated code are invalid. Review error: {reviewed_error}; generated error: {generated_error}")
            raise ValueError(
                "Review returned incomplete/invalid code and fallback generated code is also invalid. "
                f"Review error: {reviewed_error}. Generated error: {generated_error}."
            )
    
    logger.info("Code review completed successfully")
    return reviewed_code

def save_generated_code(code, output_dir="generated_api"):
    """Save generated code to file"""
    Path(output_dir).mkdir(exist_ok=True)
    
    output_file = Path(output_dir) / "main.py"
    output_file.write_text(code)
    
    logger.info(f"Generated code saved to {output_file}")
    return str(output_file)

def main(task_description):
    """Main execution of 4-stage pipeline"""
    try:
        logger.info("=" * 60)
        logger.info("Starting FastAPI Service Generation Pipeline")
        logger.info("=" * 60)
        
        llm = get_llm()
        review_llm = get_review_llm()
        
        # Stage 1: Analyze
        analysis = stage_1_analyze_task(llm, task_description)
        
        # Stage 2: Select Tools
        tools = stage_2_select_tools(llm, analysis)
        
        # Stage 3: Generate Code
        generated_code = stage_3_generate_code(llm, analysis, tools)
        
        # Stage 4: Review
        final_code = stage_4_review_code(review_llm, generated_code)
        
        # Save result
        output_path = save_generated_code(final_code)
        
        logger.info("=" * 60)
        logger.info(f"Pipeline completed successfully!")
        logger.info(f"Generated service: {analysis['service_name']}")
        logger.info(f"Output file: {output_path}")
        logger.info("=" * 60)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py '<task_description>'")
        print("Example: python script.py 'Create a task management API with users and tasks'")
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    main(task)
