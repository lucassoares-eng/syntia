import os
import json
import re

TEXT_DIR = "app/data/texts"
LEGISLATION_MAP_PATH = "app/data/legislation_map.json"

# Padrões para identificar citações de legislações
PATTERNS = [
    r'RDC\s*n[ºo]?\s*\d{1,4}/\d{4}',  # Exemplo: RDC nº 250/2005
    r'RDC\s*n[ºo]?\s*\d{1,4},\s*de\s*\d{1,2}\s*de\s*\w+\s*de\s*\d{4}',  # RDC nº 315, de 26 de outubro de 2005
    r'Lei\s*n[ºo]?\s*\d{1,4},\s*de\s*\d{1,2}\s*de\s*\w+\s*de\s*\d{4}',  # Lei nº 6.437, de 20 de agosto de 1977
    r'Lei\s*n[ºo.]?\s*\d{1,4}/\d{4}',  # Lei nº 12.345/2010
    r'IN\s*n[ºo.]?\s*\d{1,4}/\d{4}',  # IN nº 3/2013
    r'Instrução\s*Normativa\s*n[ºo.]?\s*\d{1,4},\s*de\s*\d{1,2}\s*de\s*\w+\s*de\s*\d{4}',  # Instrução Normativa nº. 11, de 06 de outubro de 2009
    r'Instrução\s*Normativa\s*n[ºo.]?\s*\d{1,4}/\d{4}',  # Instrução Normativa nº 3/2013
    r'Portaria\s*n[ºo.]?\s*\d{1,4}/\d{4}',  # Portaria nº 100/2018
    r'Portaria\s*n[ºo.]?\s*\d{1,4}/MS',  # Portaria nº 696/MS
    r'Nota\s*Técnica\s*(Conjunta\s*)?\d{1,4}/\d{4}.*?,\s*de\s*\d{1,2}\s*de\s*\w+\s*de\s*\d{4}',  # Nota Técnica Conjunta 01/2016, de 22 de abril de 2016
    r'Nota\s*Técnica\s*n[ºo.]?\s*\d{1,4}-\d{1,4}/\d{4}',  # Nota Técnica nº 06-001/2015
    r'RDC\s*n[°]?\s*\d{1,4}/\d{4}'  # Exemplo: RDC n° 55/2005
]

REVOKE_TERMS = ["revoga", "revogado", "revogada", "revogação", "fica sem efeito", "passa a vigorar", "substitui", "revogam-se"]
COMPLEMENT_TERMS = ["complementa", "alterada por", "modifica", "acrescido", "acrescenta", "fica incluído", "ficam incluídos"]
CITES_TERMS = ["conforme", "de acordo com", "nos termos", "descrita nas seções", "considerando", "não substitui"]

def extract_legislation_references(text):
    """Extrai citações de outras legislações do texto."""
    for pattern in PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0]

def check_relation(text, terms):
    """Verifica se há menção a termos de revogação ou complementação."""
    return any(term in text.lower() for term in terms)

def analyze_legislation_references():
    legislation_map = {}

    for filename in os.listdir(TEXT_DIR):
        if filename.endswith(".txt") and ('perguntas_e_respostas' not in filename):
            file_path = os.path.join(TEXT_DIR, filename)
            legislation_name = os.path.splitext(filename)[0]
            references = []
            
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            """
            # Procurar o índice do primeiro "Art. 1" e cortar o texto antes disso
            start_index = content.find("Art. 1")
            if start_index != -1:
                content = content[start_index:]  # Mantém apenas o trecho a partir de "Art. 1º"
            """
            
            lines = re.split(r'\.\n|;\n|; e\n|:\n', content)
            current_article = None
            article_category = None
                
            for line in lines:
                line = line.replace("\n", " ")
                
                # Identifica título do artigo
                article_match = re.findall(r'^Art\.\s*\d{1,4}[º°]?', line, re.IGNORECASE)
                if article_match:
                    current_article = article_match[0]
                    article_category = None
                    if check_relation(line, REVOKE_TERMS):
                        article_category = "revokes"
                    if check_relation(line, COMPLEMENT_TERMS):
                        article_category = "complements"
                    if check_relation(line, CITES_TERMS):
                        article_category = "cites"
        
                reference = extract_legislation_references(line)

                legislation_parts = legislation_name.split('_') 
                # Verificar se todas as partes de legislation_name estão dentro de reference
                if reference and all(part in reference for part in legislation_parts):
                    reference = None

                if reference:
                    category = article_category
                    if check_relation(line, REVOKE_TERMS):
                        category = "revokes"
                    if check_relation(line, COMPLEMENT_TERMS):
                        category = "complements"
                    if check_relation(line, CITES_TERMS):
                        category = "cites"
                    references.append([reference, current_article, category, line])
            
            if references:
                legislation_map[legislation_name] = {"references": references}
    
    with open(LEGISLATION_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(legislation_map, f, indent=4, ensure_ascii=False)
    
    print("[✔] Mapeamento de legislações concluído e salvo.")

analyze_legislation_references()