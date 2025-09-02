// Script for handling modals, API calls, events, swipes, etc.

// Global vars
let currentUserId = null;
let currentSection = 'home';

// Load on start
document.addEventListener('DOMContentLoaded', () => {
    checkLogin();
    loadSection('home');
    // Event listeners for nav buttons
    document.querySelectorAll('nav button').forEach(btn => {
        btn.addEventListener('click', () => {
            const section = btn.id.replace('-btn', '');
            loadSection(section);
        });
    });
});

// Check if logged in
async function checkLogin() {
    const response = await fetch('/api/profile', { method: 'GET' });
    if (response.ok) {
        const data = await response.json();
        currentUserId = data.id;
        if (data.is_admin) {
            document.getElementById('admin-btn').style.display = 'block';
        }
    } else {
        // Redirect to login modal or page, but since single HTML, show login modal
        showModal('login-modal');
    }
}

// Load section
async function loadSection(section) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(section).classList.add('active');
    currentSection = section;
    switch (section) {
        case 'home':
            loadHome();
            break;
        case 'reels':
            loadReels();
            break;
        case 'friends':
            loadFriends();
            break;
        case 'inbox':
            loadInbox();
            break;
        case 'profile':
            loadProfile(currentUserId);
            break;
        case 'search':
            loadSearch();
            break;
        case 'addto':
            loadAddTo();
            break;
        case 'notifications':
            loadNotifications();
            break;
        case 'menu':
            loadMenu();
            break;
        case 'admin':
            loadAdmin();
            break;
    }
}

// Show modal
function showModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
}

// Close modal
document.querySelectorAll('.close').forEach(close => {
    close.addEventListener('click', () => {
        close.parentElement.style.display = 'none';
    });
});

// Login form
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const identifier = document.getElementById('login-identifier').value;
    const password = document.getElementById('login-password').value;
    const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier, password })
    });
    if (response.ok) {
        checkLogin();
        showModal('none'); // Close
        loadSection('home');
    } else {
        alert('Login failed');
    }
});

// Register form
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;
    const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await response.json();
    if (response.ok) {
        alert(`Registered! Unique key: ${data.unique_key}`);
        showModal('login-modal');
    } else {
        alert(data.error);
    }
});

// Forgot form
document.getElementById('forgot-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('forgot-username').value;
    const key = document.getElementById('forgot-key').value;
    const response = await fetch('/api/forgot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, unique_key: key })
    });
    if (response.ok) {
        showModal('reset-modal');
    } else {
        alert('Invalid');
    }
});

// Reset form
document.getElementById('reset-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const password = document.getElementById('reset-password').value;
    const response = await fetch('/api/reset_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
    });
    if (response.ok) {
        alert('Reset successful');
        showModal('login-modal');
    } else {
        alert('Error');
    }
});

// Load home
async function loadHome() {
    const response = await fetch('/api/home');
    const data = await response.json();
    const storiesDiv = document.getElementById('home-stories');
    storiesDiv.innerHTML = '';
    data.stories.forEach(s => {
        const circle = document.createElement('div');
        circle.classList.add('story-circle');
        circle.innerHTML = `<img src="${s.media_url || '/static/default.jpg'}"><span>${s.user}</span>`;
