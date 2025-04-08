import re
import json
import os
from typing import Any, Dict, Union, List, Pattern

# Termos de filtro expandidos
FILTER_TERMS = [
    "RE nº", "RDC nº", "Portaria n°", "Resolução RE", "Resolução RDC", 
    "Resolução da Diretoria Colegiada", "Lei nº", "Instrução Normativa",
    "Nota Técnica", "Decreto nº", "Constituição", "Resolução ANVISA/DC"
]

# Padrões de referência atualizados e corrigidos
REFERENCE_PATTERNS = [
    # Padrão específico para a Constituição (mover para primeiro lugar)
    re.compile(
        r'Constitui[cç][aã]o\s+da\s+Rep[uú]blica\s+Federativa\s+do\s+Brasil(?:,\s*de\s*(?P<day>\d{1,2}\s*de\s*\w+\s*de\s*(?P<year>\d{4})))?',
        re.IGNORECASE
    ),
    # Padrão específico para Portarias
    re.compile(
        r'Portaria\s*n[º°]?\s*(?P<number>[\d\.]+)(?:\s+da\s+ANVISA)?(?:\s*,\s*de\s*\d{1,2}\s*de\s*\w+\s*de\s*(?P<year>\d{4}))?',
        re.IGNORECASE
    ),
    # Padrão principal revisado e corrigido (excluindo Constituição e Portaria)
    re.compile(
        r"(?P<full_match>"
        r"(?P<prefix>Resolu[cç][aã]o\s+(?:da\s+)?(?:Diretoria\s+Colegiada(?:\s+da\s+Anvisa)?|RDC|RE|ANVISA/DC)|"
        r"RDC|RE|Lei|Instru[cç][aã]o\s+Normativa|Nota\s+T[cé]cnica(?:\s+Conjunta)?|"
        r"Decreto)\s*"
        r"N?[º°]?\s*(?P<number>[\d\-\./]+)"
        r"(?:\s*,\s*de\s*\d{1,2}\s*de\s*\w+\s*de\s*(?P<year>\d{4})|"
        r"\s+de\s+\d{1,2}\s+de\s+\w+\s+de\s+(?P<year2>\d{4})|"
        r"\s*DE\s*\d{1,2}\s*[/\\]\s*\d{1,2}\s*[/\\]\s*(?P<year3>\d{4})|"
        r"\s*/\s*(?P<year4>\d{4}))?"
        r")",
        re.IGNORECASE
    ),
    # Padrões específicos para formatos variados
    re.compile(
        r'(?:Resolução\s+)?ANVISA/DC\s*N[º°]?\s*(?P<number>\d+)\s+DE\s+(?P<day>\d{1,2})[/\\](?P<month>\d{1,2})[/\\](?P<year>\d{4})',
        re.IGNORECASE
    ),
    re.compile(
        r'Decreto\s*n[º°]?\s*(?P<number>[\d\.]+)(?:\s*,\s*de\s*\d{1,2}\s*de\s*\w+\s*de\s*(?P<year>\d{4}))?',
        re.IGNORECASE
    ),
]

def format_reference(match: re.Match, pattern_index: int = 0) -> str:
    """Formata a referência no padrão {TYPE_NUMBER_YEAR}"""
    try:
        groups = match.groupdict()
        prefix = groups.get('prefix', '')
        number = groups.get('number', '')
        year = (groups.get('year', '') or groups.get('year2', '') or 
                groups.get('year3', '') or groups.get('year4', ''))
        full_text = match.group(0)
        
        # Determina o tipo do documento de forma mais precisa
        if pattern_index == 0:  # Constituição
            doc_type = 'ConstituicaoFederal'
            number = '196'  # Número do artigo da Constituição
        elif 'PORTARIA' in prefix.upper() or 'PORTARIA' in full_text.upper():
            doc_type = 'Portaria'
        elif 'DECRETO' in prefix.upper() or 'DECRETO' in full_text.upper():
            doc_type = 'Decreto'
        elif 'RE' in prefix.upper() or 'RE' in full_text.upper():
            doc_type = 'RE'
        elif 'RDC' in prefix.upper() or 'RDC' in full_text.upper():
            doc_type = 'RDC'
        elif 'LEI' in prefix.upper():
            doc_type = 'Lei'
        else:
            doc_type = prefix.replace(' ', '_') if prefix else 'UNKNOWN'
        
        # Limpa e formata o número
        number = re.sub(r'[^\d]', '', number)
        
        # Formata o ano para os padrões específicos
        if year:
            formatted_ref = f"{doc_type}_{number}_{year}"
        else:
            formatted_ref = f"{doc_type}_{number}"
        
        return formatted_ref
    
    except Exception as e:
        print(f"Erro ao formatar referência '{match.group(0)}': {e}")
        return ''

