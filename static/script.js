// static/script.js (Updated)

const apiBase = '/api';

function showModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'block';
}

function hideModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'none';
}

let currentPage = 1;
let loading = false;
let currentView = 'home';
let currentSearchType = 'all';

document.addEventListener('DOMContentLoaded', () => {
    checkLoggedIn();
    document.getElementById('homeBtn')?.addEventListener('click', () => loadView('home'));
    document.getElementById('reelsBtn')?.addEventListener('click', () => loadView('reels'));
    document.getElementById('friendsBtn')?.addEventListener('click', () => loadView('friends'));
    document.getElementById('inboxBtn')?.addEventListener('click', () => loadView('inbox'));
    document.getElementById('profileBtn')?.addEventListener('click', () => loadView('profile'));
    document.getElementById('searchBtn')?.addEventListener('click', () => loadView('search'));
    document.getElementById('addBtn')?.addEventListener('click', () => showModal('addModal'));
    document.getElementById('notifBtn')?.addEventListener('click', () => loadView('notifications'));
    document.getElementById('menuBtn')?.addEventListener('click', () => loadView('menu'));
    document.getElementById('adminBtn')?.addEventListener('click', () => loadView('admin'));
    window.addEventListener('scroll', handleInfiniteScroll);
});

function checkLoggedIn() {
    fetch(`${apiBase}/user/me`, {
        credentials: 'include'
    })
    .then(res => {
        if (res.status === 401) {
            showModal('loginModal');
        } else {
            res.json().then(user => {
                sessionStorage.setItem('user_id', user.id);
                if (user.is_admin) {
                    document.getElementById('adminBtn').style.display = 'block';
                }
                loadView('home');
            });
        }
    })
    .catch(err => {
        console.error('Error checking login:', err);
        showModal('loginModal');
    });
}

function loadView(view, userId) {
    currentView = view;
    currentPage = 1;
    const content = document.getElementById('content');
    content.innerHTML = '<p>Loading...</p>';
    if (view === 'home') {
        loadHome();
    } else if (view === 'reels') {
        loadReels();
    } else if (view === 'friends') {
        loadFriends();
    } else if (view === 'inbox') {
        loadInbox();
    } else if (view === 'profile') {
        loadProfile(userId || sessionStorage.getItem('user_id'));
    } else if (view === 'search') {
        loadSearch();
    } else if (view === 'notifications') {
        loadNotifications();
    } else if (view === 'menu') {
        loadMenu();
    } else if (view === 'admin') {
        loadAdmin();
    }
}

function handleInfiniteScroll() {
    if (loading || (window.innerHeight + window.scrollY < document.body.offsetHeight - 100)) return;
    loading = true;
    currentPage++;
    if (currentView === 'home') {
        fetch(`${apiBase}/posts/feed?page=${currentPage}`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            if (data.length > 0) {
                renderPosts(data, false);
            }
            loading = false;
        })
        .catch(err => {
            console.error('Error loading more posts:', err);
            loading = false;
        });
    } else if (currentView === 'reels') {
        fetch(`${apiBase}/reels/feed?page=${currentPage}`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            if (data.length > 0) {
                renderReels(data, false);
            }
            loading = false;
        })
        .catch(err => {
            console.error('Error loading more reels:', err);
            loading = false;
        });
    }
}

// User Authentication
function register() {
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;
    fetch(`${apiBase}/register`, {
        method: 'POST',
        body: JSON.stringify({ username, password }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message);
            hideModal('registerModal');
            hideModal('loginModal');
            checkLoggedIn();
        }
    });
}

function login() {
    const identifier = document.getElementById('loginIdentifier').value;
    const password = document.getElementById('loginPassword').value;
    fetch(`${apiBase}/login`, {
        method: 'POST',
        body: JSON.stringify({ identifier, password }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message);
            hideModal('loginModal');
            checkLoggedIn();
        }
    });
}

function verifyKey() {
    const username = document.getElementById('forgotUsername').value;
    const unique_key = document.getElementById('forgotUniqueKey').value;
    fetch(`${apiBase}/forgot`, {
        method: 'POST',
        body: JSON.stringify({ username, unique_key }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            hideModal('forgotModal');
            showModal('resetModal');
        }
    });
}

function resetPassword() {
    const password = document.getElementById('resetPassword').value;
    fetch(`${apiBase}/reset_password`, {
        method: 'POST',
        body: JSON.stringify({ password }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message);
            hideModal('resetModal');
            showModal('loginModal');
        }
    });
}

