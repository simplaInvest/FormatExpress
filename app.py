import os
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify, session, send_from_directory, send_file
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['PRESETS_FOLDER'] = 'presets'
app.secret_key = 'sua_chave_secreta_aqui'  # Necessário para session

# Criar pastas necessárias
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PRESETS_FOLDER'], exist_ok=True)

# Dicionário para armazenar os arquivos temporários
temp_files = {}

def get_preset_path(preset_name):
    return os.path.join(app.config['PRESETS_FOLDER'], f"{preset_name}.json")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Apenas arquivos CSV são permitidos'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Ler o arquivo CSV e obter as colunas
        df = pd.read_csv(filepath)
        columns = df.columns.tolist()
        total_rows = int(len(df))  # Converter para int padrão
        
        # Calcular estatísticas para cada coluna
        column_stats = {}
        for col in columns:
            non_null_count = int(df[col].count())  # Converter para int padrão
            column_stats[col] = {
                'total': non_null_count,
                'percentage': round((non_null_count / total_rows) * 100, 2)
            }
        
        # Salvar o caminho do arquivo na sessão
        session['current_file'] = filepath
        
        return jsonify({
            'message': 'Arquivo enviado com sucesso!',
            'filename': filename,
            'columns': columns,
            'column_stats': column_stats,
            'total_rows': total_rows
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao processar o arquivo: {str(e)}'}), 500

@app.route('/process', methods=['POST'])
def process_columns():
    try:
        data = request.get_json()
        columns_to_keep = data.get('columns', [])
        
        if not columns_to_keep:
            return jsonify({'error': 'Nenhuma coluna selecionada'}), 400
        
        filepath = session.get('current_file')
        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'Arquivo não encontrado'}), 404
        
        # Ler o arquivo CSV
        df = pd.read_csv(filepath)
        
        # Manter apenas as colunas selecionadas
        df = df[columns_to_keep]
        
        # Salvar o arquivo processado
        output_filename = f"processed_{os.path.basename(filepath)}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        df.to_csv(output_path, index=False)
        
        # Calcular estatísticas
        stats = {
            'num_colunas': int(len(df.columns)),
            'num_linhas': int(len(df)),
            'total_celulas': int(len(df.columns) * len(df)),
            'colunas': df.columns.tolist(),
            'output_filename': output_filename
        }
        
        # Salvar o caminho do arquivo processado na sessão
        session['processed_file'] = output_path
        
        return jsonify({
            'message': 'Arquivo processado com sucesso!',
            'filename': output_filename,
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao processar o arquivo: {str(e)}'}), 500

@app.route('/presets', methods=['GET'])
def get_presets():
    try:
        presets = []
        for filename in os.listdir(app.config['PRESETS_FOLDER']):
            if filename.endswith('.json'):
                preset_name = filename[:-5]  # Remove a extensão .json
                preset_path = os.path.join(app.config['PRESETS_FOLDER'], filename)
                with open(preset_path, 'r') as f:
                    preset_data = json.load(f)
                    presets.append({
                        'name': preset_name,
                        'columns': preset_data['columns'],
                        'use_index': preset_data.get('use_index', False)
                    })
        return jsonify({'presets': presets}), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao carregar presets: {str(e)}'}), 500

@app.route('/presets', methods=['POST'])
def save_preset():
    try:
        data = request.get_json()
        preset_name = data.get('name')
        columns = data.get('columns', [])
        use_index = data.get('use_index', False)
        
        if not preset_name or not columns:
            return jsonify({'error': 'Nome do preset e colunas são obrigatórios'}), 400
        
        # Filtrar valores None da lista de colunas
        columns = [col for col in columns if col is not None]
        
        preset_data = {
            'columns': columns,
            'use_index': use_index
        }
        
        preset_path = get_preset_path(preset_name)
        with open(preset_path, 'w') as f:
            json.dump(preset_data, f)
        
        return jsonify({'message': 'Preset salvo com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao salvar preset: {str(e)}'}), 500

@app.route('/presets/<preset_name>', methods=['DELETE'])
def delete_preset(preset_name):
    try:
        preset_path = get_preset_path(preset_name)
        if os.path.exists(preset_path):
            os.remove(preset_path)
            return jsonify({'message': 'Preset removido com sucesso!'}), 200
        return jsonify({'error': 'Preset não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': f'Erro ao remover preset: {str(e)}'}), 500

@app.route('/presets/<preset_name>', methods=['PUT'])
def update_preset(preset_name):
    try:
        data = request.get_json()
        columns = data.get('columns', [])
        use_index = data.get('use_index', False)
        
        if not columns:
            return jsonify({'error': 'É necessário selecionar pelo menos uma coluna'}), 400
        
        # Filtrar valores None da lista de colunas
        columns = [col for col in columns if col is not None]
        
        preset_path = get_preset_path(preset_name)
        if not os.path.exists(preset_path):
            return jsonify({'error': 'Preset não encontrado'}), 404
            
        preset_data = {
            'columns': columns,
            'use_index': use_index
        }
        
        with open(preset_path, 'w') as f:
            json.dump(preset_data, f)
        
        return jsonify({'message': 'Preset atualizado com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao atualizar preset: {str(e)}'}), 500

@app.route('/apply-preset', methods=['POST'])
def apply_preset():
    try:
        data = request.get_json()
        preset_name = data.get('preset_name')
        
        if not preset_name:
            return jsonify({'error': 'Nome do preset não fornecido'}), 400
            
        preset_path = os.path.join(app.config['PRESETS_FOLDER'], f'{preset_name}.json')
        
        if not os.path.exists(preset_path):
            return jsonify({'error': f'Preset {preset_name} não encontrado'}), 404
            
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
            
        if 'current_file' not in session:
            return jsonify({'error': 'Nenhum arquivo carregado'}), 400
            
        current_file = session['current_file']
        df = pd.read_csv(current_file)
        
        # Determinar se deve usar índices ou nomes de colunas
        use_index = preset_data.get('use_index', False)
        columns = preset_data.get('columns', [])
        
        if use_index:
            # Validar se todos os índices existem no arquivo
            if max(columns) >= len(df.columns):
                return jsonify({'error': 'Índices de colunas inválidos para o arquivo atual'}), 400
            selected_columns = [df.columns[i] for i in columns]
        else:
            # Validar se todas as colunas existem no arquivo
            missing_columns = [col for col in columns if col not in df.columns]
            if missing_columns:
                return jsonify({
                    'error': 'Algumas colunas do preset não existem no arquivo atual',
                    'missing_columns': missing_columns
                }), 400
            selected_columns = columns
            
        return jsonify({'columns': selected_columns})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'Erro ao baixar arquivo: {str(e)}'}), 500

