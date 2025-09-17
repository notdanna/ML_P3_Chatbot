from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from utils.automata import get_automata
import os

app = Flask(__name__)
CORS(app)  # Permitir solicitudes desde cualquier origen

# Obtener la instancia del autómata
automata = get_automata()

# HTML de la interfaz (puedes moverlo a un archivo separado si prefieres)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAES Chat - Sistema Académico</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #069 0%, #611232 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            gap: 20px;
        }

        .main-container {
            display: flex;
            width: 100%;
            max-width: 1400px;
            gap: 20px;
            height: 90vh;
        }

        .chat-container {
            background: #FFF;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            flex: 1;
            min-width: 600px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .info-card {
            background: #FFF;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            width: 350px;
            padding: 25px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            overflow-y: auto;
        }

        .chat-header {
            background: linear-gradient(135deg, #069 0%, #611232 100%);
            color: #FFF;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            position: relative;
        }

        .chat-header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }

        .chat-header p {
            opacity: 0.9;
            font-size: 14px;
        }

        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background-color: #f8f9fa;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .message {
            max-width: 80%;
            padding: 12px 18px;
            border-radius: 18px;
            word-wrap: break-word;
            animation: fadeIn 0.3s ease-in;
            white-space: pre-line;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            background: linear-gradient(135deg, #069 0%, #611232 100%);
            color: #FFF;
            align-self: flex-end;
            margin-left: auto;
        }

        .message.bot {
            background: #FFF;
            color: #333;
            align-self: flex-start;
            border: 1px solid #069;
            box-shadow: 0 2px 5px rgba(6, 102, 153, 0.1);
        }

        .message.system {
            background: #fff3cd;
            color: #611232;
            align-self: center;
            border: 1px solid #069;
            font-style: italic;
            text-align: center;
            max-width: 90%;
        }

        .chat-input-container {
            padding: 20px;
            background: #FFF;
            border-top: 1px solid #069;
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .chat-input {
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #e1e5e9;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: all 0.3s ease;
        }

        .chat-input:focus {
            border-color: #069;
            box-shadow: 0 0 0 3px rgba(6, 102, 153, 0.1);
        }

        .send-button {
            background: linear-gradient(135deg, #069 0%, #611232 100%);
            color: #FFF;
            border: none;
            border-radius: 50%;
            width: 48px;
            height: 48px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            font-size: 18px;
        }

        .send-button:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(6, 102, 153, 0.3);
        }

        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .typing-indicator {
            display: none;
            padding: 12px 18px;
            background: white;
            border: 1px solid #e1e5e9;
            border-radius: 18px;
            align-self: flex-start;
            max-width: 80px;
        }

        .typing-dots {
            display: flex;
            gap: 4px;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #667eea;
            animation: typing 1.5s infinite;
        }

        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: scale(1); opacity: 0.5; }
            30% { transform: scale(1.2); opacity: 1; }
        }

        .quick-actions {
            display: flex;
            gap: 10px;
            padding: 15px 20px 0;
            flex-wrap: wrap;
        }

        .quick-action {
            background: #f8f9fa;
            border: 1px solid #e1e5e9;
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
            white-space: nowrap;
        }

        .quick-action:hover {
            background: #069;
            color: #FFF;
            transform: translateY(-2px);
        }

        .status-indicator {
            position: absolute;
            top: 20px;
            right: 20px;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            background: #FFF;
            color: #069;
        }

        .info-card h3 {
            color: #069;
            font-size: 18px;
            margin: 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #069;
        }

        .info-section {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #069;
        }

        .info-section h4 {
            color: #611232;
            font-size: 14px;
            margin: 0 0 10px 0;
        }

        .info-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .info-list li {
            padding: 5px 0;
            color: #333;
            font-size: 13px;
            position: relative;
            padding-left: 15px;
        }

        .info-list li:before {
            content: "•";
            color: #069;
            font-weight: bold;
            position: absolute;
            left: 0;
        }

        .info-link {
            background: linear-gradient(135deg, #069 0%, #611232 100%);
            color: #FFF;
            text-decoration: none;
            padding: 12px 16px;
            border-radius: 8px;
            text-align: center;
            display: block;
            font-size: 14px;
            font-weight: bold;
            transition: all 0.3s ease;
        }

        .info-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(6, 102, 153, 0.3);
            color: #FFF;
            text-decoration: none;
        }

        .ipn-logo {
            text-align: center;
            margin-bottom: 20px;
        }

        .ipn-logo .logo-text {
            font-size: 20px;
            font-weight: bold;
            color: #069;
        }

        .ipn-logo .logo-subtext {
            font-size: 12px;
            color: #611232;
            margin-top: 5px;
        }

        /* Responsive */
        @media (max-width: 1200px) {
            .main-container {
                flex-direction: column;
                height: auto;
            }
            
            .chat-container {
                min-width: auto;
                height: 70vh;
            }
            
            .info-card {
                width: 100%;
                height: auto;
                max-height: 300px;
            }
        }

        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .chat-container {
                height: 80vh;
                border-radius: 15px;
            }
            
            .message {
                max-width: 90%;
            }
            
            .chat-header h1 {
                font-size: 20px;
            }
            
            .quick-actions {
                justify-content: center;
            }
            
            .info-card {
                padding: 15px;
            }
        }

        /* Scrollbar personalizado */
        .chat-messages::-webkit-scrollbar, .info-card::-webkit-scrollbar {
            width: 6px;
        }

        .chat-messages::-webkit-scrollbar-track, .info-card::-webkit-scrollbar-track {
            background: transparent;
        }

        .chat-messages::-webkit-scrollbar-thumb, .info-card::-webkit-scrollbar-thumb {
            background: rgba(6, 102, 153, 0.3);
            border-radius: 3px;
        }

        .chat-messages::-webkit-scrollbar-thumb:hover, .info-card::-webkit-scrollbar-thumb:hover {
            background: rgba(6, 102, 153, 0.5);
        }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="chat-container">
            <div class="chat-header">
                <div class="status-indicator" id="statusIndicator">🟢 Conectado</div>
                <h1>🎓 SAES Chat</h1>
                <p>Sistema Académico Estudiantil - IPN</p>
            </div>

            <div class="quick-actions" id="quickActions">
                <div class="quick-action" data-action="iniciar sesion">Iniciar Sesión</div>
                <div class="quick-action" data-action="info academica">Info Académica</div>
                <div class="quick-action" data-action="calificaciones">Calificaciones</div>
                <div class="quick-action" data-action="materias">Materias</div>
                <div class="quick-action" data-action="inscripcion">Inscripción</div>
                <div class="quick-action" data-action="tramites">Trámites</div>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div class="message system">
                    🤖 ¡Hola! Soy tu asistente del SAES. Para comenzar, inicia sesión con tu boleta y contraseña.
                </div>
            </div>

            <div class="typing-indicator" id="typingIndicator">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>

            <div class="chat-input-container">
                <input 
                    type="text" 
                    class="chat-input" 
                    id="messageInput" 
                    placeholder="Escribe tu mensaje aquí..."
                    maxlength="500"
                >
                <button class="send-button" id="sendButton" title="Enviar mensaje">
                    ➤
                </button>
            </div>
        </div>

        <div class="info-card">
            <div class="ipn-logo">
                <div class="logo-text">🏛️ IPN</div>
                <div class="logo-subtext">Instituto Politécnico Nacional</div>
            </div>

            <h3>💡 Información del Sistema</h3>

            <div class="info-section">
                <h4>✅ Funciones Disponibles:</h4>
                <ul class="info-list">
                    <li>Iniciar/Cerrar sesión</li>
                    <li>Consultar calificaciones</li>
                    <li>Ver información académica</li>
                    <li>Revisar materias disponibles</li>
                    <li>Proceso de inscripción</li>
                    <li>Solicitar trámites escolares</li>
                    <li>Consultar ETS (Exámenes a Título de Suficiencia)</li>
                </ul>
            </div>

            <div class="info-section">
                <h4>❌ Limitaciones:</h4>
                <ul class="info-list">
                    <li>No realiza inscripciones reales</li>
                    <li>No modifica calificaciones</li>
                    <li>Solo consulta información</li>
                    <li>Requiere datos precargados en CSV</li>
                </ul>
            </div>

            <div class="info-section">
                <h4>🔒 Seguridad:</h4>
                <ul class="info-list">
                    <li>Requiere autenticación con boleta</li>
                    <li>Validación de contraseña</li>
                    <li>Sesiones individuales</li>
                    <li>Datos protegidos por usuario</li>
                </ul>
            </div>

            <div class="info-section">
                <h4>🚀 Comandos Básicos:</h4>
                <ul class="info-list">
                    <li>"iniciar sesion" - Para autenticarse</li>
                    <li>"calificaciones" - Ver notas</li>
                    <li>"materias" - Materias disponibles</li>
                    <li>"tramites" - Servicios escolares</li>
                    <li>"ets" - Materias reprobadas</li>
                    <li>"cerrar sesion" - Salir</li>
                </ul>
            </div>

            <a href="https://www.escom.ipn.mx/#" target="_blank" class="info-link">
                🔗 Para más información consulta ESCOM
            </a>
        </div>
    </div>

    <script>
        class SAESChatInterface {
            constructor() {
                this.chatMessages = document.getElementById('chatMessages');
                this.messageInput = document.getElementById('messageInput');
                this.sendButton = document.getElementById('sendButton');
                this.typingIndicator = document.getElementById('typingIndicator');
                this.quickActions = document.getElementById('quickActions');
                
                this.isTyping = false;
                
                this.initializeEventListeners();
            }

            initializeEventListeners() {
                // Enviar mensaje con Enter
                this.messageInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        this.sendMessage();
                    }
                });

                // Enviar mensaje con botón
                this.sendButton.addEventListener('click', () => {
                    this.sendMessage();
                });

                // Acciones rápidas
                this.quickActions.addEventListener('click', (e) => {
                    if (e.target.classList.contains('quick-action')) {
                        const action = e.target.dataset.action;
                        this.messageInput.value = action;
                        this.sendMessage();
                    }
                });
            }

            async sendMessage() {
                const message = this.messageInput.value.trim();
                if (!message || this.isTyping) return;

                // Mostrar mensaje del usuario
                this.addMessage('user', message);
                this.messageInput.value = '';
                
                // Mostrar indicador de escritura
                this.showTyping();

                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ message: message })
                    });
                    
                    if (!response.ok) {
                        throw new Error('Error en la respuesta del servidor');
                    }
                    
                    const data = await response.json();
                    
                    // Ocultar indicador y mostrar respuesta
                    this.hideTyping();
                    this.addMessage('bot', data.response);
                } catch (error) {
                    this.hideTyping();
                    this.addMessage('system', '❌ Error de conexión. Intenta nuevamente.');
                    console.error('Error:', error);
                }
            }

            addMessage(type, content) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                messageDiv.textContent = content;
                
                this.chatMessages.appendChild(messageDiv);
                this.scrollToBottom();
            }

            showTyping() {
                this.isTyping = true;
                this.typingIndicator.style.display = 'block';
                this.sendButton.disabled = true;
                this.scrollToBottom();
            }

            hideTyping() {
                this.isTyping = false;
                this.typingIndicator.style.display = 'none';
                this.sendButton.disabled = false;
            }

            scrollToBottom() {
                setTimeout(() => {
                    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                }, 100);
            }
        }

        // Inicializar la interfaz cuando se carga la página
        document.addEventListener('DOMContentLoaded', () => {
            window.saesChat = new SAESChatInterface();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Página principal con la interfaz del chat"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint para procesar mensajes del chat"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Mensaje requerido'}), 400
        
        user_message = data['message']
        
        # Procesar el mensaje usando tu autómata
        bot_response = automata.step(user_message)
        
        return jsonify({
            'response': bot_response,
            'status': 'success'
        })
    
    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'response': 'Lo siento, hubo un error procesando tu mensaje. Intenta nuevamente.'
        }), 500

@app.route('/api/status')
def status():
    """Endpoint para verificar el estado del servidor"""
    return jsonify({
        'status': 'online',
        'automata_state': automata.ctx.state,
        'user': automata.ctx.get('user', 'Sin sesión')
    })

@app.route('/api/reset', methods=['POST'])
def reset():
    """Endpoint para reiniciar la sesión del chatbot"""
    try:
        automata.reset()
        return jsonify({
            'status': 'success',
            'message': 'Sesión reiniciada correctamente'
        })
    except Exception as e:
        return jsonify({
            'error': 'Error reiniciando sesión'
        }), 500

if __name__ == '__main__':
    # Configurar puerto desde variable de entorno o usar 5000 por defecto
    port = int(os.environ.get('PORT', 5001))
    
    print("🚀 Iniciando SAES Chat Server...")
    print(f"📱 Interfaz disponible en: http://localhost:{port}")
    print(f"🔌 API disponible en: http://localhost:{port}/api/chat")
    print("👆 Presiona Ctrl+C para detener el servidor")
    
    app.run(
        host='0.0.0.0',  # Permite conexiones externas
        port=port,
        debug=True,      # Modo desarrollo - cambiar a False en producción
        threaded=True    # Permite múltiples conexiones simultáneas
    )