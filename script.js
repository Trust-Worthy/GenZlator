import { translateGenZ, containsGenZSlang } from './translate.js';

// Authentication state
let currentUser = null;
let users = [];
let currentChatId = null;

// DOM Elements
const chatList = document.querySelector('.chat-list');
const messagesContainer = document.querySelector('.messages');
const messageInput = document.querySelector('.message-input input');
const sendButton = document.querySelector('.send-btn');
const newChatButton = document.querySelector('.new-chat-btn');
const searchInput = document.querySelector('.search-bar input');
const chatHeader = document.querySelector('.chat-header-info h2');
const statusIndicator = document.querySelector('.status');
const authContainer = document.querySelector('.auth-container');
const loginForm = document.querySelector('#loginForm');
const registerForm = document.querySelector('#registerForm');
const authToggle = document.querySelector('.auth-toggle');

// Initialize the app
async function init() {
    try {
        const response = await fetch('http://localhost:3001/api/me', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            await loadUsers();
            showMainInterface();
        } else {
            showAuthInterface();
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
        showAuthInterface();
    }
}

// Load all users
async function loadUsers() {
    try {
        const response = await fetch('http://localhost:3001/api/users', {
            credentials: 'include'
        });
        if (response.ok) {
            users = await response.json();
            renderChatList();
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Show authentication interface
function showAuthInterface() {
    document.querySelector('.main-container').style.display = 'none';
    authContainer.style.display = 'flex';
}

// Show main chat interface
function showMainInterface() {
    document.querySelector('.main-container').style.display = 'flex';
    authContainer.style.display = 'none';
    document.getElementById('currentUsername').textContent = currentUser.username;
    renderChatList();
}

// Render chat list
function renderChatList() {
    chatList.innerHTML = users.map(user => `
        <div class="chat-item ${user._id === currentChatId ? 'active' : ''}" data-user-id="${user._id}">
            <div class="chat-avatar">
                <i class="fas fa-user"></i>
            </div>
            <div class="chat-info">
                <div class="chat-header">
                    <h3>${user.username}</h3>
                </div>
                <p>Click to start chatting</p>
            </div>
        </div>
    `).join('');

    // Add click event listeners to chat items
    document.querySelectorAll('.chat-item').forEach(item => {
        item.addEventListener('click', () => {
            const userId = item.dataset.userId;
            switchChat(userId);
        });
    });
}

// Switch between chats
async function switchChat(userId) {
    currentChatId = userId;
    renderChatList();
    await loadMessages(userId);
    updateChatHeader(userId);
}

// Load messages for a specific chat
async function loadMessages(userId) {
    try {
        const response = await fetch(`http://localhost:3001/api/messages/${userId}`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const messages = await response.json();
            renderMessages(messages);
        }
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

// Render messages
function renderMessages(messages) {
    messagesContainer.innerHTML = messages.map(message => `
        <div class="message ${message.sender._id === currentUser.id ? 'sent' : 'received'}">
            <div class="message-content">
                <p>${message.text}</p>
                <span class="message-time">${new Date(message.createdAt).toLocaleTimeString()}</span>
            </div>
        </div>
    `).join('');

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Update chat header
function updateChatHeader(userId) {
    const user = users.find(u => u._id === userId);
    if (!user) return;

    chatHeader.textContent = user.username;
    statusIndicator.textContent = 'Active Now';
}

// Send a new message
async function sendMessage() {
    if (!currentChatId) return;
    
    const messageText = messageInput.value.trim();
    if (!messageText) return;

    try {
        const response = await fetch('http://localhost:3001/api/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                receiverId: currentChatId,
                text: messageText
            })
        });

        if (response.ok) {
            messageInput.value = '';
            await loadMessages(currentChatId);
        }
    } catch (error) {
        console.error('Error sending message:', error);
    }
}

// Handle login
async function handleLogin(event) {
    event.preventDefault();
    const email = document.querySelector('#loginEmail').value;
    const password = document.querySelector('#loginPassword').value;

    try {
        const response = await fetch('http://localhost:3001/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            await loadUsers();
            showMainInterface();
        } else {
            alert(data.error || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed');
    }
}

// Handle registration
async function handleRegister(event) {
    event.preventDefault();
    const username = document.querySelector('#registerUsername').value;
    const email = document.querySelector('#registerEmail').value;
    const password = document.querySelector('#registerPassword').value;

    try {
        const response = await fetch('http://localhost:3001/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            await loadUsers();
            showMainInterface();
        } else {
            alert(data.error || 'Registration failed');
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('Registration failed');
    }
}

// Handle logout
async function handleLogout() {
    try {
        await fetch('http://localhost:3001/api/logout', {
            method: 'POST',
            credentials: 'include'
        });
        currentUser = null;
        currentChatId = null;
        users = [];
        document.getElementById('currentUsername').textContent = 'Loading...';
        showAuthInterface();
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Toggle between login and register forms
function toggleAuthForm() {
    loginForm.style.display = loginForm.style.display === 'none' ? 'block' : 'none';
    registerForm.style.display = registerForm.style.display === 'none' ? 'block' : 'none';
    authToggle.textContent = loginForm.style.display === 'none' ? 'Login' : 'Register';
}

// Event Listeners
loginForm.addEventListener('submit', handleLogin);
registerForm.addEventListener('submit', handleRegister);
authToggle.addEventListener('click', toggleAuthForm);
sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
document.getElementById('logoutBtn').addEventListener('click', handleLogout);

// Initialize the app
init(); 