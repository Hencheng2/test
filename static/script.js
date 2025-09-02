// static/script.js (fully adjusted for frontend functionality)

const apiBase = '/api';

function showModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = 'block';
    }
}

function hideModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Global state
let currentPage = 1;
let loading = false;
let currentView = 'home';
let currentStoryIndex = 0;
let stories = [];
let currentChatId = null;
let isGroupChat = false;

document.addEventListener('DOMContentLoaded', () => {
    checkLoggedIn();
    // Add event listeners for navigation
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

    // Handle form submissions
    document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
    document.getElementById('registerForm')?.addEventListener('submit', handleRegister);
    document.getElementById('postForm')?.addEventListener('submit', handlePostCreate);
    document.getElementById('reelForm')?.addEventListener('submit', handleReelCreate);
    document.getElementById('storyForm')?.addEventListener('submit', handleStoryCreate);
    document.getElementById('chatForm')?.addEventListener('submit', handleSendMessage);
    document.getElementById('groupCreateForm')?.addEventListener('submit', handleGroupCreate);
    document.getElementById('groupEditForm')?.addEventListener('submit', handleGroupEdit);
    document.getElementById('profileEditForm')?.addEventListener('submit', handleProfileEdit);

    // Initial check on page load
    window.addEventListener('scroll', handleInfiniteScroll);
});

// Replace alert with a custom message box
function showMessage(message) {
    const messageBox = document.getElementById('messageBox');
    if (messageBox) {
        messageBox.textContent = message;
        messageBox.style.display = 'block';
        setTimeout(() => {
            messageBox.style.display = 'none';
        }, 3000);
    }
}

function handleLogin(e) {
    e.preventDefault();
    const username = e.target.username.value;
    const password = e.target.password.value;
    fetch(`${apiBase}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        credentials: 'include'
    }).then(res => res.json()).then(data => {
        if (data.success) {
            sessionStorage.setItem('user_id', data.user_id);
            if (data.is_admin) {
                document.getElementById('adminBtn').style.display = 'block';
            }
            loadView('home');
        } else {
            showMessage(data.message);
        }
    });
}

function handleRegister(e) {
    e.preventDefault();
    const username = e.target.username.value;
    const real_name = e.target.real_name.value;
    const password = e.target.password.value;
    fetch(`${apiBase}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, real_name, password }),
        credentials: 'include'
    }).then(res => res.json()).then(data => {
        if (data.success) {
            showMessage(data.message);
            document.getElementById('login-link').click();
        } else {
            showMessage(data.message);
        }
    });
}

function handlePostCreate(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    fetch(`${apiBase}/post/create`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    }).then(res => res.json()).then(data => {
        showMessage(data.message);
        hideModal('addModal');
        loadView('home');
    });
}

function handleReelCreate(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    fetch(`${apiBase}/reel/create`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    }).then(res => res.json()).then(data => {
        showMessage(data.message);
        hideModal('addModal');
        loadView('reels');
    });
}

function handleStoryCreate(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    fetch(`${apiBase}/story/create`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    }).then(res => res.json()).then(data => {
        showMessage(data.message);
        hideModal('addModal');
        loadView('home');
    });
}

function handleProfileEdit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData();
    formData.append('bio', form.bio.value);
    if (form.profile_pic.files[0]) {
        formData.append('profile_pic', form.profile_pic.files[0]);
    }

    fetch(`${apiBase}/profile/edit`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    }).then(res => res.json()).then(data => {
        showMessage(data.message);
        hideModal('profileEditModal');
        loadView('profile', sessionStorage.getItem('user_id'));
    });
}

