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
        circle.addEventListener('click', () => viewStory(s.id));
        storiesDiv.appendChild(circle);
    });
    loadPosts(1);
}

// View story
async function viewStory(storyId) {
    const response = await fetch(`/api/story/${storyId}`);
    const data = await response.json();
    const modal = document.getElementById('story-modal');
    const content = document.getElementById('story-content');
    content.innerHTML = data.media_url.endsWith('.mp4') ? `<video src="${data.media_url}" autoplay loop></video>` : `<img src="${data.media_url}">`;
    showModal('story-modal');
    // Touch events for swipe
    let touchStartX = 0;
    let touchEndX = 0;
    modal.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
    });
    modal.addEventListener('touchend', e => {
        touchEndX = e.changedTouches[0].screenX;
        if (touchEndX < touchStartX - 50) {
            // Next story
            nextStory();
        } else if (touchEndX > touchStartX + 50) {
            // Prev story
            prevStory();
        } else if (Math.abs(e.changedTouches[0].screenY - touchStartY) > 50) {
            // Swipe down to close
            modal.style.display = 'none';
        }
    });
    // Pause on hold
    let timer;
    modal.addEventListener('touchstart', () => {
        timer = setTimeout(() => {
            content.querySelector('video') ? content.querySelector('video').pause() : '';
        }, 200);
    });
    modal.addEventListener('touchend', () => clearTimeout(timer));
    // Assume next/prev functions fetch next story id
}

// Load posts with endless scroll
let postPage = 1;
async function loadPosts(page) {
    const response = await fetch(`/api/posts?page=${page}`);
    const data = await response.json();
    const postsDiv = document.getElementById('home-posts');
    data.posts.forEach(p => {
        const postDiv = document.createElement('div');
        postDiv.classList.add('post');
        postDiv.innerHTML = `
            <div class="post-header">
                <img src="${p.user.profile_pic || '/static/default.jpg'}">
                <div>
                    <strong>${p.user.real_name}</strong> @${p.user.username}
                    <small>${p.timestamp}</small>
                </div>
            </div>
            <p>${p.description}</p>
            ${p.media_url ? `<img src="${p.media_url}" class="post-media">` : ''}
            <div class="post-actions">
                <button onclick="likePost(${p.id})"><i class="fa fa-heart"></i> ${p.likes}</button>
                <button onclick="commentPost(${p.id})"><i class="fa fa-comment"></i> ${p.comments}</button>
                <button onclick="sharePost(${p.id})"><i class="fa fa-share"></i></button>
                ${!p.is_own ? `<button onclick="followUser(${p.user.id})"><i class="fa fa-user-plus"></i></button>` : ''}
                <button onclick="savePost(${p.id})"><i class="fa fa-bookmark"></i></button>
                ${!p.is_own ? `<button onclick="repost(${p.id})"><i class="fa fa-retweet"></i></button>` : ''}
                <small>Views: ${p.views}</small>
                ${!p.is_own ? `<button onclick="reportPost(${p.id})"><i class="fa fa-flag"></i></button>` : ''}
                <button onclick="hidePost(${p.id})"><i class="fa fa-eye-slash"></i></button>
                ${!p.is_own ? `<button onclick="blockUser(${p.user.id})"><i class="fa fa-ban"></i></button>` : ''}
            </div>
        `;
        postsDiv.appendChild(postDiv);
    });
    if (data.has_next) {
        postPage++;
        // Endless scroll listener
        window.addEventListener('scroll', () => {
            if (window.innerHeight + window.scrollY >= document.body.offsetHeight) {
                loadPosts(postPage);
            }
        });
    }
}

