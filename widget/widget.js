/**
 * ===========================================
 * WIDGET DE CHAT - LÓGICA (JavaScript)
 * ===========================================
 * 
 * Este archivo es el "cerebro" del widget.
 * Hace que todo funcione: abrir/cerrar chat, enviar mensajes, etc.
 * 
 * Analogía: Si el CSS es la "ropa", este JS es el "cerebro".
 * 
 * ¿Cómo funciona?
 * 1. Cuando la página carga, este script se ejecuta
 * 2. Crea automáticamente el botón y la ventana de chat
 * 3. Cuando el usuario escribe, envía el mensaje a tu API
 * 4. Muestra la respuesta del bot
 */


// ===========================================
// CONFIGURACIÓN
// ===========================================
// El cliente puede personalizar estas opciones
const ChatWidgetConfig = {
    // URL de tu API (cambiar en producción)
    apiUrl: 'http://127.0.0.1:8000',
    
    // ID del negocio (para RAG multi-tenant)
    businessId: null,
    
    // Textos personalizables
    title: '💬 Chat de Soporte',
    placeholder: 'Escribe tu mensaje...',
    welcomeMessage: '¡Hola! 👋 ¿En qué puedo ayudarte hoy?',
    
    // Colores (para futuro)
    primaryColor: '#2563eb',
};


// ===========================================
// ESTADO DEL WIDGET
// ===========================================
// Guardamos información mientras el usuario chatea
const ChatWidgetState = {
    isOpen: false,           // ¿Está abierto el chat?
    messages: [],            // Historial de mensajes
    isLoading: false,        // ¿Está esperando respuesta?
};


// ===========================================
// 1. CREAR EL HTML DEL WIDGET
// ===========================================
// Esta función crea todos los elementos HTML necesarios
function createWidgetHTML() {
    // Crear el contenedor principal
    const widgetWrapper = document.createElement('div');
    widgetWrapper.id = 'chat-widget-wrapper';
    
    // El HTML del widget completo
    widgetWrapper.innerHTML = `
        <!-- Botón flotante para abrir el chat -->
        <button class="chat-widget-button" id="chat-widget-toggle">
            <span class="chat-widget-button-icon">💬</span>
        </button>
        
        <!-- Ventana del chat (oculta por defecto) -->
        <div class="chat-widget-container" id="chat-widget-container">
            <!-- Header -->
            <div class="chat-widget-header">
                <h3 class="chat-widget-title">${ChatWidgetConfig.title}</h3>
                <button class="chat-widget-close" id="chat-widget-close">×</button>
            </div>
            
            <!-- Área de mensajes -->
            <div class="chat-widget-messages" id="chat-widget-messages">
                <!-- Los mensajes se añaden aquí dinámicamente -->
            </div>
            
            <!-- Input para escribir -->
            <div class="chat-widget-input-container">
                <input 
                    type="text" 
                    class="chat-widget-input" 
                    id="chat-widget-input"
                    placeholder="${ChatWidgetConfig.placeholder}"
                >
                <button class="chat-widget-send" id="chat-widget-send">
                    Enviar
                </button>
            </div>
        </div>
    `;
    
    // Añadir al body de la página
    document.body.appendChild(widgetWrapper);
}


// ===========================================
// 2. CARGAR LOS ESTILOS CSS
// ===========================================
function loadWidgetStyles() {
    // Crear un elemento <link> para cargar el CSS
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    // Asume que el CSS está en la misma carpeta que el JS
    link.href = ChatWidgetConfig.apiUrl + '/static/widget.css';
    document.head.appendChild(link);
}


// ===========================================
// 3. ABRIR/CERRAR EL CHAT
// ===========================================
function toggleChat() {
    const container = document.getElementById('chat-widget-container');
    const button = document.getElementById('chat-widget-toggle');
    
    ChatWidgetState.isOpen = !ChatWidgetState.isOpen;
    
    if (ChatWidgetState.isOpen) {
        // Abrir chat
        container.classList.add('open');
        button.innerHTML = '<span class="chat-widget-button-icon">✕</span>';
        
        // Mostrar mensaje de bienvenida si es la primera vez
        if (ChatWidgetState.messages.length === 0) {
            addMessage('assistant', ChatWidgetConfig.welcomeMessage);
        }
        
        // Focus en el input
        document.getElementById('chat-widget-input').focus();
    } else {
        // Cerrar chat
        container.classList.remove('open');
        button.innerHTML = '<span class="chat-widget-button-icon">💬</span>';
    }
}