function handleSendMessage(e) {
    e.preventDefault();
    const text = e.target.text.value;
    if (!text) return;

    fetch(`${apiBase}/chat/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            receiver_id: currentChatId,
            text: text,
            is_group: isGroupChat
        }),
        credentials: 'include'
    }).then(res => res.json()).then(data => {
        if (data.success) {
            e.target.text.value = '';
            loadChatHistory(currentChatId, isGroupChat);
        } else {
            showMessage(data.message);
        }
    });
}

function handleGroupCreate(e) {
    e.preventDefault();
    const name = document.getElementById('groupName').value;
    const description = document.getElementById('groupDescription').value;
    fetch(`${apiBase}/group/create`, {
        method: 'POST',
        body: JSON.stringify({ name, description }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(res => res.json()).then(data => {
        if (data.success) {
            hideModal('groupCreateModal');
            loadView('inbox');
        } else {
            showMessage(data.message);
        }
    });
}

function handleGroupEdit(e) {
    e.preventDefault();
    const group_id = sessionStorage.getItem('currentGroupId');
    const name = document.getElementById('editGroupName').value;
    const description = document.getElementById('editGroupDescription').value;
    fetch(`${apiBase}/group/edit`, {
        method: 'POST',
        body: JSON.stringify({ group_id, name, description }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(res => res.json()).then(data => {
        if (data.success) {
            hideModal('groupEditModal');
            loadChatHistory(group_id, true);
        } else {
            showMessage(data.message);
        }
    });
}

function checkLoggedIn() {
    if (!sessionStorage.getItem('user_id')) {
        loadAuthView();
    } else {
        loadView('home');
    }
}

function loadAuthView() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div id="auth-container">
            <div id="auth-form-container">
                <div id="login-view">
                    <h2>Login</h2>
                    <form id="loginForm">
                        <input type="text" name="username" placeholder="Username" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit">Log In</button>
                    </form>
                    <p>Don't have an account? <span class="switch-link" onclick="showRegister()">Sign Up</span></p>
                </div>
                <div id="register-view" style="display:none;">
                    <h2>Register</h2>
                    <form id="registerForm">
                        <input type="text" name="username" placeholder="Username" required>
                        <input type="text" name="real_name" placeholder="Full Name" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit">Register</button>
                    </form>
                    <p>Already have an account? <span class="switch-link" onclick="showLogin()">Log In</span></p>
                </div>
            </div>
        </div>
    `;
    document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
    document.getElementById('registerForm')?.addEventListener('submit', handleRegister);
    document.querySelector('.nav-bar').style.display = 'none';
}

function showRegister() {
    document.getElementById('login-view').style.display = 'none';
    document.getElementById('register-view').style.display = 'block';
}
function showLogin() {
    document.getElementById('login-view').style.display = 'block';
    document.getElementById('register-view').style.display = 'none';
}

function loadView(viewName, param = null) {
    const content = document.getElementById('content');
    content.innerHTML = '<h1>Loading...</h1>';
    document.querySelector('.nav-bar').style.display = 'flex';
    document.querySelectorAll('.nav-button').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`${viewName}Btn`)?.classList.add('active');
    currentView = viewName;
    currentPage = 1;
    loading = false;

    switch (viewName) {
        case 'home':
            loadHomeFeed();
            break;
        case 'reels':
            loadReelsFeed();
            break;
        case 'friends':
            loadFriends();
            break;
        case 'inbox':
            loadInbox();
            break;
        case 'profile':
            loadProfile(param);
            break;
        case 'search':
            loadSearch();
            break;
        case 'notifications':
            loadNotifications();
            break;
        case 'admin':
            loadAdminDashboard();
            break;
        case 'menu':
            loadMenu();
            break;
        default:
            content.innerHTML = '<h1>View Not Found</h1>';
    }
}

