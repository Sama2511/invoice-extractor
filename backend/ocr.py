import pymupdf
import pytesseract
from PIL import Image
import io
from dotenv import load_dotenv
load_dotenv()

def extract_TEXT_from_pdf(pdf):
    try:
        if isinstance(pdf ,bytes):
            doc = pymupdf.open(stream=pdf, filetype='pdf')
        else:
            doc = pymupdf.open(pdf)
    except Exception as e:
        raise ValueError(f"Could not open pdf: {e}")
    pages= []
    for page in doc: 
        text = page.get_text()
        if len(text.strip()) == 0:
            raise ValueError('PDF page is empty')
        if len(text.strip())< 50:
            mat = pymupdf.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img)
            pages.append(text)
        else:
            pages.append(text)
        
    return pages 

