// static/script.js (fully adjusted for frontend functionality)

const apiBase = '/api';

function showModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'flex';
}

function hideModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'none';
}

let currentPage = 1;
let loading = false;
let currentView = 'home';
let currentStoryIndex = 0;
let stories = [];
let currentStoryUser = null;
let currentStoryMedia = null;
let storyTimeout = null;
let storyHoldTimeout = null;

const contentDiv = document.getElementById('content');
const observer = new IntersectionObserver(handleIntersection, { threshold: 0 });

document.addEventListener('DOMContentLoaded', () => {
    checkLoggedIn();
    document.getElementById('homeBtn')?.addEventListener('click', () => loadView('home'));
    document.getElementById('reelsBtn')?.addEventListener('click', () => loadView('reels'));
    document.getElementById('friendsBtn')?.addEventListener('click', () => loadView('friends'));
    document.getElementById('inboxBtn')?.addEventListener('click', () => loadView('inbox'));
    document.getElementById('profileBtn')?.addEventListener('click', () => loadView('profile', sessionStorage.getItem('user_id')));
    document.getElementById('searchBtn')?.addEventListener('click', () => loadView('search'));
    document.getElementById('addBtn')?.addEventListener('click', () => showModal('addModal'));
    document.getElementById('notifBtn')?.addEventListener('click', () => loadView('notifications'));
    document.getElementById('menuBtn')?.addEventListener('click', () => loadView('menu'));
    document.getElementById('adminBtn')?.addEventListener('click', () => loadView('admin'));

    document.getElementById('showPostTab')?.addEventListener('click', () => switchAddTab('post'));
    document.getElementById('showReelTab')?.addEventListener('click', () => switchAddTab('reel'));
    document.getElementById('showStoryTab')?.addEventListener('click', () => switchAddTab('story'));

    document.getElementById('postForm')?.addEventListener('submit', (e) => { e.preventDefault(); createPost(); });
    document.getElementById('reelForm')?.addEventListener('submit', (e) => { e.preventDefault(); createReel(); });
    document.getElementById('storyForm')?.addEventListener('submit', (e) => { e.preventDefault(); createStory(); });

    document.getElementById('loginForm')?.addEventListener('submit', (e) => { e.preventDefault(); handleLogin(); });
    document.getElementById('registerForm')?.addEventListener('submit', (e) => { e.preventDefault(); handleRegister(); });
    document.getElementById('showRegister')?.addEventListener('click', (e) => { e.preventDefault(); document.getElementById('loginFormContainer').style.display = 'none'; document.getElementById('registerFormContainer').style.display = 'block'; });
    document.getElementById('showLogin')?.addEventListener('click', (e) => { e.preventDefault(); document.getElementById('registerFormContainer').style.display = 'none'; document.getElementById('loginFormContainer').style.display = 'block'; });

    document.getElementById('profileEditForm')?.addEventListener('submit', (e) => { e.preventDefault(); updateProfile(); });

    document.getElementById('groupCreateForm')?.addEventListener('submit', (e) => { e.preventDefault(); createGroup(); });

    document.getElementById('reportForm')?.addEventListener('submit', (e) => { e.preventDefault(); reportContent(); });
});

function switchAddTab(tab) {
    document.querySelectorAll('.content-tab').forEach(el => el.style.display = 'none');
    document.getElementById(`${tab}Tab`).style.display = 'block';
}

function checkLoggedIn() {
    fetch(`${apiBase}/auth/check_login`, { credentials: 'include' })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                return { is_logged_in: false, is_admin: false };
            }
        })
        .then(data => {
            if (data.is_logged_in) {
                sessionStorage.setItem('user_id', data.user_id);
                if (data.is_admin) {
                    document.getElementById('adminBtn').style.display = 'block';
                }
                loadView(currentView);
            } else {
                showModal('authModal');
            }
        })
        .catch(() => showModal('authModal'));
}