function loadHomeFeed() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div id="stories-section"></div>
        <div id="posts-section"></div>
    `;
    loadStories();
    loadPosts();
}

function loadStories() {
    fetch(`${apiBase}/story/feed`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            const storiesContainer = document.getElementById('stories-section');
            storiesContainer.innerHTML = '';
            if (data.success && data.stories.length > 0) {
                stories = data.stories;
                const storyList = document.createElement('div');
                storyList.className = 'stories-container';
                data.stories.forEach((story, index) => {
                    const storyItem = document.createElement('div');
                    storyItem.className = 'story-item';
                    storyItem.innerHTML = `
                        <img src="${story.user.profile_pic_url || '/static/default-pfp.png'}" alt="${story.user.username}" class="story-circle">
                        <p class="story-username">${story.user.username}</p>
                    `;
                    storyItem.onclick = () => showStoryModal(index);
                    storyList.appendChild(storyItem);
                });
                storiesContainer.appendChild(storyList);
            } else {
                storiesContainer.innerHTML = '<p>No stories to show.</p>';
            }
        });
}

function showStoryModal(index) {
    currentStoryIndex = index;
    const story = stories[currentStoryIndex];
    if (!story) {
        return hideModal('storyModal');
    }

    const storyModal = document.getElementById('storyModal');
    const storyContent = storyModal.querySelector('.story-modal-content');
    const mediaElement = story.media_url.endsWith('.mp4') ?
        `<video src="${story.media_url}" class="story-media" controls autoplay playsinline></video>` :
        `<img src="${story.media_url}" class="story-media">`;

    storyContent.innerHTML = `
        <div class="story-header">
            <img src="${story.user.profile_pic_url || '/static/default-pfp.png'}" class="profile-pic">
            <div class="story-user-info">
                <span class="story-username">${story.user.username}</span>
            </div>
            <span class="close" onclick="hideModal('storyModal')">&times;</span>
        </div>
        ${mediaElement}
    `;

    showModal('storyModal');
}

function loadPosts(append = false) {
    if (loading) return;
    loading = true;
    fetch(`${apiBase}/post/feed?page=${currentPage}`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            const postsContainer = document.getElementById('posts-section');
            if (data.success && data.posts.length > 0) {
                data.posts.forEach(post => {
                    const postCard = document.createElement('div');
                    postCard.className = 'post-card';
                    postCard.innerHTML = `
                        <div class="post-header">
                            <img src="${post.user.profile_pic_url || '/static/default-pfp.png'}" class="profile-pic" onclick="loadView('profile', '${post.user.id}')">
                            <div>
                                <div><span class="username">${post.user.real_name}</span></div>
                                <div class="post-timestamp">${new Date(post.timestamp).toLocaleString()}</div>
                            </div>
                        </div>
                        <img src="${post.media_url}" class="post-media">
                        <div class="post-actions">
                            <button class="post-action-btn ${post.liked_by_user ? 'liked' : ''}" onclick="likeContent('${post.id}', 'post')">
                                <i class="fa fa-heart"></i>
                                <span>${post.like_count}</span>
                            </button>
                            <button class="post-action-btn" onclick="showCommentModal('${post.id}')">
                                <i class="fa fa-comment"></i>
                            </button>
                        </div>
                        <div class="post-info">
                            <p>${post.description}</p>
                        </div>
                    `;
                    postsContainer.appendChild(postCard);
                });
                currentPage++;
                loading = false;
            } else if (!append) {
                postsContainer.innerHTML = '<p>No posts to display.</p>';
            }
        });
}

function handleInfiniteScroll() {
    if (currentView === 'home' && window.innerHeight + window.scrollY >= document.body.offsetHeight - 500 && !loading) {
        loadPosts(true);
    }
}

function likeContent(contentId, contentType) {
    fetch(`${apiBase}/post/like`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ post_id: contentId }),
        credentials: 'include'
    }).then(res => res.json()).then(data => {
        if (data.success) {
            loadView('home'); // Reload to show updated count
        }
    });
}

function showCommentModal(postId) {
    const modal = document.getElementById('commentModal');
    const commentsList = modal.querySelector('#comments-list');
    const commentForm = modal.querySelector('#commentForm');
    commentForm.onsubmit = (e) => {
        e.preventDefault();
        const text = commentForm.text.value;
        fetch(`${apiBase}/post/comment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ post_id: postId, text }),
            credentials: 'include'
        }).then(res => res.json()).then(data => {
            if (data.success) {
                commentForm.text.value = '';
                loadComments(postId, commentsList);
            }
        });
    };
    loadComments(postId, commentsList);
    showModal('commentModal');
}

function loadComments(postId, container) {
    container.innerHTML = 'Loading comments...';
    fetch(`${apiBase}/post/comments?post_id=${postId}`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            container.innerHTML = '';
            if (data.success && data.comments.length > 0) {
                data.comments.forEach(comment => {
                    const commentEl = document.createElement('div');
                    commentEl.className = 'comment-item';
                    commentEl.innerHTML = `
                        <img src="${comment.user.profile_pic_url || '/static/default-pfp.png'}" class="profile-pic" alt="">
                        <div>
                            <span class="username">${comment.user.username}</span> ${comment.text}
                        </div>
                    `;
                    container.appendChild(commentEl);
                });
            } else {
                container.innerHTML = '<p>No comments yet.</p>';
            }
        });
}

function loadReelsFeed() {
    const content = document.getElementById('content');
    content.innerHTML = '<div id="reels-container"></div>';
    fetch(`${apiBase}/reel/feed`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            const reelsContainer = document.getElementById('reels-container');
            if (data.success && data.reels.length > 0) {
                data.reels.forEach(reel => {
                    const reelItem = document.createElement('div');
                    reelItem.className = 'reel-video';
                    reelItem.innerHTML = `
                        <video src="${reel.media_url}" controls></video>
                        <p>${reel.description}</p>
                    `;
                    reelsContainer.appendChild(reelItem);
                });
            } else {
                reelsContainer.innerHTML = '<p>No reels to display.</p>';
            }
        });
}