// Content and Views
function loadHome() {
    const content = document.getElementById('content');
    content.innerHTML = '';
    
    // Stories
    fetch(`${apiBase}/stories`, { credentials: 'include' })
    .then(res => res.json())
    .then(stories => {
        const storiesDiv = document.createElement('div');
        storiesDiv.classList.add('stories');
        stories.forEach(story => {
            const circle = document.createElement('div');
            circle.classList.add('story-circle');
            circle.style.backgroundImage = `url(${story.media_url || '/static/default.jpg'})`;
            circle.onclick = () => showStory(story.id);
            const username = document.createElement('p');
            username.textContent = story.username;
            circle.appendChild(username);
            storiesDiv.appendChild(circle);
        });
        content.appendChild(storiesDiv);
    })
    .catch(err => console.error('Error loading stories:', err));

    // Posts
    fetch(`${apiBase}/posts/feed?page=1`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => renderPosts(data))
    .catch(err => console.error('Error loading posts:', err));
}

function renderPosts(posts, clear = true) {
    const content = document.getElementById('content');
    if (clear) content.innerHTML += '<h3>Posts</h3>';
    
    posts.forEach(post => {
        const postDiv = document.createElement('div');
        postDiv.classList.add('post');
        postDiv.innerHTML = `
            <div class="post-header">
                <img src="${post.profile_pic_url || '/static/default.jpg'}" class="small-circle" onclick="loadView('profile', ${post.user_id})">
                <div class="user-info">
                    <span class="user-real-name" onclick="loadView('profile', ${post.user_id})">${post.real_name}</span>
                    <span class="user-username">@${post.username}</span>
                    <span class="post-date">${post.timestamp}</span>
                </div>
            </div>
            <div class="post-body">
                <p>${post.description}</p>
                ${post.media_url ? `<img src="${post.media_url}" alt="Post media">` : ''}
            </div>
            <div class="post-actions">
                <span class="like-btn ${post.is_liked ? 'liked' : ''}" onclick="toggleLike(${post.id}, this)"><i class="fa fa-heart"></i> ${post.likes_count}</span>
                <span onclick="toggleComments(${post.id})"><i class="fa fa-comment"></i> ${post.comments_count}</span>
                <span onclick="repostPost(${post.id})"><i class="fa fa-retweet"></i> ${post.reposts_count}</span>
                <span onclick="savePost(${post.id})"><i class="fa fa-bookmark"></i></span>
                <span class="post-views">${post.views} views</span>
                <div class="dropdown">
                    <button class="dropbtn"><i class="fa fa-ellipsis-h"></i></button>
                    <div class="dropdown-content">
                        <a href="#" onclick="reportPost(${post.id}, 'post')">Report Post</a>
                        <a href="#" onclick="hidePost(${post.id})">Hide Post</a>
                        <a href="#" onclick="toggleNotifications(${post.id})">Turn on notifications</a>
                        <a href="#" onclick="blockUser(${post.user_id})">Block Profile</a>
                        <a href="#" onclick="followUser(${post.user_id})">Follow</a>
                    </div>
                </div>
            </div>
            <div id="comments-${post.id}" class="comments-section"></div>
        `;
        content.appendChild(postDiv);
    });
}

function loadReels() {
    const content = document.getElementById('content');
    content.innerHTML = '<div id="reels-container"></div>';
    fetch(`${apiBase}/reels/feed?page=1`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => renderReels(data))
    .catch(err => console.error('Error loading reels:', err));
}

function renderReels(reels, clear = true) {
    const container = document.getElementById('reels-container');
    if (clear) container.innerHTML = '';
    reels.forEach(reel => {
        const reelDiv = document.createElement('div');
        reelDiv.classList.add('reel');
        reelDiv.innerHTML = `
            <video class="reel-video" src="${reel.media_url}" controls muted loop></video>
            <div class="reel-overlay">
                <div class="reel-user-info">
                    <img src="${reel.profile_pic_url || '/static/default.jpg'}" class="small-circle" onclick="loadView('profile', ${reel.user_id})">
                    <span class="user-real-name" onclick="loadView('profile', ${reel.user_id})">${reel.real_name}</span>
                    <span class="user-username">@${reel.username}</span>
                </div>
                <p class="reel-description">${reel.description}</p>
                <div class="reel-actions">
                    <span class="like-btn ${reel.is_liked ? 'liked' : ''}" onclick="toggleLike(${reel.id}, this)"><i class="fa fa-heart"></i> ${reel.likes_count}</span>
                    <span onclick="toggleComments(${reel.id})"><i class="fa fa-comment"></i> ${reel.comments_count}</span>
                    <span onclick="repostPost(${reel.id})"><i class="fa fa-retweet"></i> ${reel.reposts_count}</span>
                    <span onclick="savePost(${reel.id})"><i class="fa fa-bookmark"></i></span>
                    <a href="${reel.media_url}" download><i class="fa fa-download"></i></a>
                </div>
            </div>
        `;
        container.appendChild(reelDiv);
    });
}