@app.route('/stats', methods=['POST'])
def get_stats():
    try:
        if 'current_file' not in session:
            return jsonify({'error': 'Nenhum arquivo carregado'}), 400
            
        data = request.get_json()
        selected_columns = data.get('columns', [])
        
        if not selected_columns:
            return jsonify({'error': 'Nenhuma coluna selecionada'}), 400
            
        df = pd.read_csv(session['current_file'])
        
        # Validar se todas as colunas selecionadas existem no DataFrame
        invalid_columns = [col for col in selected_columns if col not in df.columns]
        if invalid_columns:
            return jsonify({
                'error': f'As seguintes colunas não existem no arquivo: {", ".join(invalid_columns)}'
            }), 400
            
        # Filtrar apenas as colunas selecionadas que existem no DataFrame
        valid_columns = [col for col in selected_columns if col in df.columns]
        df_selected = df[valid_columns]
        
        stats = {
            'num_colunas': len(valid_columns),
            'num_linhas': len(df_selected),
            'total_celulas': len(df_selected) * len(valid_columns),
            'colunas': valid_columns
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao calcular estatísticas: {str(e)}'}), 500

@app.route('/upload-multiple', methods=['POST'])
def upload_multiple():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        files = request.files.getlist('files')
        if len(files) < 2:
            return jsonify({'error': 'Selecione pelo menos 2 arquivos para mesclar'}), 400
        
        column_info = []
        temp_files.clear()  # Limpar arquivos temporários anteriores
        
        for i, file in enumerate(files):
            if file.filename == '':
                continue
                
            if not file.filename.endswith('.csv'):
                return jsonify({'error': f'O arquivo {file.filename} não é um CSV válido'}), 400
                
            try:
                # Ler o arquivo CSV
                df = pd.read_csv(file)
                
                # Calcular estatísticas das colunas
                column_stats = {}
                for column in df.columns:
                    non_null_count = int(df[column].count())  # Converter para int nativo
                    total_count = int(len(df))  # Converter para int nativo
                    percentage = round((non_null_count / total_count) * 100, 2)
                    column_stats[column] = {
                        'total': non_null_count,
                        'percentage': percentage
                    }
                
                # Salvar o arquivo temporariamente
                temp_filename = secure_filename(f'temp_{i}_{file.filename}')
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
                df.to_csv(temp_path, index=False)
                temp_files[temp_filename] = temp_path
                
                column_info.append({
                    'filename': file.filename,
                    'columns': list(df.columns),
                    'column_stats': column_stats,
                    'num_rows': int(len(df))  # Converter para int nativo
                })
                
            except pd.errors.EmptyDataError:
                return jsonify({'error': f'O arquivo {file.filename} está vazio'}), 400
            except pd.errors.ParserError:
                return jsonify({'error': f'O arquivo {file.filename} não está em formato CSV válido'}), 400
            except Exception as e:
                return jsonify({'error': f'Erro ao processar o arquivo {file.filename}: {str(e)}'}), 400
        
        return jsonify({
            'message': 'Arquivos processados com sucesso',
            'column_info': column_info
        })
        
    except Exception as e:
        app.logger.error(f'Erro no upload múltiplo: {str(e)}')
        return jsonify({'error': f'Erro ao processar os arquivos: {str(e)}'}), 500

@app.route('/merge-files', methods=['POST'])
def merge_files():
    if not temp_files:
        return jsonify({'error': 'Nenhum arquivo para mesclar'}), 400
    
    try:
        # Ler todos os DataFrames
        dfs = []
        for filename, path in temp_files.items():
            df = pd.read_csv(path)
            dfs.append(df)
        
        # Mesclar os DataFrames
        merged_df = pd.concat(dfs, ignore_index=True)
        
        # Salvar o arquivo mesclado
        output_filename = 'merged_output.csv'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        merged_df.to_csv(output_path, index=False)
        
        # Calcular estatísticas do arquivo mesclado
        stats = {
            'num_colunas': int(len(merged_df.columns)),  # Converter para int nativo
            'num_linhas': int(len(merged_df)),  # Converter para int nativo
            'total_celulas': int(len(merged_df) * len(merged_df.columns)),  # Converter para int nativo
            'colunas': list(merged_df.columns)
        }
        
        # Limpar arquivos temporários
        for path in temp_files.values():
            try:
                os.remove(path)
            except:
                pass
        temp_files.clear()
        
        return jsonify({
            'message': 'Arquivos mesclados com sucesso',
            'filename': output_filename,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao mesclar os arquivos: {str(e)}'}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'error': 'O arquivo é muito grande. O tamanho máximo permitido é 100MB. Por favor, divida seus arquivos em partes menores.'
    }), 413

if __name__ == '__main__':
    app.run(debug=True) 