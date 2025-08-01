import streamlit as st
import pandas as pd
import io
import tempfile
import os
from pathlib import Path
import sys

# Thêm đường dẫn để import các module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser.normal_file_extractor import process_file
from utils.normal_file.xlsx_utils import process_xlsx
from utils.normal_file.docx_utils import process_docx
from utils.normal_file.pdf_utils import process_pdf

# Cấu hình trang
st.set_page_config(
    page_title="File Processor Demo",
    page_icon="📄",
    layout="wide"
)

# Tiêu đề
st.title("📄 Demo Xử Lý File - Normal File Extractor")
st.markdown("---")

# Sidebar
st.sidebar.header("🎛️ Cài đặt")
st.sidebar.markdown("### Các loại file được hỗ trợ:")
st.sidebar.markdown("- 📊 Excel (.xlsx)")
st.sidebar.markdown("- 📝 Word (.docx)")
st.sidebar.markdown("- 📄 PDF (.pdf)")

# Tabs
tab1, tab2, tab3 = st.tabs(["📤 Upload File", "🔧 Test Utils", "📊 Kết quả"])

with tab1:
    st.header("📤 Upload và Xử Lý File")
    
    uploaded_file = st.file_uploader(
        "Chọn file để xử lý",
        type=['xlsx', 'docx', 'pdf'],
        help="Hỗ trợ file Excel, Word và PDF"
    )
    
    if uploaded_file is not None:
        # Hiển thị thông tin file
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tên file", uploaded_file.name)
        with col2:
            st.metric("Kích thước", f"{uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.metric("Loại file", uploaded_file.type or "Unknown")
        
        # Nút xử lý
        if st.button("🚀 Xử lý File", type="primary"):
            with st.spinner("Đang xử lý file..."):
                try:
                    # Đọc nội dung file
                    file_content = uploaded_file.read()
                    
                    # Xử lý file
                    result = process_file(uploaded_file.name, file_content)
                    
                    if result:
                        # Lưu kết quả vào session state
                        st.session_state['processed_content'] = result
                        st.session_state['file_name'] = uploaded_file.name
                        st.success("✅ Xử lý file thành công!")
                        
                        # Hiển thị preview
                        st.subheader("📋 Preview kết quả:")
                        st.text_area(
                            "Nội dung đã xử lý:",
                            value=result,
                            height=300,
                            disabled=True
                        )
                    else:
                        st.error("❌ Không thể xử lý file này!")
                        
                except Exception as e:
                    st.error(f"❌ Lỗi khi xử lý file: {str(e)}")

with tab2:
    st.header("🔧 Test Các Utils Riêng Biệt")
    
    # Test XLSX Utils
    st.subheader("📊 Test XLSX Utils")
    xlsx_file = st.file_uploader("Chọn file Excel", type=['xlsx'], key="xlsx_test")
    
    if xlsx_file:
        if st.button("Test XLSX Utils", key="btn_xlsx"):
            with st.spinner("Đang test XLSX utils..."):
                try:
                    content = xlsx_file.read()
                    result = process_xlsx(xlsx_file.name, content)
                    st.success("✅ XLSX Utils hoạt động tốt!")
                    st.text_area("Kết quả XLSX:", value=result, height=200, disabled=True)
                except Exception as e:
                    st.error(f"❌ Lỗi XLSX Utils: {str(e)}")
    
    # Test DOCX Utils
    st.subheader("📝 Test DOCX Utils")
    docx_file = st.file_uploader("Chọn file Word", type=['docx'], key="docx_test")
    
    if docx_file:
        if st.button("Test DOCX Utils", key="btn_docx"):
            with st.spinner("Đang test DOCX utils..."):
                try:
                    content = docx_file.read()
                    result = process_docx(docx_file.name.replace('.docx', ''), io.BytesIO(content))
                    st.success("✅ DOCX Utils hoạt động tốt!")
                    st.text_area("Kết quả DOCX:", value=result, height=200, disabled=True)
                except Exception as e:
                    st.error(f"❌ Lỗi DOCX Utils: {str(e)}")
    
    # Test PDF Utils
    st.subheader("📄 Test PDF Utils")
    pdf_file = st.file_uploader("Chọn file PDF", type=['pdf'], key="pdf_test")
    
    if pdf_file:
        if st.button("Test PDF Utils", key="btn_pdf"):
            with st.spinner("Đang test PDF utils..."):
                try:
                    content = pdf_file.read()
                    result = process_pdf(content)
                    st.success("✅ PDF Utils hoạt động tốt!")
                    st.text_area("Kết quả PDF:", value=result, height=200, disabled=True)
                except Exception as e:
                    st.error(f"❌ Lỗi PDF Utils: {str(e)}")

with tab3:
    st.header("📊 Kết Quả Xử Lý")
    
    if 'processed_content' in st.session_state:
        st.subheader(f"📄 Kết quả: {st.session_state.get('file_name', 'Unknown')}")
        
        # Tùy chọn hiển thị
        display_option = st.selectbox(
            "Chọn cách hiển thị:",
            ["Raw Text", "Markdown", "Download"]
        )
        
        if display_option == "Raw Text":
            st.text_area(
                "Nội dung thô:",
                value=st.session_state['processed_content'],
                height=400,
                disabled=True
            )
        elif display_option == "Markdown":
            st.markdown(st.session_state['processed_content'])
        elif display_option == "Download":
            # Tạo file để download
            processed_file_name = st.session_state.get('file_name', 'processed').replace('.xlsx', '.txt').replace('.docx', '.txt').replace('.pdf', '.txt')
            
            st.download_button(
                label="📥 Tải xuống kết quả",
                data=st.session_state['processed_content'],
                file_name=f"processed_{processed_file_name}",
                mime="text/plain"
            )
            
            # Hiển thị thống kê
            content = st.session_state['processed_content']
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Số ký tự", len(content))
            with col2:
                st.metric("Số dòng", len(content.split('\n')))
            with col3:
                st.metric("Số từ", len(content.split()))
    else:
        st.info("ℹ️ Chưa có kết quả xử lý nào. Hãy upload và xử lý file trong tab đầu tiên!")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>🔧 Được phát triển với Streamlit | 📧 Hỗ trợ: support@example.com</p>
    </div>
    """,
    unsafe_allow_html=True
) 