// ===========================================
// 4. AÑADIR UN MENSAJE AL CHAT
// ===========================================
// role: 'user' o 'assistant'
// content: el texto del mensaje
function addMessage(role, content) {
    const messagesContainer = document.getElementById('chat-widget-messages');
    
    // Crear el elemento del mensaje
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    
    messageDiv.innerHTML = `
        <div class="chat-message-bubble">
            ${escapeHTML(content)}
        </div>
    `;
    
    // Añadir al contenedor
    messagesContainer.appendChild(messageDiv);
    
    // Scroll hacia abajo para ver el nuevo mensaje
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Guardar en el historial
    ChatWidgetState.messages.push({ role, content });
}


// ===========================================
// 5. MOSTRAR/OCULTAR "ESCRIBIENDO..."
// ===========================================
function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-widget-messages');
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message assistant';
    typingDiv.id = 'typing-indicator';
    
    typingDiv.innerHTML = `
        <div class="chat-typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    const typingDiv = document.getElementById('typing-indicator');
    if (typingDiv) {
        typingDiv.remove();
    }
}


// ===========================================
// 6. ENVIAR MENSAJE A LA API
// ===========================================
async function sendMessage() {
    const input = document.getElementById('chat-widget-input');
    const sendButton = document.getElementById('chat-widget-send');
    const userMessage = input.value.trim();
    
    // No enviar si está vacío o ya estamos cargando
    if (!userMessage || ChatWidgetState.isLoading) {
        return;
    }
    
    // Limpiar input
    input.value = '';
    
    // Mostrar mensaje del usuario
    addMessage('user', userMessage);
    
    // Estado: cargando
    ChatWidgetState.isLoading = true;
    sendButton.disabled = true;
    showTypingIndicator();
    
    try {
        // Preparar los mensajes para la API
        // Formato que espera tu endpoint /chat
        const messagesForAPI = ChatWidgetState.messages.map(msg => ({
            role: msg.role,
            content: msg.content
        }));
        
        // Llamar a tu API
        const response = await fetch(`${ChatWidgetConfig.apiUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                messages: messagesForAPI,
                business_id: ChatWidgetConfig.businessId
            })
        });
        
        // Verificar si la respuesta fue exitosa
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        // Parsear la respuesta JSON
        const data = await response.json();
        
        // Ocultar "escribiendo..." y mostrar respuesta
        hideTypingIndicator();
        addMessage('assistant', data.reply);
        
    } catch (error) {
        // Si hay error, mostrar mensaje de error
        console.error('Error al enviar mensaje:', error);
        hideTypingIndicator();
        addMessage('assistant', 'Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo.');
    } finally {
        // Restaurar estado
        ChatWidgetState.isLoading = false;
        sendButton.disabled = false;
        input.focus();
    }
}


// ===========================================
// 7. UTILIDADES
// ===========================================

// Escapar HTML para prevenir inyección de código (seguridad)
function escapeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


// ===========================================
// 8. INICIALIZAR EL WIDGET
// ===========================================
function initChatWidget(config = {}) {
    // Mezclar configuración por defecto con la del usuario
    Object.assign(ChatWidgetConfig, config);
    
    // Cargar estilos
    loadWidgetStyles();
    
    // Crear el HTML
    createWidgetHTML();
    
    // Event listeners
    
    // Click en botón flotante → abrir/cerrar chat
    document.getElementById('chat-widget-toggle').addEventListener('click', toggleChat);
    
    // Click en X → cerrar chat
    document.getElementById('chat-widget-close').addEventListener('click', toggleChat);
    
    // Click en "Enviar" → enviar mensaje
    document.getElementById('chat-widget-send').addEventListener('click', sendMessage);
    
    // Enter en input → enviar mensaje
    document.getElementById('chat-widget-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    console.log('✅ Chat Widget inicializado');
}


// ===========================================
// 9. AUTO-INICIALIZAR CUANDO CARGA LA PÁGINA
// ===========================================
// Si el script tiene el atributo data-auto-init="true", se inicializa solo
if (document.currentScript && document.currentScript.getAttribute('data-auto-init') === 'true') {
    // Esperar a que el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => initChatWidget());
    } else {
        initChatWidget();
    }
}


// Exportar para uso manual
window.ChatWidget = {
    init: initChatWidget,
    config: ChatWidgetConfig,
};
