import pandas as pd

def filter_tags(tags_str, excluded_tags):
    """Filtra tags excluídas de uma string de tags"""
    if not isinstance(tags_str, str) or not tags_str.strip():
        return tags_str
    
    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
    filtered_tags = [tag for tag in tags if tag not in excluded_tags]
    result = ', '.join(filtered_tags) if filtered_tags else ''
    
    return result

# Simular o arquivo de teste
data = {
    'Nome': ['João', 'Maria', 'Pedro', 'Ana', 'Carlos'],
    'Email': ['joao@email.com', 'maria@email.com', 'pedro@email.com', 'ana@email.com', 'carlos@email.com'],
    'Tags': [
        'aluno-SC12, presente-01, captacao-EI12',
        'aluno-SC12, presente-01, inactive',
        'aluno-SC13, presente-01, captacao-EI12, premium',
        'aluno-SC12, presente-01, trial',
        'aluno-SC14, presente-01, inactive'
    ]
}

df = pd.DataFrame(data)
print("=== ARQUIVO ORIGINAL ===")
print(df)
print()

# Simular exclusão das tags "inactive" e "trial"
excluded_tags = ["inactive", "trial"]
print(f"Tags a serem excluídas: {excluded_tags}")
print()

# Aplicar filtro
if 'Tags' in df.columns and excluded_tags:
    print("Aplicando filtro de tags...")
    df['Tags'] = df['Tags'].apply(lambda x: filter_tags(x, excluded_tags))
    print("Filtro aplicado!")
else:
    print("Nenhum filtro aplicado")

print()
print("=== ARQUIVO APÓS FILTRO ===")
print(df) 