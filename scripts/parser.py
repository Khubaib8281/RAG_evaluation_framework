import os
import re
import tempfile
import sys  
import pdfplumber
from PyPDF2 import PdfReader
from langchain_community.document_loaders import UnstructuredFileLoader
from pdf2image import convert_from_path
import pytesseract  
from langchain.text_splitter import RecursiveCharacterTextSplitter
from docx import Document
import logging
logger = logging.getLogger(__name__)
import docx2txt   

   
# ------------------------
# 1. Text Cleaning
# ------------------------
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)   # collapse multiple spaces/newlines
    text = text.strip()
    return text


# ------------------------
# 2. PDF Extractors
# ------------------------
def extract_with_pdfplumber(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return clean_text(text)


def extract_with_pypdf(file_path: str) -> str:
    text = ""
    reader = PdfReader(file_path)
    for page in reader.pages:
        text += page.extract_text() or ""
    return clean_text(text)


def extract_with_unstructured(file_path: str) -> str:
    loader = UnstructuredFileLoader(file_path)
    docs = loader.load()
    text = " ".join([d.page_content for d in docs])
    return clean_text(text)


def extract_with_ocr(file_path: str) -> str:
    text = ""
    images = convert_from_path(file_path)
    for img in images:
        text += pytesseract.image_to_string(img)
    return clean_text(text)


# ------------------------
# 3. DOCX Extractors
# ------------------------
def extract_with_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    text = "\n".join([p.text for p in doc.paragraphs])
    return clean_text(text)


def extract_with_docx2txt(file_path: str) -> str:
    text = docx2txt.process(file_path)
    return clean_text(text)


# ------------------------
# 4. Dispatcher
# ------------------------
def extract_text_from_file(uploaded_file) -> tuple[str, str]:
    """
    Handles both Streamlit UploadedFile and local file paths.
    Returns (extracted_text, message)
    """
    file_path = None
    temp_created = False
    try:
        # If it's a Streamlit UploadedFile (file-like object)
        if hasattr(uploaded_file, "name") and not isinstance(uploaded_file, str):
            # Get extension from uploaded file name
            ext = os.path.splitext(uploaded_file.name)[1].lower()

            # Save to temp file so extractors can read it
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(uploaded_file.getbuffer())
                file_path = tmp.name
                temp_created = True
        else:
            # Already a real file path
            file_path = uploaded_file
            ext = os.path.splitext(file_path)[1].lower()

        # Select extractors based on extension
        if ext == ".pdf":
            extractors = [
                ("pdfplumber", extract_with_pdfplumber),
                ("pypdf", extract_with_pypdf),
                ("unstructured", extract_with_unstructured),
                ("ocr", extract_with_ocr),
            ]
        elif ext == ".docx":
            extractors = [
                ("python-docx", extract_with_docx),
                ("docx2txt", extract_with_docx2txt),
                ("unstructured", extract_with_unstructured),
            ]
        else:
            return "", f"❌ Unsupported file type: {ext}"

        # Try extractors in order
        for name, extractor in extractors:
            try:
                text = extractor(file_path)
                if len(text) > 200:  # sanity check
                    return text, f"Extracted using {name}, length={len(text)}"
                else:
                    logger.debug("%s returned short chunk (len=%s)", name, len(text))
            except Exception as e:
                logger.exception("Extractor %s failed: %s", name, e)

        return "", f"⚠️ Could not extract text from {uploaded_file.name if hasattr(uploaded_file,'name') else file_path}"

    finally:
        if temp_created and file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                logger.exception("Failed to remove temp file %s", file_path)
