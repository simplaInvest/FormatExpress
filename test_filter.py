def filter_tags(tags_str, excluded_tags):
    """Filtra tags excluídas de uma string de tags"""
    if not isinstance(tags_str, str) or not tags_str.strip():
        return tags_str
    
    print(f"DEBUG - Original: '{tags_str}'")
    print(f"DEBUG - Excluded tags: {excluded_tags}")
    
    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
    print(f"DEBUG - Parsed tags: {tags}")
    
    filtered_tags = [tag for tag in tags if tag not in excluded_tags]
    print(f"DEBUG - Filtered tags: {filtered_tags}")
    
    result = ', '.join(filtered_tags) if filtered_tags else ''
    print(f"DEBUG - Final result: '{result}'")
    
    return result

# Teste
test_data = "aluno-SC12, presente-01, captacao-EI12, inactive"
excluded = ["inactive", "trial"]

print("=== TESTE DA FUNÇÃO FILTER_TAGS ===")
result = filter_tags(test_data, excluded)
print(f"Resultado final: '{result}'") 