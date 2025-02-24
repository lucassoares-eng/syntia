import os
import re
import json

# Caminho da pasta contendo os textos
TEXTS_DIR = "app/data/texts"

def clean_text(text):
    """Remove caracteres especiais e normaliza espaços"""
    text = re.sub(r"[“”‘’]", '"', text)  # Normaliza aspas
    text = re.sub(r"[^\w\s.,;:()º°/-§]", "", text)  # Remove caracteres especiais
    return text.strip()

def extract_articles(content):
    # Regex para capturar títulos dos artigos e anexos
    sections = re.split(r'(CAPÍTULO+[IVXLCDM]|CAPÍTULO\s+[IVXLCDM]+|Seção\s+[IVXLCDM]+|Art\.\s*\d{1,3}[º°]?|ANEXO\s+[IVXLCDM]+)', content)

    # Criando o dicionário estruturado
    articles_dict = {}

    # Processar o cabeçalho, excluindo tudo antes de "Dispõe sobre" ou "Assunto"
    header = sections[0].strip()
    match = re.search(r'(Dispõe sobre|Assunto)', header)
    if match:
        header = header[match.start():].strip().lstrip('.').lstrip()  # Mantém apenas o texto a partir da palavra-chave encontrada

    articles_dict["header"] = re.sub(r"\s+", " ", header)

    current_chapter = None
    current_section = None

    # Itera nos pares (Título, Texto)
    for i in range(1, len(sections) - 1, 2):
        title = sections[i].strip().replace(".", "").replace("º", "").replace("°", "")  # Remove pontuação desnecessária
        text = sections[i + 1].strip().lstrip('.').lstrip()  # Texto do artigo

        # Verifica se é um capítulo
        if title.startswith("CAPÍTULO"):
            current_chapter = title.replace("CAPÍTULO", "").strip()
            current_section = None
            continue

        # Verifica se é uma seção
        if title.startswith("Seção"):
            current_section = title.replace("Seção", "").strip()
            continue

        # Verifica se é artigo ou anexo
        if title.startswith("Art"):
            key = title.replace("Art", "art").replace(" ", "")  # Ex: "Art 1º" -> "art1"
            # Dividir o artigo pelos parágrafos (ex: "§ 1º", "§ 2º", "Parágrafo único")
            paragraphs = re.split(r'(§\s*\d{1,3}[º°]?|Parágrafo único)', text)

            # Estrutura do artigo
            section_dict = {"chapter": current_chapter, "section": current_section}
    
            # Se houver parágrafos, organizar a estrutura
            if len(paragraphs) > 1:
                section_dict["text"] = paragraphs[0].strip().lstrip('.').lstrip()  # Texto antes do primeiro parágrafo
                
                for j in range(1, len(paragraphs) - 1, 2):
                    para_key = paragraphs[j].strip().replace("§", "p").replace("º", "").replace("°", "").replace(" ", "")
                    # Ajuste para "Parágrafo único"
                    if "Parágrafo único" in paragraphs[j]:
                        para_key = "p"
                    # Limpa pontos e espaços extras no início do texto
                    clean_text = paragraphs[j + 1].strip().lstrip('.').lstrip()
    
                    # Dividir incisos dentro do parágrafo
                    incisos = re.split(r'(\n[IVX]{1,8}[.]?\s?)', clean_text)
                    inciso_dict = {}
    
                    if len(incisos) > 1:
                        section_dict[para_key] = {"text": incisos[0].strip()}  # Texto antes do primeiro inciso
    
                        for k in range(1, len(incisos) - 1, 2):
                            inciso_key = f"{incisos[k].strip().lstrip('.').lstrip().replace('.', '')}"
                            inciso_text = incisos[k + 1].strip().lstrip('.').lstrip()
                            inciso_dict[inciso_key] = re.sub(r"\s+", " ", inciso_text)
    
                        section_dict[para_key].update(inciso_dict)
                    else:
                        section_dict[para_key] = re.sub(r"\s+", " ", clean_text)
            else:
                # Se não houver parágrafos, dividir diretamente por incisos
                incisos = re.split(r'(\n[IVX]{1,8}[.]?\s?)', text)
                if len(incisos) > 1:
                    section_dict["text"] = re.sub(r"\s+", " ", incisos[0].strip())  # Texto antes do primeiro inciso
                    inciso_dict = {}
                    
                    for k in range(1, len(incisos) - 1, 2):
                        inciso_key = f"{incisos[k].strip().lstrip('.').lstrip().replace('.', '')}"
                        inciso_text = incisos[k + 1].strip().lstrip('.').lstrip()
                        inciso_dict[inciso_key] = re.sub(r"\s+", " ", inciso_text)
    
                    section_dict.update(inciso_dict)
                else:
                    section_dict["text"] = re.sub(r"\s+", " ", text)
    
            # Adiciona ao dicionário principal
            articles_dict[key] = section_dict
        else:
            key = title.replace("ANEXO", "anexo").replace(" ", "_").lower()  # Ex: "ANEXO I" -> "anexoI"
            articles_dict[key] = re.sub(r"\s+", " ", text)

    return articles_dict

def process_legislation(file_path):
    """Lê e estrutura o texto legal"""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    # Normaliza o texto
    content = clean_text(content)
    legislation = extract_articles(content)
    return legislation

# Processa todos os arquivos da pasta
structured_legislations = {}

for filename in os.listdir(TEXTS_DIR):
    if filename.endswith(".txt") and not ('perguntas_e_respostas' in filename):
        file_path = os.path.join(TEXTS_DIR, filename)
        structured_legislations[filename] = process_legislation(file_path)

# Salva os dados estruturados em JSON
output_path = "app/data/processed_legislation.json"
with open(output_path, "w", encoding="utf-8") as json_file:
    json.dump(structured_legislations, json_file, indent=4, ensure_ascii=False)

print(f"Processamento concluído! Dados salvos em {output_path}")