async function loadView(view, targetId = null) {
    currentView = view;
    let html = '';
    contentDiv.innerHTML = '<div class="center">Loading...</div>';
    
    document.querySelectorAll('.nav-button').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`${view}Btn`)?.classList.add('active');

    try {
        switch (view) {
            case 'home':
                await loadStories();
                await loadPosts();
                break;
            case 'reels':
                await loadReels();
                break;
            case 'friends':
                await loadFriendsView();
                break;
            case 'inbox':
                await loadInbox();
                break;
            case 'profile':
                await loadProfile(targetId);
                break;
            case 'search':
                html = `
                    <div class="search-container">
                        <input type="text" id="searchInput" placeholder="Search users or posts...">
                        <button id="searchExecuteBtn">Search</button>
                    </div>
                    <div id="searchResults"></div>
                `;
                contentDiv.innerHTML = html;
                document.getElementById('searchExecuteBtn')?.addEventListener('click', () => executeSearch());
                break;
            case 'notifications':
                await loadNotifications();
                break;
            case 'admin':
                await loadAdminDashboard();
                break;
            case 'menu':
                await loadMenu();
                break;
        }
    } catch (error) {
        console.error('Error loading view:', error);
        contentDiv.innerHTML = `<div class="center">Error loading content. Please try again later.</div>`;
    }
}

// --- Dynamic View Loading Functions ---

async function loadStories() {
    const response = await fetch(`${apiBase}/stories/feed`, { credentials: 'include' });
    if (!response.ok) throw new Error('Failed to fetch stories');
    stories = await response.json();
    let storiesHtml = '<div class="stories-container">';
    if (stories.length === 0) {
        storiesHtml += `<p class="center">No stories to show. Add some friends or create your own!</p>`;
    } else {
        stories.forEach(userStory => {
            const isRead = sessionStorage.getItem(`stories_read_${userStory.username}`) === 'true';
            storiesHtml += `
                <div class="story-item ${isRead ? 'read' : 'unread'}" onclick="showStoryModal('${userStory.username}')">
                    <img src="${userStory.profile_pic_url || '/static/default-profile.png'}" alt="${userStory.username}" class="story-circle">
                    <span class="story-username">${userStory.username}</span>
                </div>
            `;
        });
    }
    storiesHtml += '</div>';
    contentDiv.innerHTML = storiesHtml + contentDiv.innerHTML;
}

async function loadPosts() {
    currentPage = 1;
    loading = false;
    const postsDiv = document.createElement('div');
    postsDiv.id = 'postsContainer';
    contentDiv.appendChild(postsDiv);
    await fetchPosts();
    // Enable infinite scrolling
    observer.observe(document.querySelector('.post-card:last-child') || document.body);
}

async function fetchPosts() {
    if (loading) return;
    loading = true;
    const response = await fetch(`${apiBase}/posts/feed?page=${currentPage}`, { credentials: 'include' });
    const newPosts = await response.json();
    if (newPosts.length > 0) {
        const postsContainer = document.getElementById('postsContainer');
        newPosts.forEach(post => {
            postsContainer.appendChild(renderPost(post));
        });
        currentPage++;
        loading = false;
        // Re-observe the new last element
        observer.observe(document.querySelector('.post-card:last-child'));
    } else {
        loading = false;
        observer.unobserve(document.body);
        const postsContainer = document.getElementById('postsContainer');
        if (!postsContainer.innerHTML.includes('End of feed')) {
            postsContainer.innerHTML += '<div class="center">End of feed.</div>';
        }
    }
}

async function loadReels() {
    currentPage = 1;
    loading = false;
    contentDiv.innerHTML = '<div id="reelsContainer"></div>';
    await fetchReels();
    observer.observe(document.querySelector('.reel-card:last-child') || document.body);
}

