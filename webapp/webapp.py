from flask import Flask, render_template, jsonify, request
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/debate/<topic>')
def debate(topic):
    """Render the debate page for a specific topic."""
    return render_template('debate.html', topic=topic)

@app.route('/api/topics')
def get_topics():
    """Get predefined debate topics."""
    topics = os.getenv('PREDEFINED_TOPICS', '').split(',')
    return jsonify(topics)

@app.route('/api/debate/start', methods=['POST'])
def start_debate():
    """Start a new debate session."""
    data = request.json
    topic = data.get('topic')
    user_id = data.get('user_id')
    
    # Here you would integrate with your debate manager
    return jsonify({
        'status': 'success',
        'message': f'Started debate on {topic}'
    })

@app.route('/api/debate/message', methods=['POST'])
def send_message():
    """Send a message in the debate."""
    data = request.json
    message = data.get('message')
    user_id = data.get('user_id')
    
    # Here you would integrate with your debate manager
    return jsonify({
        'status': 'success',
        'response': 'Bot response here'
    })

if __name__ == '__main__':
    app.run(debug=True) 