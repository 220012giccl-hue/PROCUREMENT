import os
import mimetypes
from pathlib import Path

class FileProcessor:
    def __init__(self, upload_dir="uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
    def save_file(self, file_content, filename):
        file_path = self.upload_dir / filename
        print(f"DEBUG: [FileProcessor] Saving file to {file_path}")
        with open(file_path, 'wb') as f:
            f.write(file_content)
        return str(file_path)
    
    def extract_content(self, file_path):
        file_path = Path(file_path)
        mime_type, _ = mimetypes.guess_type(str(file_path))
        print(f"DEBUG: [FileProcessor] Extracting content from {file_path} (Mime: {mime_type})")
        
        result = {'content': '', 'file_type': mime_type or 'unknown'}
        
        try:
            if file_path.suffix.lower() == '.pdf':
                result['content'] = self._extract_pdf(file_path)
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                result['content'] = self._extract_word(file_path)
            
            print(f"DEBUG: [FileProcessor] Extraction complete. Length: {len(result['content'])}")
        except Exception as e:
            print(f"ERROR: [FileProcessor] Extraction failed: {e}")
            result['content'] = f"Error: {e}"
        return result
    
    def _extract_pdf(self, file_path):
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                return '\n'.join([p.extract_text() for p in reader.pages])
        except: return "PDF extractor error"

    def _extract_word(self, file_path):
        try:
            import docx
            doc = docx.Document(file_path)
            return '\n'.join([p.text for p in doc.paragraphs])
        except: return "Word extractor error"
