import os
import re
import sys

def clean_ocr(directory_path):
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt") or filename.endswith(".md"):
            print(filename)
            file_path = os.path.join(directory_path, filename)

            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Remove HTML tags and extract text content
                text = re.sub(r'<[^>]+>', '', content)
                # Remove LaTeX text markup and extract content
                text = re.sub(r'\$\\[a-z]+\{(.*?)\}', r'\1', text)
                #text = re.sub(r'\$\\mathcal\{(.*?)\}\$', r'\1', text)
                text = re.sub(r'\\[a-zA-Z]+', '', text)
                text = text.replace('\\circ', '°')
                text = text.replace('\\quad', ' ')
                text = text.replace('array', ' ')
                lines = text.splitlines(keepends=True)

            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(line for line in lines if '![' not in line and '[blank' not in line.lower() and 'is blank' not in line.lower() and 'no visible' not in line.lower() and 'no text' not in line.lower() and line.strip() and not line.lower().startswith('note:') and not line.lower().startswith('*note:') and not line.startswith('<div '))

if len(sys.argv) != 2:
    print("\nUsage: python clean_text.py <folder>")
else:
    clean_ocr(sys.argv[1])