def contains_filter_terms(text: str) -> bool:
    """Verifica se o texto contém termos de filtro"""
    text_lower = text.lower()
    return any(term.lower() in text_lower for term in FILTER_TERMS)

def process_text(text: str) -> str:
    """Processa texto mantendo o original e acrescentando {REF}"""
    if not isinstance(text, str) or not contains_filter_terms(text):
        return text
    
    # Set para rastrear referências já processadas no texto
    processed_refs = set()
    
    def apply_patterns(text: str) -> str:
        """Aplica todos os padrões de referência ao texto"""
        # Primeiro, processa apenas o padrão específico da Constituição
        def constituicao_replacer(match):
            original_text = match.group(0)
            ref = format_reference(match, 0)  # Usa o primeiro padrão (Constituição)
            
            if not ref or '_' not in ref:
                return original_text
            
            # Verifica se a referência já foi processada neste texto
            if ref in processed_refs:
                return original_text
            
            # Adiciona a referência ao conjunto de processadas
            processed_refs.add(ref)
            return f"{original_text} {{{ref}}}"
        
        # Aplica o padrão da Constituição primeiro
        text = REFERENCE_PATTERNS[0].sub(constituicao_replacer, text)
        
        # Depois, processa os demais padrões
        for i, pattern in enumerate(REFERENCE_PATTERNS[1:], 1):
            def replacer(match):
                original_text = match.group(0)
                ref = format_reference(match, i)
                
                if not ref or '_' not in ref:
                    return original_text
                
                # Verifica se a referência já foi processada neste texto
                if ref in processed_refs:
                    return original_text
                
                # Adiciona a referência ao conjunto de processadas
                processed_refs.add(ref)
                return f"{original_text} {{{ref}}}"
            
            text = pattern.sub(replacer, text)
        
        return text
    
    # Aplica os padrões uma única vez
    return apply_patterns(text)

def process_content(content: Any) -> Any:
    """Processa conteúdo recursivamente (string, dict ou list)"""
    try:
        if isinstance(content, str):
            return process_text(content)
        elif isinstance(content, dict):
            return {k: process_content(v) for k, v in content.items()}
        elif isinstance(content, list):
            return [process_content(item) for item in content]
        return content
    except Exception as e:
        print(f"Erro ao processar conteúdo: {e}")
        return content

def preprocess_references():
    """Função principal para carregar, processar e salvar os dados"""
    try:
        input_dir = "app/data/preprocess"
        output_dir = "app/data/preprocess_references"
        os.makedirs(output_dir, exist_ok=True)  # Cria a pasta de saída se não existir

        for filename in os.listdir(input_dir):
            if filename.endswith(".json"):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename)

                # Carrega o arquivo JSON individual
                with open(input_path, "r", encoding="utf-8") as file:
                    legislation_data = json.load(file)

                # Processa o conteúdo do arquivo
                processed_data = process_content(legislation_data)

                # Salva o resultado processado
                with open(output_path, "w", encoding="utf-8") as file:
                    json.dump(processed_data, file, ensure_ascii=False, indent=4)

        print(f"Processamento concluído! Arquivos salvos em {output_dir}")
    
    except Exception as e:
        print(f"Erro durante o processamento: {e}")

if __name__ == "__main__":
    preprocess_references()