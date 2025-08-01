import fitz
import re
import base64
import sys

def is_list_item(line):
    return re.match(r"^\s*([-•*]|\d+[\.|\)]|\d+\s)", line)

def process_pdf(pdf_bytes):
    if not pdf_bytes:
        raise ValueError("Không có dữ liệu PDF được cung cấp")
        
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Không thể mở file PDF: {str(e)}")
        
    markdown_lines = []
    images = []
    
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            img_list = page.get_images(full=True)
            img_xrefs = [img[0] for img in img_list]
            img_idx = 0
            img_count = 0
            blocks_sorted = sorted(blocks, key=lambda b: b["bbox"][1])
            
            for b in blocks_sorted:
                if b["type"] == 0:
                    text = ""
                    for line in b["lines"]:
                        line_text = " ".join([span["text"] for span in line["spans"]]).strip()
                        if line_text:
                            if is_list_item(line_text):
                                text += "\n" + line_text + "\n"
                            else:
                                text += line_text + "\n"
                    if text:
                        markdown_lines.append(text.strip())
                        
                elif b["type"] == 1:
                    if img_idx < len(img_xrefs):
                        try:
                            img_count += 1
                            xref = img_xrefs[img_idx]
                            img_idx += 1
                            base_image = doc.extract_image(xref)
                            if not base_image:
                                continue
                            image_bytes = base_image["image"]
                            img_format = base_image.get("ext", "png")
                            img_b64 = base64.b64encode(image_bytes).decode()
                            # Markdown nhúng ảnh base64
                            markdown_img = f'![page{page_num+1}_img{img_count}](data:image/{img_format};base64,{img_b64})'
                            markdown_lines.append(markdown_img)
                            images.append({
                                "name": f"page{page_num+1}_img{img_count}.{img_format}",
                                "content": img_b64,
                                "type": f"image/{img_format}"
                            })
                        except Exception as e:
                            print(f"Lỗi khi xử lý hình ảnh: {str(e)}", file=sys.stderr)
                            continue
    finally:
        doc.close()
        
    if not markdown_lines and not images:
        raise ValueError("Không thể trích xuất nội dung từ file PDF")
        
    return "\n\n".join(markdown_lines)
