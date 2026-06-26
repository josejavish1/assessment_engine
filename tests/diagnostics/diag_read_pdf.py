import pypdf
import sys

def read_pdf(file_path):
    try:
        reader = pypdf.PdfReader(file_path)
        text = ""
        for i, page in enumerate(reader.pages[:8]):
            text += page.extract_text() + "\n"
        print(text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    read_pdf(sys.argv[1])
