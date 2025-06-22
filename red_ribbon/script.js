// Constante para a URL base do seu servidor Flask
const API_BASE_URL = 'http://localhost:5000';

// --- Funções de Gerenciamento de Abas ---
function openTab(evt, tabName) {
    let i, tabContent, tabButtons;

    // Esconde todo o conteúdo das abas
    tabContent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabContent.length; i++) {
        tabContent[i].style.display = "none";
    }

    // Remove a classe "active" de todos os botões de aba
    tabButtons = document.getElementsByClassName("tab-button");
    for (i = 0; i < tabButtons.length; i++) {
        tabButtons[i].className = tabButtons[i].className.replace(" active", "");
    }

    // Mostra o conteúdo da aba atual e adiciona a classe "active" ao botão clicado
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";

    // Lógica para carregar dados ou listas quando a aba específica é aberta
    if (tabName === 'list_tab') {
        listQrCodes(); // Chama a função para listar QR Codes
    } else if (tabName === 'data_tab') {
        fetchServerData(); // Chama a função para buscar dados de exemplo
    }
}

// --- Lógica de Upload de Excel e Geração de QR Code ---
document.getElementById('excelUploadForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // Evita o envio padrão do formulário (que recarregaria a página)

    const uploadMessage = document.getElementById('uploadMessage');
    const generatedQrCodeDetails = document.getElementById('generatedQrCodeDetails');
    const generatedQrId = document.getElementById('generatedQrId');
    const generatedQrFilename = document.getElementById('generatedQrFilename');
    const generatedQrImage = document.getElementById('generatedQrImage');
    const excelFile = document.getElementById('excelFile').files[0]; // Pega o primeiro arquivo selecionado

    // Validação básica do arquivo
    if (!excelFile) {
        uploadMessage.textContent = "Por favor, selecione um arquivo Excel para fazer o upload.";
        uploadMessage.className = "message error"; // Adiciona classe para estilo de erro
        generatedQrCodeDetails.style.display = 'none';
        return;
    }

    uploadMessage.textContent = "Enviando arquivo e gerando QR Code... Por favor, aguarde.";
    uploadMessage.className = "message info"; // Adiciona classe para estilo de informação
    generatedQrCodeDetails.style.display = 'none'; // Esconde detalhes de QR Code gerados anteriormente

    const formData = new FormData(); // Cria um objeto FormData para enviar o arquivo
    formData.append('excel_file', excelFile); // Adiciona o arquivo Excel ao FormData

    try {
        const response = await fetch(`${API_BASE_URL}/upload_and_generate_qr`, {
            method: 'POST',
            body: formData // Envia o FormData como corpo da requisição POST
        });

        const result = await response.json(); // Converte a resposta para JSON

        if (response.ok) { // Verifica se a requisição foi bem-sucedida (status 2xx)
            uploadMessage.textContent = result.message;
            uploadMessage.className = "message success"; // Estilo de sucesso

            // Exibe os detalhes do QR Code gerado na aba "Gerar QR Code"
            generatedQrId.textContent = result.id;
            generatedQrFilename.textContent = result.filename;
            generatedQrImage.src = `${API_BASE_URL}${result.qrcode_url}`; // Define a URL da imagem
            generatedQrImage.alt = `QR Code para ${result.filename}`;
            generatedQrCodeDetails.style.display = 'block';

            // Limpa o input do arquivo após o upload bem-sucedido
            document.getElementById('excelFile').value = '';

        } else {
            // Lida com erros da API
            uploadMessage.textContent = `Erro ao gerar QR Code: ${result.error || 'Erro desconhecido'}`;
            uploadMessage.className = "message error"; // Estilo de erro
        }
    } catch (error) {
        // Lida com erros de rede ou outros erros inesperados
        uploadMessage.textContent = `Erro de conexão com o servidor: ${error.message}`;
        uploadMessage.className = "message error"; // Estilo de erro
        console.error("Erro ao fazer upload do arquivo Excel:", error);
    }
});

// --- Lógica de Listagem de QR Codes ---
async function listQrCodes() {
    const qrCodeListDiv = document.getElementById('qrCodeList');
    qrCodeListDiv.innerHTML = '<p class="message info">Carregando seus QR Codes...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/list_qrcodes`);
        if (!response.ok) {
            throw new Error(`Erro HTTP! Status: ${response.status}`);
        }
        const qrcodes = await response.json();

        qrCodeListDiv.innerHTML = ''; // Limpa a mensagem de carregamento

        if (qrcodes.length === 0) {
            qrCodeListDiv.innerHTML = '<p class="message info">Nenhum QR Code gerado ainda. Use a aba "Gerar QR Code" para começar!</p>';
            return;
        }

        // Cria e adiciona um elemento HTML para cada QR Code na lista
        qrcodes.forEach(qr => {
            const qrItem = document.createElement('div');
            qrItem.className = 'qr-item';
            qrItem.innerHTML = `
                <div class="qr-item-details">
                    <h4>ID: ${qr.id}</h4>
                    <p><strong>Arquivo:</strong> ${qr.filename}</p>
                    <p><strong>Gerado em:</strong> ${new Date(qr.created_at).toLocaleString()}</p>
                    <p title="${qr.data_encoded}"><strong>Dados (primeiras 50 chars):</strong> ${qr.data_encoded.substring(0, 50)}...</p>
                </div>
                <div class="qr-item-actions">
                    <button class="view-button" onclick="showQrCodeModal('${qr.qrcode_url}')">Ver QR Code</button>
                    <button class="edit-button" onclick="openEditQrCodeModal('${qr.id}')">Editar</button>
                    <button class="delete-button" onclick="deleteQrCode('${qr.id}')">Deletar</button>
                </div>
            `;
            qrCodeListDiv.appendChild(qrItem);
        });

    } catch (error) {
        qrCodeListDiv.innerHTML = `<p class="message error">Erro ao carregar lista de QR Codes: ${error.message}</p>`;
        console.error("Erro ao listar QR Codes:", error);
    }
}