function createPost() {
    const type = document.getElementById('addType').value;
    const mediaFile = document.getElementById('addMedia').files[0];
    const description = document.getElementById('addDescription').value;
    const privacy = document.getElementById('addPrivacy').value;
    
    const formData = new FormData();
    formData.append('file', mediaFile);
    
    fetch(`${apiBase}/upload`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        const media_url = data.url;
        
        fetch(`${apiBase}/post/create`, {
            method: 'POST',
            body: JSON.stringify({ type, description, media_url, privacy }),
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        })
        .then(res => res.json())
        .then(postData => {
            if (postData.error) {
                alert(postData.error);
            } else {
                alert(postData.message);
                hideModal('addModal');
                loadView('home');
            }
        });
    });
}

function toggleLike(postId, element) {
    const isLiked = element.classList.contains('liked');
    const url = isLiked ? `${apiBase}/post/${postId}/unlike` : `${apiBase}/post/${postId}/like`;
    const newCount = isLiked ? parseInt(element.textContent) - 1 : parseInt(element.textContent) + 1;
    
    fetch(url, { method: 'POST', credentials: 'include' })
    .then(res => {
        if (res.ok) {
            element.classList.toggle('liked');
            element.innerHTML = `<i class="fa fa-heart"></i> ${newCount}`;
        }
    });
}

function repostPost(postId) {
    fetch(`${apiBase}/post/${postId}/repost`, { method: 'POST', credentials: 'include' })
    .then(res => {
        if (res.ok) alert('Reposted!');
    });
}

function savePost(postId) {
    fetch(`${apiBase}/post/${postId}/save`, { method: 'POST', credentials: 'include' })
    .then(res => {
        if (res.ok) alert('Saved!');
    });
}

// Social Connections
function followUser(userId) {
    fetch(`${apiBase}/follow/${userId}`, { method: 'POST', credentials: 'include' })
    .then(res => res.json())
    .then(data => alert(data.message));
}

function unfollowUser(userId) {
    fetch(`${apiBase}/unfollow/${userId}`, { method: 'POST', credentials: 'include' })
    .then(res => res.json())
    .then(data => alert(data.message));
}

function blockUser(userId) {
    fetch(`${apiBase}/block`, {
        method: 'POST',
        body: JSON.stringify({ target_id: userId }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        if (res.ok) alert(data.message);
    });
}

function loadFriends() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="friends-navbar">
            <button onclick="loadFriendsList('followers')">Followers</button>
            <button onclick="loadFriendsList('following')">Following</button>
            <button onclick="loadFriendsList('friends')">Friends</button>
            <button onclick="loadFriendsList('requests')">Requests</button>
            <button onclick="loadFriendsList('suggested')">Suggested</button>
        </div>
        <div id="friends-list-container">Loading...</div>
    `;
    loadFriendsList('friends');
}

function loadFriendsList(view) {
    const container = document.getElementById('friends-list-container');
    container.innerHTML = 'Loading...';
    fetch(`${apiBase}/friends?view=${view}`, { credentials: 'include' })
    .then(res => res.json())
    .then(users => {
        container.innerHTML = '';
        users.forEach(user => {
            const userDiv = document.createElement('div');
            userDiv.classList.add('friends-item');
            userDiv.innerHTML = `
                <img src="${user.profile_pic_url || '/static/default.jpg'}" class="small-circle" onclick="loadView('profile', ${user.id})">
                <div class="user-info">
                    <span class="user-real-name" onclick="loadView('profile', ${user.id})">${user.real_name}</span>
                    <span class="user-mutual">@${user.username} - ${user.mutual_count} mutual friends/followers</span>
                </div>
                <div class="friends-actions">
                    <button onclick="messageUser(${user.id})"><i class="fa fa-envelope"></i></button>
                    ${view === 'requests' ? `
                        <button onclick="acceptFollow(${user.id})">Accept</button>
                        <button onclick="declineFollow(${user.id})">Decline</button>
                        <button onclick="blockUser(${user.id})">Block</button>
                    ` : view === 'suggested' ? `
                        <button onclick="followUser(${user.id})">Follow</button>
                        <button onclick="removeSuggestion(${user.id})">Remove</button>
                        <button onclick="blockUser(${user.id})">Block</button>
                    ` : `
                        <div class="dropdown">
                            <button class="dropbtn"><i class="fa fa-ellipsis-h"></i></button>
                            <div class="dropdown-content">
                                <a href="#" onclick="unfollowUser(${user.id})">Unfollow</a>
                                <a href="#" onclick="blockUser(${user.id})">Block</a>
                            </div>
                        </div>
                    `}
                </div>
            `;
            container.appendChild(userDiv);
        });
    });
}

function acceptFollow(followerId) {
    fetch(`${apiBase}/follow/accept/${followerId}`, { method: 'POST', credentials: 'include' })
    .then(res => {
        if (res.ok) loadFriendsList('requests');
    });
}

function declineFollow(followerId) {
    fetch(`${apiBase}/follow/decline/${followerId}`, { method: 'POST', credentials: 'include' })
    .then(res => {
        if (res.ok) loadFriendsList('requests');
    });
}

// Messaging and Groups
function loadInbox() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="inbox-navbar">
            <button onclick="loadChatList('direct_chats')">Chats</button>
            <button onclick="loadChatList('group_chats')">Groups</button>
            <button onclick="showModal('newChatModal')"><i class="fa fa-plus"></i></button>
        </div>
        <div id="chat-list-container">Loading...</div>
    `;
    loadChatList('direct_chats');
}

