import os
from flask import Flask, request, send_file, jsonify, g, render_template
import sqlite3
from manage import QRCodeManager 

# Importe a extensão CORS
from flask_cors import CORS 

app = Flask(__name__, static_folder='.', static_url_path='') 

# --- CONFIGURAÇÃO DE CORS ALTAMENTE PERMISSIVA PARA DESENVOLVIMENTO ---

# NÃO USE ESTA CONFIGURAÇÃO EM AMBIENTE DE PRODUÇÃO POR RAZÕES DE SEGURANÇA.
CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "expose_headers": "*"}})


# Configurações de pastas e banco de dados
DATABASE = 'dados.db'
QRCODES_FOLDER = 'qrcodes_generated'
TEMP_FOLDER = 'temp'

# Inicializa o gerenciador de QR Codes
manager = QRCodeManager() 

if not os.path.exists(QRCODES_FOLDER):
    os.makedirs(QRCODES_FOLDER)
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

# --- Gerenciamento da Conexão com o Banco de Dados ---
def get_db():
  
    db = getattr(g, '_database', None) 
    if db is None:
        db = g._database = sqlite3.connect(DATABASE) 
        db.row_factory = sqlite3.Row # Para acessar colunas por nome
        
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qrcodes (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                data_encoded TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit() 
    return db

@app.teardown_appcontext
def close_connection(exception):
  
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Rota para servir o index.html ---
# Esta rota permite que você acesse sua aplicação pela URL do servidor (ex: http://localhost:5000/)
@app.route('/')
def index():
    return send_file('index.html') 

# --- Rotas da API ---

@app.route('/upload_and_generate_qr', methods=['POST'])
def upload_and_generate_qr():
    """
    Recebe um arquivo Excel, extrai os dados, gera um QR Code,
    salva-o e registra suas informações no banco de dados.
    """
    if 'excel_file' not in request.files:
        return jsonify({"error": "Nenhum arquivo Excel enviado."}), 400
    
    excel_file = request.files['excel_file']
    if excel_file.filename == '':
        return jsonify({"error": "Nome do arquivo inválido."}), 400

    if excel_file:
        temp_filepath = os.path.join(TEMP_FOLDER, excel_file.filename)
        excel_file.save(temp_filepath)

        data_to_encode = manager.get_excel_data_for_qrcode(temp_filepath)
        
        os.remove(temp_filepath) # Limpa o arquivo temporário

        if data_to_encode:
            db_conn = get_db() 
            cursor = db_conn.cursor()
            
            qrcode_id, filename = manager.generate_and_save_qrcode(data_to_encode, cursor)
            db_conn.commit() 

            if qrcode_id:
                return jsonify({
                    "message": "QR Code gerado com sucesso!",
                    "id": qrcode_id,
                    "filename": filename,
                    "qrcode_url": f"/qrcode_image/{qrcode_id}"
                }), 200
            else:
                return jsonify({"error": "Falha interna ao gerar QR Code."}), 500
        else:
            return jsonify({"error": "Não foi possível extrair dados válidos do arquivo Excel."}), 400

@app.route('/list_qrcodes', methods=['GET'])
def list_qrcodes():
    """
    Lista todos os QR Codes gerados e registrados no banco de dados.
    """
    db_conn = get_db() 
    cursor = db_conn.cursor()
    qrcodes = manager.get_all_qrcodes(cursor) 

    qrcodes_list = []
    for qr in qrcodes: 
        qrcodes_list.append({
            "id": qr['id'],
            "filename": qr['filename'],
            "data_encoded": qr['data_encoded'],
            "created_at": qr['created_at'],
            "qrcode_url": f"/qrcode_image/{qr['id']}" 
        })
    return jsonify(qrcodes_list), 200

@app.route('/qrcode_image/<qrcode_id>', methods=['GET'])
def get_qrcode_image(qrcode_id):
    """
    Serve a imagem de um QR Code específico com base no seu ID.
    """
    db_conn = get_db() 
    cursor = db_conn.cursor()
    qrcode_info = manager.get_qrcode_by_id(qrcode_id, cursor) 

    if qrcode_info:
        filepath = os.path.join(QRCODES_FOLDER, qrcode_info['filename'])
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/png')
        else:
            return "Arquivo QR Code não encontrado no sistema de arquivos.", 404
    return "QR Code não encontrado no banco de dados.", 404

@app.route('/delete_qrcode/<qrcode_id>', methods=['DELETE'])
def delete_qrcode_route(qrcode_id):
    """
    Deleta um QR Code do banco de dados e seu arquivo de imagem associado.
    """
    db_conn = get_db() 
    cursor = db_conn.cursor()
    
    if manager.delete_qrcode(qrcode_id, cursor): 
        db_conn.commit() 
        return jsonify({"message": f"QR Code {qrcode_id} deletado com sucesso."}), 200
    return jsonify({"error": f"QR Code {qrcode_id} não encontrado ou erro ao deletar."}), 404


@app.route('/get_qrcode_data/<qrcode_id>', methods=['GET'])
def get_qrcode_data(qrcode_id):
    """
    Retorna os dados brutos codificados em um QR Code específico para pré-preencher um formulário de edição.
    """
    db_conn = get_db()
    cursor = db_conn.cursor()
    qrcode_info = manager.get_qrcode_by_id(qrcode_id, cursor) 

    if qrcode_info:
        # qrcode_info agora contém 'data_encoded' devido à mudança em manage.py
        return jsonify({"id": qrcode_info['id'], "data_encoded": qrcode_info['data_encoded']}), 200
    return jsonify({"error": "QR Code não encontrado."}), 404

# --- NOVA ROTA: Atualizar um QR Code (deleta o antigo e cria um novo) ---
@app.route('/update_qrcode/<qrcode_id>', methods=['POST'])
def update_qrcode(qrcode_id):
   
    new_data = request.json.get('new_data_encoded')
    if not new_data:
        return jsonify({"error": "Novos dados para o QR Code não fornecidos."}), 400

    db_conn = get_db()
    cursor = db_conn.cursor()

    if not manager.delete_qrcode(qrcode_id, cursor):
        return jsonify({"error": "QR Code original não encontrado para atualização."}), 404
    
 
    new_qrcode_id, new_filename = manager.generate_and_save_qrcode(new_data, cursor)
    db_conn.commit() # Confirma as alterações no banco de dados

    if new_qrcode_id:
        return jsonify({
            "message": "QR Code atualizado com sucesso!",
            "old_id": qrcode_id, # Para referência, se necessário
            "new_id": new_qrcode_id,
            "new_filename": new_filename,
            "qrcode_url": f"/qrcode_image/{new_qrcode_id}"
        }), 200
    else:
        return jsonify({"error": "Falha interna ao gerar o novo QR Code."}), 500


@app.route("/dados", methods=['GET'])
def get_example_data():
    """
    Rota de exemplo para demonstrar a busca de dados simples do servidor.
    """
    dados = { 
        "mensagem": "Este é um dado de exemplo do servidor Flask. ele armazena as suas informações em um servidor local, no seu computador, ou seja usando o programa você sabe com o que está lidando",
        "versao_api": "1.0",
        "data_atual": "2025-06-19" 
    }
    return jsonify(dados)

if __name__ == "__main__":

    app.run(debug=True)
