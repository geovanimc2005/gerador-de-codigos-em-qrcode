import os
import pandas as pd
import qrcode
from qrcode.image.pil import PilImage # <-- Importação CORRETA: PilImage
import uuid # Para IDs únicos para os QR Codes
import sqlite3 # Importar sqlite3 para o tipo de retorno do cursor (se necessário, mas já vem no flask)

class QRCodeManager:
    def __init__(self):
        self.qrcodes_folder = "qrcodes_generated"
        if not os.path.exists(self.qrcodes_folder):
            os.makedirs(self.qrcodes_folder)

    def get_excel_data_for_qrcode(self, excel_filepath):
        """
        Lê dados de um arquivo Excel e os formata em uma string para o QR Code.
        Você pode personalizar esta função para ler colunas ou abas específicas,
        ou formatar os dados de forma diferente (JSON, CSV, etc.).
        """
        try:
            df = pd.read_excel(excel_filepath)
            data_to_encode = df.to_csv(index=False, sep=';')

            if df.empty:
                print(f"Aviso: O arquivo Excel '{excel_filepath}' está vazio.")
                return None
            
            return data_to_encode
        except Exception as e:
            print(f"Erro ao ler arquivo Excel '{excel_filepath}': {e}")
            return None

    def generate_and_save_qrcode(self, data_to_encode, db_cursor):
        """
        Gera um QR Code com base nos dados fornecidos, salva a imagem
        e registra as informações no banco de dados.
        Retorna o ID único e o nome do arquivo do QR Code gerado.
        """
        if not data_to_encode:
            print("Erro: Nenhum dado fornecido para gerar o QR Code.")
            return None, None

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data_to_encode)
        qr.make(fit=True)

        # <-- Uso CORRETO: PilImage
        img = qr.make_image(fill_color="black", back_color="white", image_factory=PilImage)
        
        unique_id = str(uuid.uuid4())
        filename = f"qrcode_{unique_id}.png"
        
        filepath = os.path.join(self.qrcodes_folder, filename)
        img.save(filepath)

        db_cursor.execute(
            "INSERT INTO qrcodes (id, filename, data_encoded) VALUES (?, ?, ?)",
            (unique_id, filename, data_to_encode)
        )
        return unique_id, filename

    def get_all_qrcodes(self, db_cursor):
        """Retorna todas as informações dos QR Codes registrados no banco de dados."""
        db_cursor.execute("SELECT id, filename, data_encoded, created_at FROM qrcodes ORDER BY created_at DESC")
        return db_cursor.fetchall()

    def get_qrcode_by_id(self, qrcode_id, db_cursor):
        """
        Retorna as informações de um QR Code específico pelo ID,
        incluindo os dados codificados.
        """
        # <-- Adicionado 'data_encoded' na seleção
        db_cursor.execute("SELECT id, filename, data_encoded FROM qrcodes WHERE id = ?", (qrcode_id,))
        return db_cursor.fetchone()

    def delete_qrcode(self, qrcode_id, db_cursor):
        """
        Deleta um QR Code do banco de dados e seu arquivo de imagem associado.
        Retorna True em caso de sucesso, False caso contrário.
        """
        qrcode_info = self.get_qrcode_by_id(qrcode_id, db_cursor)
        if qrcode_info:
            filename = qrcode_info['filename']
            filepath = os.path.join(self.qrcodes_folder, filename)

            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError as e:
                    print(f"Erro ao remover arquivo {filepath}: {e}")
            
            db_cursor.execute("DELETE FROM qrcodes WHERE id = ?", (qrcode_id,))
            return True
        return False