async function fetchReels() {
    if (loading) return;
    loading = true;
    const response = await fetch(`${apiBase}/reels/feed?page=${currentPage}`, { credentials: 'include' });
    const newReels = await response.json();
    if (newReels.length > 0) {
        const reelsContainer = document.getElementById('reelsContainer');
        newReels.forEach(reel => {
            reelsContainer.appendChild(renderReel(reel));
        });
        currentPage++;
        loading = false;
        observer.observe(document.querySelector('.reel-card:last-child'));
    } else {
        loading = false;
        observer.unobserve(document.body);
        const reelsContainer = document.getElementById('reelsContainer');
        if (!reelsContainer.innerHTML.includes('End of reels')) {
            reelsContainer.innerHTML += '<div class="center">End of reels.</div>';
        }
    }
}

async function loadFriendsView() {
    const requestsResponse = await fetch(`${apiBase}/friends/requests`, { credentials: 'include' });
    const requests = await requestsResponse.json();
    const friendsResponse = await fetch(`${apiBase}/friends`, { credentials: 'include' });
    const friends = await friendsResponse.json();
    
    let html = `<h2>Friend Requests</h2>`;
    if (requests.length > 0) {
        requests.forEach(req => {
            html += `
                <div class="list-item">
                    <img src="${req.profile_pic_url || '/static/default-profile.png'}" class="profile-pic">
                    <span>${req.real_name} (@${req.username})</span>
                    <button onclick="acceptFriendRequest('${req.id}')">Accept</button>
                    <button onclick="rejectFriendRequest('${req.id}')">Reject</button>
                </div>
            `;
        });
    } else {
        html += `<p class="center">No new friend requests.</p>`;
    }

    html += `<h2>My Friends</h2>`;
    if (friends.length > 0) {
        friends.forEach(friend => {
            html += `
                <div class="list-item" onclick="loadView('profile', '${friend.id}')">
                    <img src="${friend.profile_pic_url || '/static/default-profile.png'}" class="profile-pic">
                    <span>${friend.real_name} (@${friend.username})</span>
                    <button class="unfriend-button" onclick="event.stopPropagation(); unfriendUser('${friend.id}')">Unfriend</button>
                </div>
            `;
        });
    } else {
        html += `<p class="center">You have no friends yet. Use search to find some!</p>`;
    }
    contentDiv.innerHTML = html;
}

async function loadInbox() {
    const response = await fetch(`${apiBase}/inbox/chats`, { credentials: 'include' });
    const chats = await response.json();
    let html = `
        <h2>Inbox</h2>
        <div class="inbox-controls">
            <button onclick="showModal('groupCreateModal')">Create Group</button>
        </div>
    `;
    if (chats.length > 0) {
        chats.forEach(chat => {
            html += `
                <div class="list-item" onclick="showChatModal('${chat.id}', ${chat.is_group || false})">
                    <img src="${chat.profile_pic_url || '/static/default-profile.png'}" class="profile-pic">
                    <div class="chat-info">
                        <span>${chat.name || chat.real_name}</span>
                        <small>${chat.last_message}</small>
                    </div>
                    ${chat.unread > 0 ? `<span class="unread-count">${chat.unread}</span>` : ''}
                </div>
            `;
        });
    } else {
        html += `<p class="center">No chats yet. Message a friend!</p>`;
    }
    contentDiv.innerHTML = html;
}

async function loadProfile(userId) {
    const response = await fetch(`${apiBase}/user/profile/${userId}`, { credentials: 'include' });
    const user = await response.json();
    let isMyProfile = sessionStorage.getItem('user_id') === userId;

    let html = `
        <div class="profile-header">
            <img src="${user.profile_pic_url || '/static/default-profile.png'}" alt="${user.username}" class="profile-pic">
            <h2>${user.real_name} (@${user.username})</h2>
            <p>${user.bio || 'No bio yet.'}</p>
            <div class="profile-actions">
                ${isMyProfile ? `<button onclick="showModal('profileEditModal')">Edit Profile</button>` :
                    user.is_friend ? `<button class="unfriend-button" onclick="unfriendUser('${userId}')">Unfriend</button>` :
                    user.is_pending ? `<button disabled>Request Sent</button>` :
                    `<button class="follow-button" onclick="sendFriendRequest('${userId}')">Add Friend</button>`
                }
                ${!isMyProfile ? `<button onclick="messageUser('${userId}')">Message</button>` : ''}
                ${!isMyProfile ? `<button class="report-button" onclick="showReportModal('${userId}', 'user')">Report</button>` : ''}
            </div>
        </div>
        <h3>Posts</h3>
        <div class="posts-list" id="userPosts"></div>
        <h3>Reels</h3>
        <div class="reels-list" id="userReels"></div>
    `;
    contentDiv.innerHTML = html;
    user.posts.forEach(post => document.getElementById('userPosts').appendChild(renderPost(post)));
    user.reels.forEach(reel => document.getElementById('userReels').appendChild(renderReel(reel)));
}

