import os
import base64
from docx import Document
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from urllib.parse import quote

def process_docx(docx_name, docx_stream):
    """
    Trích xuất văn bản, hình ảnh và hyperlink từ file DOCX, giữ nguyên thứ tự xuất hiện.

    Args:
        docx_name (str): Tên file (không bao gồm phần mở rộng)
        docx_stream (BytesIO): Stream nội dung file .docx

    Returns:
        dict: {
            "data": (str) Nội dung đã trích xuất dạng markdown (text + ảnh + hyperlink),
            "images": (list) Danh sách ảnh dạng base64 + đường dẫn để upload
        }
    """
    # Định nghĩa namespace dùng chung
    NSMAP = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    }

    doc = Document(docx_stream)

    response = {
        "data": ""
    }

    img_count = 0
    rels = doc.part.rels

    # Các biến môi trường cần thiết
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    S3_EXPLORER_URL = os.getenv("S3_EXPLORER_URL")

    for para in doc.paragraphs:
        for child in para._element:
            # 👉 Hyperlink
            if child.tag == qn("w:hyperlink"):
                rId = child.get(qn("r:id"))
                link_text = ""
                for r in child.findall(".//w:t", namespaces=NSMAP):
                    if r.text:
                        link_text += r.text
                if rId and rId in rels:
                    link_url = rels[rId]._target
                    response["data"] += f"[{link_text}]({link_url})"
            # 👉 Text & Image
            elif child.tag == qn("w:r"):
                run = child
                run_text = ""

                # Check image
                drawing = run.find(".//a:blip", namespaces=NSMAP)
                if drawing is not None:
                    rId = drawing.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                    if rId and rId in rels and rels[rId].reltype == RT.IMAGE:
                        img_count += 1
                        image_part = rels[rId].target_part
                        image_data = image_part.blob
                        ext = os.path.splitext(image_part.partname)[1].lower()
                        if not ext:
                            ext = ".png"

                        # Encode image to base64
                        image_base64 = base64.b64encode(image_data).decode("utf-8")

                        # Create markdown image path
                        s3_prefix = f"{S3_BUCKET_NAME}/images/FAQs/{docx_name}/docx_img{img_count}{ext}"
                        s3_url = f"{S3_EXPLORER_URL}/api/download?path={quote(s3_prefix, safe='')}"

                        response["data"] += f"\n![Image]({s3_url})\n"
                        # response["images"].append({
                        #     "file_path": s3_prefix,
                        #     "content": image_base64
                        # })
                else:
                    # Text thường
                    for t in run.findall(".//w:t", namespaces=NSMAP):
                        if t.text:
                            run_text += t.text
                    if run_text.strip():
                        response["data"] += run_text

        response["data"] += "\n"  # newline sau mỗi paragraph

    return response["data"]