function loadFriends() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="container">
            <h2>My Friends</h2>
            <div id="friend-list" class="friend-list"></div>
        </div>
    `;
    fetch(`${apiBase}/friends/list`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            const friendList = document.getElementById('friend-list');
            if (data.success && data.friends.length > 0) {
                data.friends.forEach(friend => {
                    const friendItem = document.createElement('div');
                    friendItem.className = 'friend-item';
                    friendItem.innerHTML = `
                        <img src="${friend.profile_pic_url || '/static/default-pfp.png'}" class="profile-pic" onclick="loadView('profile', '${friend.id}')">
                        <span>${friend.real_name}</span>
                    `;
                    friendList.appendChild(friendItem);
                });
            } else {
                friendList.innerHTML = '<p>You have no friends yet.</p>';
            }
        });
}

function loadInbox() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="container">
            <h2>Inbox</h2>
            <button onclick="showModal('groupCreateModal')">Create Group</button>
            <div id="inbox-list" class="inbox-list"></div>
        </div>
    `;
    fetch(`${apiBase}/inbox/list`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            const inboxList = document.getElementById('inbox-list');
            inboxList.innerHTML = '';
            if (data.success) {
                data.direct_chats.forEach(chat => {
                    const chatItem = document.createElement('div');
                    chatItem.className = 'chat-item';
                    chatItem.onclick = () => showChatModal(chat.id, false);
                    chatItem.innerHTML = `
                        <img src="${chat.profile_pic_url || '/static/default-pfp.png'}" class="profile-pic">
                        <div class="chat-info">
                            <div class="chat-name">${chat.real_name}</div>
                            <div class="chat-last-msg">${chat.last_message}</div>
                        </div>
                        ${chat.unread > 0 ? `<div class="unread">${chat.unread}</div>` : ''}
                    `;
                    inboxList.appendChild(chatItem);
                });
                data.group_chats.forEach(chat => {
                    const chatItem = document.createElement('div');
                    chatItem.className = 'chat-item';
                    chatItem.onclick = () => showChatModal(chat.id, true);
                    chatItem.innerHTML = `
                        <img src="${chat.profile_pic_url || '/static/default-group-pfp.png'}" class="profile-pic">
                        <div class="chat-info">
                            <div class="chat-name">${chat.name}</div>
                            <div class="chat-last-msg">${chat.last_message}</div>
                        </div>
                    `;
                    inboxList.appendChild(chatItem);
                });
                if (data.direct_chats.length === 0 && data.group_chats.length === 0) {
                    inboxList.innerHTML = '<p>Your inbox is empty.</p>';
                }
            }
        });
}

function showChatModal(chatId, isGroup) {
    currentChatId = chatId;
    isGroupChat = isGroup;
    const modal = document.getElementById('chatModal');
    const modalTitle = modal.querySelector('h3');
    modalTitle.textContent = isGroup ? 'Group Chat' : 'Direct Message';
    
    sessionStorage.setItem('currentGroupId', chatId);
    
    if (isGroup) {
      document.getElementById('groupEditBtn').style.display = 'block';
    } else {
      document.getElementById('groupEditBtn').style.display = 'none';
    }

    loadChatHistory(chatId, isGroup);
    showModal('chatModal');
}

function loadChatHistory(chatId, isGroup) {
    const chatContainer = document.getElementById('chat-messages');
    chatContainer.innerHTML = 'Loading messages...';
    fetch(`${apiBase}/chat/history?chat_id=${chatId}&is_group=${isGroup}`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            chatContainer.innerHTML = '';
            if (data.success && data.messages.length > 0) {
                data.messages.forEach(msg => {
                    const messageEl = document.createElement('div');
                    messageEl.className = 'chat-message-bubble ' + (msg.sender_id === sessionStorage.getItem('user_id') ? 'sent' : 'received');
                    messageEl.innerHTML = `
                        <div>${msg.text}</div>
                    `;
                    chatContainer.appendChild(messageEl);
                });
            } else {
                chatContainer.innerHTML = '<p>Start the conversation!</p>';
            }
            chatContainer.scrollTop = chatContainer.scrollHeight;
        });
}

