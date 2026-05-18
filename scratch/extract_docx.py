import zipfile
import xml.etree.ElementTree as ET
import os

def extract_text_from_docx(docx_path):
    try:
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            # Word document text is in word/document.xml
            xml_content = zip_ref.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            # Namespace for Word processingML
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            texts = []
            for paragraph in tree.findall('.//w:p', ns):
                paragraph_text = ""
                for run in paragraph.findall('.//w:r', ns):
                    for text in run.findall('.//w:t', ns):
                        paragraph_text += text.text
                if paragraph_text:
                    texts.append(paragraph_text)
            
            return "\n".join(texts)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    path = "Project Goal(Procurement).txt"
    if os.path.exists(path):
        content = extract_text_from_docx(path)
        with open("Project_Goal_Extracted.txt", "w", encoding="utf-8") as f:
            f.write(content)
        print("Success: Extracted to Project_Goal_Extracted.txt")
    else:
        print("File not found.")