// Similar for reels load, with video tags and touch pause
async function loadReels() {
    const response = await fetch('/api/reels');
    const data = await response.json();
    const reelsDiv = document.getElementById('reels-container');
    reelsDiv.innerHTML = '';
    data.reels.forEach(r => {
        const reelDiv = document.createElement('div');
        reelDiv.classList.add('reel');
        reelDiv.innerHTML = `
            <video src="${r.media_url}" autoplay loop></video>
            <div class="reel-info">
                <strong>${r.user.real_name}</strong> @${r.user.username}
                <p>${r.description}</p>
            </div>
            <div class="reel-actions">
                <button onclick="followUser(${r.user.id})"><i class="fa fa-plus-circle"></i></button>
                <button onclick="likePost(${r.id})"><i class="fa fa-heart"></i></button>
                <button onclick="repost(${r.id})"><i class="fa fa-retweet"></i></button>
                <button onclick="commentPost(${r.id})"><i class="fa fa-comment"></i></button>
                <button onclick="sharePost(${r.id})"><i class="fa fa-share"></i></button>
                <button onclick="savePost(${r.id})"><i class="fa fa-bookmark"></i></button>
                <button onclick="downloadReel(${r.id})"><i class="fa fa-download"></i></button>
            </div>
        `;
        // Touch to pause/play
        reelDiv.addEventListener('touchstart', () => {
            const video = reelDiv.querySelector('video');
            video.paused ? video.play() : video.pause();
        });
        reelsDiv.appendChild(reelDiv);
    });
}

// Friends load with tabs
async function loadFriends() {
    const tabs = document.querySelectorAll('#friends-tabs button');
    tabs.forEach(tab => {
        tab.addEventListener('click', async () => {
            const type = tab.id.replace('-tab', '');
            const response = await fetch(`/api/friends/${type}`);
            const data = await response.json();
            const list = document.getElementById('friends-list');
            list.innerHTML = '';
            data[type].forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <img src="${item.profile_pic || '/static/default.jpg'}">
                    <div>
                        <strong>${item.real_name}</strong>
                        <small>${item.mutual} mutual</small>
                    </div>
                    <button onclick="messageUser(${item.id})"><i class="fa fa-message"></i></button>
                    ${type === 'followers' ? '<button onclick="blockUser(${item.id})"><i class="fa fa-ban"></i></button>' : ''}
                    ${type === 'following' || type === 'friends' ? '<button onclick="showDropdown(${item.id})"><i class="fa fa-ellipsis-v"></i></button>' : ''}
                    ${type === 'requests' ? '<button onclick="acceptRequest(${item.id})">Accept</button><button onclick="declineRequest(${item.id})">Decline</button><button onclick="blockUser(${item.id})">Block</button>' : ''}
                    ${type === 'suggested' ? '<button onclick="followUser(${item.id})">Follow</button><button onclick="removeSuggested(${item.id})">Remove</button><button onclick="blockUser(${item.id})">Block</button>' : ''}
                `;
                li.addEventListener('click', () => loadProfile(item.id));
                list.appendChild(li);
            });
        });
    });
    // Load default followers
    tabs[0].click();
}

// Inbox load
async function loadInbox() {
    const tabs = document.querySelectorAll('#inbox-tabs button');
    tabs.forEach(tab => {
        tab.addEventListener('click', async () => {
            const type = tab.id.replace('-tab', '');
            const response = await fetch(`/api/inbox/${type}`);
            const data = await response.json();
            const list = document.getElementById('inbox-list');
            list.innerHTML = '';
            data[type].forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <img src="${item.profile_pic || '/static/default.jpg'}">
                    <div>
                        <strong>${item.real_name || item.name}</strong>
                        <small>${item.last_msg_snippet}</small>
                    </div>
                    <small>${item.last_time}</small>
                    ${item.unread > 0 ? `<span class="unread">${item.unread}</span>` : ''}
                `;
                li.addEventListener('click', () => openChat(item.other_id || item.group_id, type === 'groups'));
                list.appendChild(li);
            });
        });
    });
    // Default chats
    tabs[0].click();
    // New chat button
    document.getElementById('new-chat-btn').addEventListener('click', () => showModal('new-chat-modal'));
    // Search in new chat
    document.getElementById('new-chat-search').addEventListener('input', (e) => {
        // Filter friends/groups client-side or API
    });
    // Create group
    document.getElementById('create-group-btn').addEventListener('click', () => showModal('create-group-modal'));
    document.getElementById('create-group-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const response = await fetch('/api/create_group', { method: 'POST', body: formData });
        if (response.ok) {
            alert('Group created');
            showModal('none');
        }
    });
}