async function executeSearch() {
    const query = document.getElementById('searchInput').value;
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '<div class="center">Searching...</div>';
    
    const response = await fetch(`${apiBase}/search?q=${query}`, { credentials: 'include' });
    const results = await response.json();
    let html = '';
    
    html += `<h3>Users</h3>`;
    if (results.users.length > 0) {
        results.users.forEach(user => {
            html += `
                <div class="list-item" onclick="loadView('profile', '${user.id}')">
                    <img src="${user.profile_pic_url || '/static/default-profile.png'}" class="profile-pic">
                    <span>${user.real_name} (@${user.username})</span>
                </div>
            `;
        });
    } else {
        html += `<p class="center">No users found.</p>`;
    }

    html += `<h3>Posts</h3>`;
    if (results.posts.length > 0) {
        results.posts.forEach(post => {
            html += `<div class="post-card">${post.content}</div>`;
        });
    } else {
        html += `<p class="center">No posts found.</p>`;
    }

    resultsDiv.innerHTML = html;
}

async function loadNotifications() {
    const response = await fetch(`${apiBase}/notifications`, { credentials: 'include' });
    const notifications = await response.json();
    let html = `<h2>Notifications</h2>`;
    if (notifications.length > 0) {
        notifications.forEach(notif => {
            html += `<div class="list-item">${notif.text}</div>`;
        });
    } else {
        html += `<p class="center">No new notifications.</p>`;
    }
    contentDiv.innerHTML = html;
}

async function loadAdminDashboard() {
    const postsResponse = await fetch(`${apiBase}/admin/reports/posts`, { credentials: 'include' });
    const reportedPosts = await postsResponse.json();
    const usersResponse = await fetch(`${apiBase}/admin/reports/users`, { credentials: 'include' });
    const reportedUsers = await usersResponse.json();

    let html = `
        <h2>Admin Dashboard</h2>
        <h3>Reported Posts</h3>
        <div id="reportedPosts"></div>
        <h3>Reported Users</h3>
        <div id="reportedUsers"></div>
        <h3>Send System Message</h3>
        <div class="list-item">
            <select id="systemMsgTarget">
                <option value="all">All Users</option>
                <!-- Add options for specific users later if needed -->
            </select>
            <textarea id="systemMsgText" placeholder="Message content"></textarea>
            <button onclick="sendSystemMessage()">Send</button>
        </div>
    `;
    contentDiv.innerHTML = html;

    reportedPosts.forEach(post => {
        const postDiv = document.createElement('div');
        postDiv.className = 'list-item';
        postDiv.innerHTML = `
            <span>Post by @${post.username}: ${post.content}</span>
            <small>Reason: ${post.reason}</small>
            <button onclick="adminDeletePost('${post.target_id}')">Delete Post</button>
        `;
        document.getElementById('reportedPosts').appendChild(postDiv);
    });

    reportedUsers.forEach(user => {
        const userDiv = document.createElement('div');
        userDiv.className = 'list-item';
        userDiv.innerHTML = `
            <span>User: @${user.username}</span>
            <small>Reason: ${user.reason}</small>
            <button onclick="adminBanUser('${user.target_id}')">Ban User</button>
        `;
        document.getElementById('reportedUsers').appendChild(userDiv);
    });
}

function loadMenu() {
    let html = `
        <h2>Menu</h2>
        <div class="menu-item" onclick="toggleDarkMode()">Toggle Dark Mode</div>
        <div class="menu-item" onclick="handleLogout()">Logout</div>
    `;
    contentDiv.innerHTML = html;
}

