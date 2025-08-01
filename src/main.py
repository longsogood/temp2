from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from typing import Annotated, Optional
import tempfile
import os
import sys
from pathlib import Path
import requests
import logging

# Thêm thư mục gốc vào sys.path
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from parser.hdsd_docx_extractor import generate_processes_file_list
from parser.hdsd_xlsx_extractor import api_call as process_hdsd_xlsx
from parser.qa_docx_extractor import api_call as process_qa_docx
from parser.qa_xlsx_extractor import api_call as process_qa_xlsx
from parser.normal_file_extractor import api_call as process_normal_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
SEND_RESPONSE_API_URL = os.getenv("SEND_RESPONSE_API_URL")


def handle_process_hdsd_docx_background(filepath: str, content: bytes):
    try:
        result = generate_processes_file_list(filepath, content)
        # payload = {"file_name": filename, "data": file_list}
        # response = requests.post(SEND_RESPONSE_API_URL, json=payload, headers={"Content-Type": "application/json"})
        # response.raise_for_status()
        if result.get("status") == "success":
            logger.info(f"\n{'='*100}\n[OK] HDSD DOCX xong: {filepath}\n{'='*100}\n")
        else:
            logger.info(f"\n{'='*100}\n[ERROR] process-docx with {filepath}: {result.get('error_code')}\n{'='*100}\n")
            if result.get("response_detail"):
                logger.error(f"[API ERROR DETAIL] {result['response_detail']}")
    except Exception as e:
        logger.error(f"\n{'='*100}\n[ERROR] process-docx with {filepath}: {e}\n{'='*100}\n")
    # finally:
    #     try:
    #         os.unlink(tmp_path)
    #     except Exception as e:
    #         logger.error(f"\n{'='*100}\n[WARNING] Không xoá được file tạm: {e}\n{'='*100}\n")


def handle_process_qa_docx_background(filepath: str, content: bytes):
    try:
        result = process_qa_docx(filepath, content)
        # response = requests.post(SEND_RESPONSE_API_URL, json={"file_name": filename, "data": result}, headers={"Content-Type": "application/json"})
        # response.raise_for_status()
        if result.get("status") == "success":
            logger.info(f"\n{'='*100}\n[OK] QA DOCX xong: {filepath}\n{'='*100}\n")
        else:
            logger.info(f"\n{'='*100}\n[ERROR] process-qa-docx with {filepath}: {result.get('error_code')}\n{'='*100}\n")
            if result.get("response_detail"):
                logger.error(f"[API ERROR DETAIL] {result['response_detail']}")
    except Exception as e:
        logger.error(f"\n{'='*100}\n[ERROR] process-qa-docx with {filepath}: {e}\n{'='*100}\n")


def handle_process_qa_xlsx_background(filename: str, content: bytes):
    try:
        result = process_qa_xlsx(filename, content)
        # response = requests.post(SEND_RESPONSE_API_URL, json={"file_name": filename, "data": result}, headers={"Content-Type": "application/json"})
        # response.raise_for_status()
        if result.get("status") == "success":
            logger.info(f"\n{'='*100}\n[OK] QA XLSX xong: {filename}\n{'='*100}\n")
        else:
            logger.info(f"\n{'='*100}\n[ERROR] process-qa-xlsx with {filename}: {result.get('error_code')}\n{'='*100}\n")
            if result.get("response_detail"):
                logger.error(f"[API ERROR DETAIL] {result['response_detail']}")
    except Exception as e:
        logger.error(f"\n{'='*100}\n[ERROR] process-qa-xlsx with {filename}: {e}\n{'='*100}\n")


def handle_process_hdsd_xlsx_background(filepath: str, content: bytes):
    try:
        result = process_hdsd_xlsx(filepath, content)
        # response = requests.post(SEND_RESPONSE_API_URL, json={"file_name": filename, "data": result}, headers={"Content-Type": "application/json"})
        # response.raise_for_status()
        if result.get("status") == "success":
            logger.info(f"\n{'='*100}\n[OK] HDSD XLSX xong: {filepath}\n{'='*100}\n")
        else:
            logger.info(f"\n{'='*100}\n[ERROR] process-xlsx with {filepath}: {result.get('error_code')}\n{'='*100}\n")
            if result.get("response_detail"):
                logger.error(f"[API ERROR DETAIL] {result['response_detail']}")
    except Exception as e:
        logger.error(f"\n{'='*100}\n[ERROR] process-xlsx with {filepath}: {e}\n{'='*100}\n")