// --- Lógica para Visualizar QR Code (em nova aba) ---
function showQrCodeModal(imageUrl) {
    // Abre a imagem do QR Code em uma nova aba/janela do navegador
    window.open(`${API_BASE_URL}${imageUrl}`, '_blank');
}

// --- Lógica para Deletar QR Code ---
async function deleteQrCode(qrcodeId) {
    if (!confirm(`Tem certeza que deseja deletar o QR Code com ID: ${qrcodeId}? Esta ação é irreversível.`)) {
        return; // O usuário cancelou a exclusão
    }

    try {
        const response = await fetch(`${API_BASE_URL}/delete_qrcode/${qrcodeId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message);
            listQrCodes(); // Recarrega a lista de QR Codes após a exclusão
        } else {
            alert(`Erro ao deletar QR Code: ${result.error || 'Erro desconhecido'}`);
        }
    } catch (error) {
        alert(`Erro de conexão ao tentar deletar o QR Code: ${error.message}`);
        console.error("Erro ao deletar QR Code:", error);
    }
}

// --- Lógica para Buscar Dados de Exemplo do Servidor ---
async function fetchServerData() {
    const serverDataElement = document.getElementById('server_data');
    serverDataElement.textContent = 'Carregando dados do servidor...'; // Mensagem de carregamento

    try {
        const response = await fetch(`${API_BASE_URL}/dados`);
        if (!response.ok) {
            throw new Error(`Erro HTTP! Status: ${response.status}`);
        }
        const data = await response.json();
        serverDataElement.textContent = JSON.stringify(data, null, 2); // Exibe o JSON formatado
    } catch (error) {
        serverDataElement.textContent = `Erro ao buscar dados do servidor: ${error.message}`;
        console.error("Erro ao buscar dados do servidor:", error);
    }
}

// --- NOVO: Funções para o Modal de Edição de QR Code ---
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

async function openEditQrCodeModal(qrcodeId) {
    const editQrCodeModal = document.getElementById('editQrCodeModal');
    const editQrId = document.getElementById('editQrId');
    const editQrData = document.getElementById('editQrData');
    const editMessage = document.getElementById('editMessage');

    // Limpa mensagens anteriores
    editMessage.textContent = '';
    editMessage.className = "message";

    editQrId.textContent = qrcodeId;
    editQrData.value = 'Carregando dados...';
    editQrCodeModal.style.display = 'block'; // Mostra o modal

    try {
        const response = await fetch(`${API_BASE_URL}/get_qrcode_data/${qrcodeId}`);
        if (!response.ok) {
            throw new Error(`Erro ao buscar dados do QR Code: ${response.status}`);
        }
        const data = await response.json();
        editQrData.value = data.data_encoded; // Preenche a área de texto com os dados atuais
    } catch (error) {
        editMessage.textContent = `Erro ao carregar dados para edição: ${error.message}`;
        editMessage.className = "message error";
        console.error("Erro ao carregar dados para edição:", error);
        editQrData.value = 'Erro ao carregar. Tente novamente.';
    }
}

document.getElementById('saveQrChangesButton').addEventListener('click', async function() {
    const qrcodeId = document.getElementById('editQrId').textContent;
    const new_data_encoded = document.getElementById('editQrData').value;
    const editMessage = document.getElementById('editMessage');

    editMessage.textContent = 'Salvando alterações e regerando QR Code...';
    editMessage.className = "message info";

    try {
        const response = await fetch(`${API_BASE_URL}/update_qrcode/${qrcodeId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ new_data_encoded: new_data_encoded })
        });

        const result = await response.json();

        if (response.ok) {
            editMessage.textContent = result.message;
            editMessage.className = "message success";
            alert(result.message); // Alerta para o usuário
            closeModal('editQrCodeModal'); // Fecha o modal
            listQrCodes(); // Recarrega a lista de QR Codes para mostrar o novo (se tiver um novo ID)
        } else {
            editMessage.textContent = `Erro ao salvar alterações: ${result.error || 'Erro desconhecido'}`;
            editMessage.className = "message error";
        }
    } catch (error) {
        editMessage.textContent = `Erro de conexão ao salvar: ${error.message}`;
        editMessage.className = "message error";
        console.error("Erro ao salvar alterações do QR Code:", error);
    }
});

// --- Inicialização: Ativa a primeira aba ao carregar a página ---
document.addEventListener("DOMContentLoaded", function() {
    // Simula um clique no botão da primeira aba ativa para carregar o conteúdo inicial
    document.querySelector(".tab-button.active").click(); 
});