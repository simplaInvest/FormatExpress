# Processador de Arquivos CSV

Este é um aplicativo web para processar e mesclar arquivos CSV.

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone este repositório ou baixe os arquivos

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Executando o Aplicativo

1. Certifique-se de que o ambiente virtual está ativado

2. Execute o servidor:
```bash
python app.py
```

3. Abra seu navegador e acesse:
```
http://127.0.0.1:5000
```

## Funcionalidades

- Upload de arquivos CSV
- Visualização de estatísticas das colunas
- Seleção de colunas específicas
- Mesclagem de múltiplos arquivos CSV
- Gerenciamento de presets de colunas
- Download de arquivos processados

## Limitações

- Tamanho máximo de arquivo: 100MB
- Apenas arquivos CSV são suportados 