import logging
import os
import json
import requests
from pathlib import Path
import io
from dotenv import load_dotenv

SEND_RESPONSE_API_URL = os.getenv("SEND_RESPONSE_API_URL")

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def log_with_file(level, message, file_name=None, max_content_length=200):
    """Ghi log với thông tin file"""
    prefix = ""
    if file_name:
        prefix += f"[File: {file_name}] "
    if isinstance(message, str) and len(message) > max_content_length:
        message = message[:max_content_length] + "... [đã cắt bớt]"
    logger.log(level, prefix + message)

def sanitize_path_component(name):
    """
    Chuyển đổi một thành phần đường dẫn thành dạng an toàn cho filesystem.
    """
    import re
    # Loại bỏ ký tự điều khiển
    name = re.sub(r'[\x00-\x1f\x7f]', '', name)
    # Thay thế các ký tự không hợp lệ bằng _
    name = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', name)
    # Thay thế khoảng trắng liên tiếp bằng _
    name = re.sub(r'\s+', '_', name)
    # Loại bỏ dấu chấm/dấu cách ở đầu/cuối
    name = name.strip(" .")
    # Cắt bớt nếu quá dài
    name = name[:100]
    # Tránh tên file đặc biệt trên Windows
    reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {f'COM{i}' for i in range(1, 10)} | {f'LPT{i}' for i in range(1, 10)}
    if name.upper() in reserved:
        name = f"_{name}_"
    return name or "unnamed"

def create_response(filepath, content): 
    """Tạo response cho API"""
    return {
        "file_name": str(filepath),
        "data": [
            {
                "file_path": os.path.join(
                    "processed",
                    str(filepath.parent) if str(filepath.parent) != "." else None,
                    f"{filepath.stem}.txt"
                ) if str(filepath.parent) != "." else os.path.join(
                    "processed",
                    f"{filepath.stem}.txt"
                ),
                "content": content
            }
        ],
    }

def process_file(filepath, file_content):
    """
    Xử lý file dựa trên phần mở rộng và trả về nội dung đã xử lý
    
    Args:
        filepath (Path): Đường dẫn file
        file_content (bytes): Nội dung file dạng bytes
        
    Returns:
        str: Nội dung đã xử lý dạng markdown
    """
    filepath = Path(filepath)
    
    try:
        match filepath.suffix.lower():
            case ".xlsx":
                log_with_file(logging.INFO, f"Xử lý file xlsx: {filepath.name}", file_name=filepath.name)
                data = process_xlsx(filepath.name, file_content)
                log_with_file(logging.INFO, f"Đã xử lý xong file xlsx", file_name=filepath.name)
                
            case ".docx":
                log_with_file(logging.INFO, f"Xử lý file docx: {filepath.name}", file_name=filepath.name)
                data = process_docx(filepath.stem, io.BytesIO(file_content))
                log_with_file(logging.INFO, f"Đã xử lý xong file docx", file_name=filepath.name)
                
            case ".pdf":
                log_with_file(logging.INFO, f"Xử lý file pdf: {filepath.name}", file_name=filepath.name)
                data = process_pdf(file_content)
                log_with_file(logging.INFO, f"Đã xử lý xong file pdf", file_name=filepath.name)
                
            case _:
                logger.warning(f"File không được hỗ trợ: {filepath.name}")
                return None
                
        return data
        
    except Exception as e:
        log_with_file(logging.ERROR, f"Lỗi khi xử lý file {filepath.name}: {e}", file_name=filepath.name)
        raise

def api_call(filepath, file_content):
    """
    Xử lý file và gửi kết quả qua API
    
    Args:
        filepath: Đường dẫn file
        file_content: Nội dung file dạng bytes
        
    Returns:
        dict: Kết quả xử lý
    """
    try:
        # Xử lý file
        data = process_file(filepath, file_content)
        
        if data is None:
            return {"status": "error", "error": "File không được hỗ trợ"}
        
        log_with_file(logging.INFO, "Đang tạo file đầu ra...", file_name=filepath.name)
        response = create_response(filepath, data)

        # Gửi kết quả qua API
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        send_response = requests.post(
            SEND_RESPONSE_API_URL, 
            headers=headers, 
            data=json.dumps(response), 
            verify=False
        )
        
        if send_response.status_code == 200 and send_response.json().get("success"):
            return {"status": "success"}
        else:
            log_with_file(
                logging.ERROR, 
                f"Lỗi gửi API: status_code={send_response.status_code}, response={send_response.text}", 
                file_name=filepath.name
            )
            return {
                "status": "error", 
                "error_code": send_response.status_code, 
                "response_detail": send_response.text
            }
            
    except Exception as e:
        log_with_file(logging.ERROR, f"Lỗi trong quá trình xử lý: {e}", file_name=filepath.name)
        return {"status": "error", "error": str(e)}
