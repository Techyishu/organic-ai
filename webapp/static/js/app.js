// Initialize Telegram WebApp
const webapp = window.Telegram.WebApp;
webapp.ready();

// Set theme colors
document.documentElement.style.setProperty('--tg-theme-bg-color', webapp.backgroundColor);
document.documentElement.style.setProperty('--tg-theme-text-color', webapp.textColor);
document.documentElement.style.setProperty('--tg-theme-button-color', webapp.buttonColor);
document.documentElement.style.setProperty('--tg-theme-button-text-color', webapp.buttonTextColor);

// Load topics
async function loadTopics() {
    const response = await fetch('/api/topics');
    const topics = await response.json();
    const topicGrid = document.getElementById('topicGrid');
    
    topics.forEach(topic => {
        const topicCard = document.createElement('div');
        topicCard.className = 'topic-card';
        topicCard.textContent = topic;
        topicCard.onclick = () => startDebate(topic);
        topicGrid.appendChild(topicCard);
    });
}

// Start debate
async function startDebate(topic) {
    topic = topic || document.getElementById('customTopic').value;
    if (!topic) return;

    const response = await fetch('/api/debate/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            topic,
            user_id: webapp.initDataUnsafe.user.id
        })
    });

    if (response.ok) {
        window.location.href = `/debate/${encodeURIComponent(topic)}`;
    }
}

// Send message
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    if (!message) return;

    const chatContainer = document.getElementById('chatContainer');
    
    // Add user message
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'message user-message';
    userMessageDiv.textContent = message;
    chatContainer.appendChild(userMessageDiv);
    
    // Clear input
    messageInput.value = '';

    // Send to server
    const response = await fetch('/api/debate/message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message,
            user_id: webapp.initDataUnsafe.user.id
        })
    });

    if (response.ok) {
        const data = await response.json();
        
        // Add bot response
        const botMessageDiv = document.createElement('div');
        botMessageDiv.className = 'message bot-message';
        botMessageDiv.textContent = data.response;
        chatContainer.appendChild(botMessageDiv);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Load topics on page load if we're on the index page
if (document.getElementById('topicGrid')) {
    loadTopics();
} 