// --- Interaction Functions ---

function handleLogin() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    fetch(`${apiBase}/auth/login`, {
        method: 'POST',
        body: JSON.stringify({ username, password }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(response => response.json()).then(data => {
        if (data.message) {
            sessionStorage.setItem('user_id', data.user_id);
            if (data.is_admin) {
                document.getElementById('adminBtn').style.display = 'block';
            }
            hideModal('authModal');
            loadView('home');
        } else {
            console.error(data.error);
        }
    });
}

function handleRegister() {
    const username = document.getElementById('registerUsername').value;
    const real_name = document.getElementById('registerRealName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    fetch(`${apiBase}/auth/register`, {
        method: 'POST',
        body: JSON.stringify({ username, real_name, email, password }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(response => response.json()).then(data => {
        if (data.message) {
            console.log(data.message);
            document.getElementById('registerFormContainer').style.display = 'none';
            document.getElementById('loginFormContainer').style.display = 'block';
        } else {
            console.error(data.error);
        }
    });
}

function handleLogout() {
    fetch(`${apiBase}/auth/logout`, { credentials: 'include' })
        .then(() => {
            sessionStorage.removeItem('user_id');
            window.location.reload();
        });
}

async function createPost() {
    const form = document.getElementById('postForm');
    const formData = new FormData(form);
    await fetch(`${apiBase}/posts/create`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    });
    hideModal('addModal');
    loadView('home');
}

async function createReel() {
    const form = document.getElementById('reelForm');
    const formData = new FormData(form);
    await fetch(`${apiBase}/reels/create`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    });
    hideModal('addModal');
    loadView('reels');
}

async function createStory() {
    const form = document.getElementById('storyForm');
    const formData = new FormData(form);
    await fetch(`${apiBase}/stories/create`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    });
    hideModal('addModal');
    loadView('home');
}

function likePost(postId) {
    fetch(`${apiBase}/posts/like/${postId}`, {
        method: 'POST',
        credentials: 'include'
    }).then(() => {
        // Simple UI update. Full refresh can be used too.
        const likeCountSpan = document.querySelector(`#post-${postId} .like-count`);
        const likeBtn = document.querySelector(`#post-${postId} .like-button`);
        const isLiked = likeBtn.classList.toggle('liked');
        const currentLikes = parseInt(likeCountSpan.textContent);
        likeCountSpan.textContent = isLiked ? currentLikes + 1 : currentLikes - 1;
    });
}

function toggleComments(postId) {
    const commentsDiv = document.querySelector(`#post-${postId} .comments-container`);
    if (commentsDiv.classList.contains('hidden')) {
        fetchComments(postId);
    }
    commentsDiv.classList.toggle('hidden');
}

async function fetchComments(postId) {
    const commentsDiv = document.querySelector(`#post-${postId} .comments-container`);
    const response = await fetch(`${apiBase}/posts/comments/${postId}`, { credentials: 'include' });
    const comments = await response.json();
    let commentsHtml = '';
    comments.forEach(comment => {
        commentsHtml += `
            <div class="comment-item">
                <img src="${comment.profile_pic_url || '/static/default-profile.png'}" class="profile-pic" style="width: 30px; height: 30px;">
                <strong>@${comment.username}</strong>: ${comment.text}
            </div>
        `;
    });
    commentsHtml += `
        <form class="comment-form" onsubmit="event.preventDefault(); postComment('${postId}')">
            <input type="text" placeholder="Add a comment..." required>
            <button type="submit">Send</button>
        </form>
    `;
    commentsDiv.innerHTML = commentsHtml;
}

function postComment(postId) {
    const form = document.querySelector(`#post-${postId} .comment-form`);
    const input = form.querySelector('input');
    const text = input.value;
    fetch(`${apiBase}/posts/comment/${postId}`, {
        method: 'POST',
        body: JSON.stringify({ text }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => {
        input.value = '';
        fetchComments(postId);
    });
}

function sendFriendRequest(targetId) {
    fetch(`${apiBase}/friends/add/${targetId}`, {
        method: 'POST',
        credentials: 'include'
    }).then(() => {
        console.log('Friend request sent');
        loadView('profile', targetId);
    });
}

function unfriendUser(targetId) {
    // This is a simplified unfriend. A real app would need to find the specific friend id.
    fetch(`${apiBase}/friends/unfriend/${targetId}`, {
        method: 'POST',
        credentials: 'include'
    }).then(() => {
        console.log('Unfriended');
        loadView('profile', targetId);
    });
}

function acceptFriendRequest(requestId) {
    fetch(`${apiBase}/friends/accept/${requestId}`, {
        method: 'POST',
        credentials: 'include'
    }).then(() => {
        loadView('friends');
    });
}

function rejectFriendRequest(requestId) {
    fetch(`${apiBase}/friends/reject/${requestId}`, {
        method: 'POST',
        credentials: 'include'
    }).then(() => {
        loadView('friends');
    });
}

function messageUser(id) {
    showChatModal(id, false);
}

function showChatModal(targetId, isGroup) {
    const modal = document.getElementById('chatModal');
    const chatHeader = document.getElementById('chatHeader');
    const chatName = document.getElementById('chatName');
    const chatProfilePic = document.getElementById('chatProfilePic');
    const chatActions = document.getElementById('chatActions');
    const chatForm = document.getElementById('chatForm');

    chatForm.onsubmit = (e) => {
        e.preventDefault();
        sendMessage(targetId, isGroup);
    };

    chatActions.innerHTML = '';
    
    if (isGroup) {
        chatHeader.innerHTML = '<h3>Group Chat</h3>';
        chatActions.innerHTML = `
            <button onclick="leaveGroup('${targetId}')">Leave Group</button>
        `;
        // In a real app, you'd fetch group details
        chatName.textContent = "Group Chat";
        chatProfilePic.src = "/static/default-group.png";
    } else {
        fetch(`${apiBase}/user/profile/${targetId}`, { credentials: 'include' }).then(res => res.json()).then(user => {
            chatName.textContent = user.real_name;
            chatProfilePic.src = user.profile_pic_url || '/static/default-profile.png';
            chatActions.innerHTML = `<button onclick="loadView('profile', '${targetId}')">View Profile</button>`;
        });
    }

    fetchMessages(targetId);
    showModal('chatModal');
}

function fetchMessages(targetId) {
    const messagesDiv = document.getElementById('chatMessages');
    messagesDiv.innerHTML = '<div class="center">Loading messages...</div>';
    fetch(`${apiBase}/inbox/messages/${targetId}`, { credentials: 'include' }).then(res => res.json()).then(messages => {
        messagesDiv.innerHTML = '';
        messages.forEach(msg => {
            const isSent = msg.sender_id === sessionStorage.getItem('user_id');
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${isSent ? 'sent-message' : 'received-message'}`;
            msgDiv.textContent = msg.text;
            messagesDiv.appendChild(msgDiv);
        });
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    });
}

function sendMessage(targetId, isGroup) {
    const input = document.getElementById('chatInput');
    const text = input.value;
    if (!text) return;

    fetch(`${apiBase}/inbox/send`, {
        method: 'POST',
        body: JSON.stringify({ receiver_id: targetId, text, is_group: isGroup }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => {
        input.value = '';
        fetchMessages(targetId);
    });
}

function createGroup() {
    const name = document.getElementById('groupName').value;
    const description = document.getElementById('groupDescription').value;
    fetch(`${apiBase}/group/create`, {
        method: 'POST',
        body: JSON.stringify({ name, description }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => {
        hideModal('groupCreateModal');
        loadView('inbox');
    });
}

function leaveGroup(groupId) {
    fetch(`${apiBase}/group/leave/${groupId}`, {
        method: 'POST',
        credentials: 'include'
    }).then(() => {
        hideModal('chatModal');
        loadView('inbox');
    });
}

function updateProfile() {
    const form = document.getElementById('profileEditForm');
    const formData = new FormData(form);
    fetch(`${apiBase}/user/profile`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    }).then(() => {
        hideModal('profileEditModal');
        loadView('profile', sessionStorage.getItem('user_id'));
    });
}

function showReportModal(targetId, targetType) {
    const form = document.getElementById('reportForm');
    form.dataset.targetId = targetId;
    form.dataset.targetType = targetType;
    showModal('reportModal');
}

function reportContent() {
    const form = document.getElementById('reportForm');
    const target_id = form.dataset.targetId;
    const target_type = form.dataset.targetType;
    const reason = document.getElementById('reportReason').value;

    fetch(`${apiBase}/report`, {
        method: 'POST',
        body: JSON.stringify({ target_id, target_type, reason }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => {
        hideModal('reportModal');
        document.getElementById('reportReason').value = '';
    });
}

function adminDeletePost(postId) {
    fetch(`${apiBase}/admin/delete_post/${postId}`, {
        method: 'POST',
        credentials: 'include'
    }).then(() => {
        loadView('admin');
    });
}

function adminBanUser(userId) {
    fetch(`${apiBase}/admin/ban_user/${userId}`, {
        method: 'POST',
        credentials: 'include'
    }).then(() => {
        loadView('admin');
    });
}

function sendSystemMessage() {
    const target_id = document.getElementById('systemMsgTarget').value;
    const message = document.getElementById('systemMsgText').value;
    fetch(`${apiBase}/admin/send_system`, {
        method: 'POST',
        body: JSON.stringify({ target_id, message }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => {
        document.getElementById('systemMsgText').value = '';
    });
}

// --- UI Rendering Helpers ---

function renderPost(post) {
    const postCard = document.createElement('div');
    postCard.className = 'post-card';
    postCard.id = `post-${post.id}`;
    const mediaHtml = post.media_url ? `<img src="${post.media_url}" class="post-media">` : '';
    const likedClass = post.is_liked ? 'liked' : '';

    postCard.innerHTML = `
        <div class="user-info">
            <img src="${post.profile_pic_url || '/static/default-profile.png'}" class="profile-pic" onclick="loadView('profile', '${post.user_id}')">
            <div class="user-info-text">
                <span class="username">${post.real_name}</span>
                <small>@${post.username}</small>
                <small>${new Date(post.timestamp).toLocaleDateString()}</small>
            </div>
        </div>
        <p>${post.content}</p>
        ${mediaHtml}
        <div class="post-stats">
            <span><span class="like-count">${post.like_count}</span> likes</span>
            <span><span class="comment-count">${post.comment_count}</span> comments</span>
        </div>
        <div class="post-actions">
            <button class="like-button ${likedClass}" onclick="likePost('${post.id}')"><i class="fa fa-heart"></i> Like</button>
            <button class="comment-button" onclick="toggleComments('${post.id}')"><i class="fa fa-comment"></i> Comment</button>
            <button class="share-button"><i class="fa fa-share"></i> Share</button>
        </div>
        <div class="comments-container hidden"></div>
    `;
    return postCard;
}

function renderReel(reel) {
    const reelCard = document.createElement('div');
    reelCard.className = 'reel-card';
    const likedClass = reel.is_liked ? 'liked' : '';
    reelCard.innerHTML = `
        <video src="${reel.media_url}" class="reel-media" controls></video>
        <div class="user-info">
            <img src="${reel.profile_pic_url || '/static/default-profile.png'}" class="profile-pic">
            <div class="user-info-text">
                <span class="username">${reel.real_name}</span>
                <small>@${reel.username}</small>
            </div>
        </div>
        <p>${reel.content}</p>
        <div class="post-actions">
            <button class="like-button ${likedClass}" onclick="likePost('${reel.id}')"><i class="fa fa-heart"></i> ${reel.like_count}</button>
            <button class="comment-button" onclick="toggleComments('${reel.id}')"><i class="fa fa-comment"></i> ${reel.comment_count}</button>
            <button class="share-button"><i class="fa fa-share"></i></button>
        </div>
    `;
    return reelCard;
}

function handleIntersection(entries, observer) {
    entries.forEach(entry => {
        if (entry.isIntersecting && !loading) {
            if (currentView === 'home') {
                fetchPosts();
            } else if (currentView === 'reels') {
                fetchReels();
            }
        }
    });
}

function showStoryModal(username) {
    currentStoryUser = stories.find(s => s.username === username);
    if (!currentStoryUser) return;
    currentStoryIndex = 0;
    const modal = document.getElementById('storyViewModal');
    const container = document.getElementById('storyViewContainer');
    
    // Set stories as read for this user
    sessionStorage.setItem(`stories_read_${username}`, 'true');
    document.querySelector(`.story-item:has(img[alt="${username}"])`).classList.remove('unread');
    document.querySelector(`.story-item:has(img[alt="${username}"])`).classList.add('read');

    const renderStory = () => {
        if (storyTimeout) clearTimeout(storyTimeout);
        const story = currentStoryUser.stories[currentStoryIndex];
        const mediaTag = story.media_url.endsWith('.mp4') ? `<video src="${story.media_url}" controls autoplay></video>` : `<img src="${story.media_url}">`;
        container.innerHTML = `
            <div class="story-user-info">
                <img src="${currentStoryUser.profile_pic_url || '/static/default-profile.png'}" class="profile-pic">
                <span>${currentStoryUser.username}</span>
            </div>
            ${mediaTag}
        `;
        currentStoryMedia = container.querySelector('video') || container.querySelector('img');

        // Autoplay and set timeout for next story
        if (currentStoryMedia.tagName === 'VIDEO') {
            currentStoryMedia.play();
            currentStoryMedia.onended = nextStory;
        } else {
            storyTimeout = setTimeout(nextStory, 5000); // 5 seconds for images
        }
    };

    const nextStory = () => {
        currentStoryIndex++;
        if (currentStoryIndex < currentStoryUser.stories.length) {
            renderStory();
        } else {
            hideModal('storyViewModal');
        }
    };

    const prevStory = () => {
        currentStoryIndex = Math.max(0, currentStoryIndex - 1);
        renderStory();
    };

    // Touch and mouse events for navigation
    let startX = 0;
    let isHolding = false;
    modal.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
        isHolding = true;
        storyHoldTimeout = setTimeout(() => {
            if (currentStoryMedia && currentStoryMedia.tagName === 'VIDEO') {
                currentStoryMedia.pause();
            } else if (storyTimeout) {
                clearTimeout(storyTimeout);
            }
        }, 300); // 300ms for a "hold"
    });
    modal.addEventListener('touchend', (e) => {
        isHolding = false;
        if (storyHoldTimeout) clearTimeout(storyHoldTimeout);
        if (currentStoryMedia && currentStoryMedia.tagName === 'VIDEO') {
            currentStoryMedia.play();
        } else {
            storyTimeout = setTimeout(nextStory, 5000);
        }
        const endX = e.changedTouches[0].clientX;
        if (Math.abs(endX - startX) > 50) {
            if (endX < startX) {
                nextStory();
            } else {
                prevStory();
            }
        }
    });

    modal.addEventListener('mousedown', (e) => {
        isHolding = true;
        storyHoldTimeout = setTimeout(() => {
            if (currentStoryMedia && currentStoryMedia.tagName === 'VIDEO') {
                currentStoryMedia.pause();
            } else if (storyTimeout) {
                clearTimeout(storyTimeout);
            }
        }, 300);
    });
    modal.addEventListener('mouseup', () => {
        if (storyHoldTimeout) clearTimeout(storyHoldTimeout);
        if (isHolding) {
            if (currentStoryMedia && currentStoryMedia.tagName === 'VIDEO') {
                currentStoryMedia.play();
            } else {
                storyTimeout = setTimeout(nextStory, 5000);
            }
            isHolding = false;
        }
    });

    renderStory();
    showModal('storyViewModal');
}

function toggleDarkMode() {
    document.body.classList.toggle('dark');
}
