let sessionId = null;

document.getElementById('file-input').addEventListener('change', async function() {
    const file = this.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    const status = document.getElementById('upload-status');
    status.className = '';
    status.textContent = 'Uploading...';

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            sessionId = data.session_id;
	    console.log("session ID set:", sessionId);
            status.className = 'success';
            status.textContent = `✓ ${data.filename} uploaded — ${data.chunks_created} chunks created`;
            document.getElementById('chat-section').style.display = 'block';
        } else {
            status.className = 'error';
            status.textContent = `✗ ${data.detail}`;
        }
    } catch (error) {
        status.className = 'error';
        status.textContent = '✗ Upload failed. Please try again.';
    }
});

async function sendQuestion() {
    const input = document.getElementById('question-input');
    const question = input.value.trim();
    if (!question || !sessionId) return;

    appendMessage('user', question);
    input.value = '';

    const thinking = appendMessage('ai', 'Thinking...');

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, session_id: sessionId })
        });

        const data = await response.json();
        thinking.textContent = data.answer;
    } catch (error) {
        thinking.textContent = 'Something went wrong. Please try again.';
    }
}

function appendMessage(role, text) {
    const chatBox = document.getElementById('chat-box');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
}

document.getElementById('question-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') sendQuestion();
});
