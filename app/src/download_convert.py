import os
import json
import requests
import pdfplumber
from bs4 import BeautifulSoup
import urllib3

# Desativar aviso de requisições HTTPS não verificadas
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Diretórios
DATA_DIR = "app/data"
PDF_DIR = os.path.join(DATA_DIR, "pdfs")
TEXT_DIR = os.path.join(DATA_DIR, "texts")

# Criar diretórios se não existirem
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(TEXT_DIR, exist_ok=True)

def download_file(name, url):
    """Faz o download de um arquivo (PDF ou HTML) e processa conforme o tipo de conteúdo."""
    response = requests.get(url, stream=True, verify=False, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        print(f"[✘] Erro ao baixar {name}: {response.status_code}")
        return None

    content_type = response.headers.get("Content-Type", "")
    
    if "application/pdf" in content_type:
        return save_pdf(name, response)
    elif "text/html" in content_type:
        return save_html_as_text(name, response.text)
    else:
        print(f"[✘] Tipo de arquivo não suportado para {name}: {content_type}")
        return None

def save_pdf(name, response):
    """Salva um PDF no diretório e retorna o caminho do arquivo."""
    pdf_path = os.path.join(PDF_DIR, f"{name}.pdf")
    
    with open(pdf_path, "wb") as f:
        f.write(response.content)

    convert_pdf_to_text(pdf_path, name)
    return pdf_path

def save_html_as_text(name, html_content):
    """Extrai texto de uma página HTML e salva como arquivo .txt."""
    text_path = os.path.join(TEXT_DIR, f"{name}.txt")
    
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator="\n", strip=True)  # Extrai e limpa o texto
    
    text_path = os.path.join(TEXT_DIR, f"{name}.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"[✔] HTML convertido para texto: {text_path}")
    return text_path

def convert_pdf_to_text(pdf_path, name):
    """Converte um PDF para texto e salva em um arquivo .txt."""
    text_path = os.path.join(TEXT_DIR, f"{name}.txt")

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])

    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"[✔] PDF convertido para texto: {text_path}")

# Carregar a lista de documentos
with open("documents.json", "r", encoding="utf-8") as file:
    documents = json.load(file)["documents"]

# Executar download e conversão somente se o texto ainda não existir
for doc in documents:
    text_path = os.path.join(TEXT_DIR, f"{doc['name']}.txt")
    
    if not os.path.exists(text_path):
        download_file(doc["name"], doc["link"])
    else:
        print(f"[✔] Arquivo já existe, pulando: {doc['name']}")