// Open chat modal
async function openChat(id, isGroup) {
    showModal(isGroup ? 'group-chat-modal' : 'chat-modal');
    const response = await fetch(`/api/messages/${isGroup ? 'group' : 'private'}/${id}`);
    const data = await response.json();
    const messagesDiv = document.getElementById(isGroup ? 'group-messages' : 'chat-messages');
    messagesDiv.innerHTML = '';
    data.messages.forEach(m => {
        const msgDiv = document.createElement('div');
        msgDiv.textContent = `${m.sender_name || ''}: ${m.text}`;
        if (m.media_url) {
            const media = m.media_url.endsWith('.mp4') ? document.createElement('video') : document.createElement('img');
            media.src = m.media_url;
            msgDiv.appendChild(media);
        }
        messagesDiv.appendChild(msgDiv);
    });
    // Send message
    const input = document.getElementById(isGroup ? 'group-input' : 'chat-input');
    const sendBtn = document.getElementById(isGroup ? 'group-send' : 'chat-send');
    sendBtn.addEventListener('click', async () => {
        const text = input.value;
        await fetch(`/api/messages/${isGroup ? 'group' : 'private'}/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        input.value = '';
        openChat(id, isGroup); // Reload
    });
    // Other buttons: customize, wallpaper, search, etc. - stub
}

// Load profile
async function loadProfile(userId) {
    const response = await fetch(`/api/profile/${userId}`);
    const data = await response.json();
    showModal('profile-modal');
    document.getElementById('profile-pic').src = data.profile_pic || '/static/default.jpg';
    document.getElementById('profile-name').textContent = data.real_name;
    document.getElementById('profile-key').textContent = data.unique_key || '';
    document.getElementById('profile-stats').innerHTML = `
        Friends: ${data.friends_count} | Followers: ${data.followers_count} | Following: ${data.following_count}
    `;
    if (data.is_own) {
        document.getElementById('profile-actions').innerHTML = `
            <button onclick="editProfile()">Edit</button>
            <button onclick="shareProfile(${userId})">Share</button>
        `;
        // Load tabs: posts, locked, saved, reposts, liked, reels
        loadProfileTab('posts', data.posts);
    } else {
        document.getElementById('profile-actions').innerHTML = `
            <button onclick="followUser(${userId})">Follow</button>
            <button onclick="messageUser(${userId})">Message</button>
        `;
        // Tabs: posts, reels
        loadProfileTab('posts', data.posts);
    }
    document.getElementById('profile-bio').textContent = data.bio;
    // User info, show first 3, more button
    const infoDiv = document.getElementById('profile-info');
    infoDiv.innerHTML = '';
    const info = data.user_info;
    const keys = Object.keys(info).slice(0, 3);
    keys.forEach(k => {
        if (info[k]) infoDiv.innerHTML += `<p>${k}: ${info[k]}</p>`;
    });
    if (Object.keys(info).length > 3) {
        const moreBtn = document.createElement('button');
        moreBtn.textContent = 'Show more';
        moreBtn.addEventListener('click', () => {
            Object.keys(info).slice(3).forEach(k => {
                if (info[k]) infoDiv.innerHTML += `<p>${k}: ${info[k]}</p>`;
            });
            moreBtn.remove();
        });
        infoDiv.appendChild(moreBtn);
    }
}

// Edit profile form
function editProfile() {
    showModal('edit-profile-modal');
    document.getElementById('edit-profile-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const response = await fetch('/api/profile/update', { method: 'POST', body: formData });
        if (response.ok) {
            alert('Updated');
            showModal('none');
            loadProfile(currentUserId);
        }
    });
}

// Load profile tab gallery
function loadProfileTab(tab, ids) {
    const gallery = document.getElementById('profile-gallery');
    gallery.innerHTML = '';
    ids.forEach(id => {
        // Fetch post details if needed, or assume client fetches
        const item = document.createElement('div');
        item.textContent = `Post ${id}`;
        item.addEventListener('click', () => viewPost(id));
        gallery.appendChild(item);
    });
}

// Load search
function loadSearch() {
    const searchInput = document.getElementById('search-bar');
    searchInput.addEventListener('input', async () => {
        const query = searchInput.value;
        const tab = document.querySelector('.tabs button.active').id.replace('-tab', '');
        const response = await fetch(`/api/search?query=${query}&tab=${tab}`);
        const data = await response.json();
        // Display results in #search-results
    });
    // Tabs click to switch
}

// Load add to
function loadAddTo() {
    // Buttons for post, reel, story
    document.getElementById('add-post-btn').addEventListener('click', () => showModal('create-post-modal'));
    // Similar for reel, story
    document.getElementById('create-post-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        formData.append('type', 'post');
        const response = await fetch('/api/create', { method: 'POST', body: formData });
        if (response.ok) {
            alert('Posted');
            showModal('none');
        }
    });
    // Repeat for reel, story
}

// Load notifications
async function loadNotifications() {
    const response = await fetch('/api/notifications');
    const data = await response.json();
    const list = document.getElementById('notifications-list');
    list.innerHTML = '';
    data.notifications.forEach(n => {
        const li = document.createElement('li');
        li.textContent = `${n.message} - ${n.timestamp}`;
        if (!n.is_read) li.style.fontWeight = 'bold';
        li.addEventListener('click', () => markRead(n.id));
        list.appendChild(li);
    });
}

async function markRead(notifId) {
    await fetch(`/api/notification/mark_read/${notifId}`, { method: 'POST' });
    loadNotifications();
}

// Load menu
function loadMenu() {
    // Click handlers for help, settings, logout
    document.getElementById('logout-btn').addEventListener('click', async () => {
        await fetch('/api/logout', { method: 'POST' });
        window.location.reload();
    });
    // Settings form submit to /api/settings
}

// Load admin
async function loadAdmin() {
    const response = await fetch('/api/admin/users');
    const data = await response.json();
    const list = document.getElementById('admin-users');
    list.innerHTML = '';
    data.users.forEach(u => {
        const li = document.createElement('li');
        li.innerHTML = `${u.username} - <button onclick="deleteUser(${u.id})">Delete</button> <button onclick="banUser(${u.id})">Ban</button> <button onclick="warnUser(${u.id})">Warn</button>`;
        list.appendChild(li);
    });
    // Similar for reports, send message, etc.
}

// Interaction functions
async function likePost(postId) {
    await fetch(`/api/like/${postId}`, { method: 'POST' });
    loadSection(currentSection);
}

async function commentPost(postId) {
    const text = prompt('Comment:');
    if (text) {
        await fetch(`/api/comment/${postId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        loadSection(currentSection);
    }
}

async function repost(postId) {
    await fetch(`/api/repost/${postId}`, { method: 'POST' });
}

async function savePost(postId) {
    await fetch(`/api/save/${postId}`, { method: 'POST' });
}

async function reportPost(postId) {
    const desc = prompt('Description:');
    await fetch(`/api/report/${postId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'post', description: desc })
    });
}

async function hidePost(postId) {
    await fetch(`/api/hide/${postId}`, { method: 'POST' });
    // Remove from DOM
}

async function blockUser(userId) {
    await fetch(`/api/block/user/${userId}`, { method: 'POST' });
}

async function followUser(userId) {
    await fetch(`/api/follow/${userId}`, { method: 'POST' });
}

async function acceptRequest(userId) {
    await fetch(`/api/accept_request/${userId}`, { method: 'POST' });
    loadFriends();
}

async function declineRequest(userId) {
    await fetch(`/api/decline_request/${userId}`, { method: 'POST' });
    loadFriends();
}

async function messageUser(userId) {
    openChat(userId, false);
}

// Download reel with watermark (client-side canvas)
function downloadReel(reelId) {
    // Fetch video, add watermark using canvas, download
    alert('Download not implemented fully');
}

// Admin actions
async function deleteUser(userId) {
    await fetch(`/api/admin/delete/user/${userId}`, { method: 'POST' });
    loadAdmin();
}

async function banUser(userId) {
    await fetch(`/api/admin/ban/user/${userId}`, { method: 'POST' });
}

async function warnUser(userId) {
    const msg = prompt('Warning message:');
    await fetch(`/api/admin/warn/user/${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
    });
}

// Etc. for other functions