def handle_process_normal_file_background(filename: str, content: bytes):
    try:
        result = process_normal_file(filename, content)
        # response = requests.post(SEND_RESPONSE_API_URL, json={"file_name": filename, "data": result}, headers={"Content-Type": "application/json"})
        # response.raise_for_status()
        if result.get("status") == "success":
            logger.info(f"\n{'='*100}\n[OK] NORMAL FILE xong: {filename}\n{'='*100}\n")
        else:
            logger.info(f"\n{'='*100}\n[ERROR] process-normal-file with {filename}: {result.get('error_code')}\n{'='*100}\n")
            if result.get("response_detail"):
                logger.error(f"[API ERROR DETAIL] {result['response_detail']}")
    except Exception as e:
        logger.error(f"\n{'='*100}\n[ERROR] process-normal-file with {filename}: {e}\n{'='*100}\n")

@app.post("/process-docx/")
async def process_docx_endpoint(file: Annotated[UploadFile, File(..., description="File docx QA cần xử lý")],
                                   filepath: Annotated[Optional[str], Form(description="Đường dẫn logic nếu cần")] = None,
                                   background_tasks: BackgroundTasks = BackgroundTasks()):
    if not file.filename.endswith(".docx"):
        raise HTTPException(400, detail="Invalid file format")
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            content = await file.read()
            actual_filepath = filepath if filepath else file.filename
            background_tasks.add_task(handle_process_hdsd_docx_background, actual_filepath, content)
        return {"message": f"Đã nhận file {file.filename}. Đang xử lý nền."}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/process-qa-docx/")
async def process_qa_docx_endpoint(file: Annotated[UploadFile, File(..., description="File docx QA cần xử lý")],
                                   filepath: Annotated[Optional[str], Form(description="Đường dẫn logic nếu cần")] = None,
                                   background_tasks: BackgroundTasks = BackgroundTasks()):
    if not file.filename.endswith(".docx"):
        raise HTTPException(400, detail="Invalid file format")
    try:
        content = await file.read()
        actual_filepath = filepath if filepath else file.filename
        background_tasks.add_task(handle_process_qa_docx_background, actual_filepath, content)
        return {"message": f"Đã nhận file {file.filename}. Đang xử lý QA DOCX nền."}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/process-qa-xlsx/")
async def process_qa_xlsx_endpoint(file: Annotated[UploadFile, File(..., description="File xlsx QA cần xử lý")],
                                   filepath: Annotated[Optional[str], Form(description="Đường dẫn logic nếu cần")] = None,
                                   background_tasks: BackgroundTasks = BackgroundTasks()):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(400, detail="Invalid file format")
    try:
        content = await file.read()
        actual_filepath = filepath if filepath else file.filename
        background_tasks.add_task(handle_process_qa_xlsx_background, actual_filepath, content)
        return {"message": f"Đã nhận file {file.filename}. Đang xử lý QA XLSX nền."}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/process-xlsx/")
async def process_xlsx_endpoint(file: Annotated[UploadFile, File(..., description="File xlsx HDSD cần xử lý")],
                                   filepath: Annotated[Optional[str], Form(description="Đường dẫn logic nếu cần")] = None,
                                   background_tasks: BackgroundTasks = BackgroundTasks()):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(400, detail="Invalid file format")
    try:
        content = await file.read()
        actual_filepath = filepath if filepath else file.filename
        background_tasks.add_task(handle_process_hdsd_xlsx_background, actual_filepath, content)
        return {"message": f"Đã nhận file {file.filename}. Đang xử lý HDSD XLSX nền."}
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.post("/process-normal-file/")
async def process_normal_file_endpoint(file: Annotated[UploadFile, File(..., description="Normal file cần xử lý")],
                                   filepath: Annotated[Optional[str], Form(description="Đường dẫn logic nếu cần")] = None,
                                   background_tasks: BackgroundTasks = BackgroundTasks()):
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".docx")):
        raise HTTPException(400, detail=f"Invalid file format {file.filename}")
    try:
        content = await file.read()
        actual_filepath = filepath if filepath else file.filename
        background_tasks.add_task(handle_process_normal_file_background, actual_filepath, content)
        return {"message": f"Đã nhận file {file.filename}. Đang xử lý Normal file nền."}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        raise