function loadSearch() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="container">
            <h2>Search Users</h2>
            <input type="text" id="searchInput" placeholder="Search by username or name">
            <div id="searchResults" class="user-list"></div>
        </div>
    `;
    document.getElementById('searchInput').addEventListener('input', (e) => {
        const query = e.target.value;
        if (query.length > 1) {
            fetch(`${apiBase}/user/search?q=${query}`, { credentials: 'include' })
                .then(res => res.json())
                .then(data => {
                    const resultsContainer = document.getElementById('searchResults');
                    resultsContainer.innerHTML = '';
                    if (data.success && data.users.length > 0) {
                        data.users.forEach(user => {
                            const userItem = document.createElement('div');
                            userItem.className = 'friend-item';
                            userItem.innerHTML = `
                                <img src="${user.profile_pic_url || '/static/default-pfp.png'}" class="profile-pic">
                                <span>${user.real_name} (@${user.username})</span>
                                <button onclick="loadView('profile', '${user.id}')" style="margin-left:auto;">View Profile</button>
                            `;
                            resultsContainer.appendChild(userItem);
                        });
                    } else {
                        resultsContainer.innerHTML = '<p>No users found.</p>';
                    }
                });
        }
    });
}

function loadNotifications() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="container">
            <h2>Notifications</h2>
            <div id="notifications-list"></div>
        </div>
    `;
    fetch(`${apiBase}/notifications/get`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            const list = document.getElementById('notifications-list');
            if (data.success && data.notifications.length > 0) {
                data.notifications.forEach(notif => {
                    const notifItem = document.createElement('div');
                    notifItem.className = 'notification-item';
                    notifItem.innerHTML = `<p>${notif.content}</p>`;
                    list.appendChild(notifItem);
                });
            } else {
                list.innerHTML = '<p>You have no new notifications.</p>';
            }
        });
}

function loadAdminDashboard() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="container">
            <h2>Admin Dashboard</h2>
            <h3>User Management</h3>
            <div id="admin-users-list"></div>
            <h3>Pending Reports</h3>
            <div id="admin-reports-list"></div>
        </div>
    `;
    fetch(`${apiBase}/admin/dashboard`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const usersList = document.getElementById('admin-users-list');
                usersList.innerHTML = '<h4>Users</h4>';
                data.users.forEach(user => {
                    const userDiv = document.createElement('div');
                    userDiv.className = 'admin-user-item';
                    userDiv.innerHTML = `
                        <span>${user.username} (${user.real_name}) - ${user.active ? 'Active' : 'Blocked'}</span>
                        <button onclick="adminToggleActive('${user.id}')">${user.active ? 'Block' : 'Unblock'}</button>
                    `;
                    usersList.appendChild(userDiv);
                });

                const reportsList = document.getElementById('admin-reports-list');
                reportsList.innerHTML = '<h4>Reports</h4>';
                data.reports.forEach(report => {
                    const reportDiv = document.createElement('div');
                    reportDiv.className = 'admin-report-item';
                    reportDiv.innerHTML = `
                        <p>Report ID: ${report.id}</p>
                        <p>Reason: ${report.reason}</p>
                        <button onclick="adminResolveReport('${report.id}')">Resolve</button>
                        <button onclick="adminDeleteContent('${report.id}')">Delete Content</button>
                    `;
                    reportsList.appendChild(reportDiv);
                });
            } else {
                content.innerHTML = '<p>Access Denied.</p>';
            }
        });
}

function adminToggleActive(userId) {
    fetch(`${apiBase}/admin/toggle_active`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
        credentials: 'include'
    }).then(() => loadAdminDashboard());
}

function adminResolveReport(reportId) {
    fetch(`${apiBase}/admin/report/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_id: reportId }),
        credentials: 'include'
    }).then(() => loadAdminDashboard());
}

function adminDeleteContent(reportId) {
    fetch(`${apiBase}/admin/report/delete_content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_id: reportId }),
        credentials: 'include'
    }).then(() => loadAdminDashboard());
}

function loadMenu() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="container">
            <h2>Menu</h2>
            <ul>
                <li><button onclick="handleLogout()">Logout</button></li>
                <li><button onclick="showModal('profileEditModal')">Edit Profile</button></li>
                <li><button onclick="showModal('reportModal')">Report Something</button></li>
            </ul>
        </div>
    `;
}

function handleLogout() {
    fetch(`${apiBase}/logout`, {
        method: 'POST',
        credentials: 'include'
    }).then(res => res.json()).then(data => {
        if (data.success) {
            sessionStorage.clear();
            loadAuthView();
        }
    });
}
