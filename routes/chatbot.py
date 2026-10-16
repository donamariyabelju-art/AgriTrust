from flask import Blueprint, render_template, request, jsonify
from services.chatbot_service import get_chatbot_response, SUGGESTED_PROMPTS

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/chatbot')
def chatbot_view():
    return render_template('chatbot.html', suggested_prompts=SUGGESTED_PROMPTS)

@chatbot_bp.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'Message content cannot be empty.'}), 400

    response_data = get_chatbot_response(message)
    return jsonify(response_data)