function loadChatList(type) {
    const container = document.getElementById('chat-list-container');
    container.innerHTML = 'Loading...';
    fetch(`${apiBase}/messages/chats`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => {
        container.innerHTML = '';
        const chats = type === 'direct_chats' ? data.direct_chats : data.group_chats;
        chats.forEach(chat => {
            const chatDiv = document.createElement('div');
            chatDiv.classList.add('chat-item');
            chatDiv.onclick = () => openChatModal(chat.id, type === 'group_chats');
            chatDiv.innerHTML = `
                <img src="${chat.profile_pic_url || '/static/default.jpg'}" class="small-circle">
                <div class="chat-info">
                    <span class="chat-name">${chat.real_name || chat.name}</span>
                    <span class="chat-last-msg">${chat.last_message}</span>
                </div>
                <div class="chat-meta">
                    <span class="chat-time">${chat.last_timestamp}</span>
                    ${chat.unread_count > 0 ? `<span class="unread-count">${chat.unread_count}</span>` : ''}
                </div>
            `;
            container.appendChild(chatDiv);
        });
    });
}

function openChatModal(id, isGroup) {
    showModal('chatModal');
    const header = document.getElementById('chatHeader');
    const content = document.getElementById('chatContent');
    header.innerHTML = '';
    content.innerHTML = '';
    
    const url = isGroup ? `${apiBase}/messages/group/${id}` : `${apiBase}/messages/direct/${id}`;
    fetch(url, { credentials: 'include' })
    .then(res => res.json())
    .then(messages => {
        messages.forEach(msg => {
            const msgDiv = document.createElement('div');
            msgDiv.classList.add('message');
            msgDiv.textContent = msg.text;
            content.appendChild(msgDiv);
        });
    });
}

function createGroup() {
    const name = document.getElementById('groupName').value;
    const description = document.getElementById('groupDescription').value;
    // Handle profile picture upload
    
    fetch(`${apiBase}/groups/create`, {
        method: 'POST',
        body: JSON.stringify({ name, description }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) alert(data.error);
        else {
            alert(data.message);
            hideModal('createGroupModal');
            loadInbox();
        }
    });
}

// Admin
function loadAdmin() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <h2>Admin Dashboard</h2>
        <h3>Pending Reports</h3>
        <div id="reports-list">Loading...</div>
    `;
    fetch(`${apiBase}/admin/reports`, { credentials: 'include' })
    .then(res => res.json())
    .then(reports => {
        const list = document.getElementById('reports-list');
        list.innerHTML = '';
        if (reports.length === 0) {
            list.innerHTML = '<p>No pending reports.</p>';
            return;
        }
        reports.forEach(report => {
            const reportDiv = document.createElement('div');
            reportDiv.classList.add('report-item');
            reportDiv.innerHTML = `
                <p><strong>Reporter:</strong> @${report.reporter_username}</p>
                <p><strong>Target:</strong> ${report.target_type} ID: ${report.target_id}</p>
                <p><strong>Reason:</strong> ${report.reason}</p>
                <button onclick="adminAction(${report.id}, 'dismiss', '${report.target_type}', ${report.target_id})">Dismiss</button>
                <button onclick="adminAction(${report.id}, 'ban_user', '${report.target_type}', ${report.target_id})">Ban User</button>
            `;
            list.appendChild(reportDiv);
        });
    });
}

function adminAction(reportId, action, targetType, targetId) {
    fetch(`${apiBase}/admin/action`, {
        method: 'POST',
        body: JSON.stringify({ report_id: reportId, action, target_type: targetType, target_id: targetId }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        if (res.ok) {
            alert(data.message);
            loadAdmin();
        }
    });
}
