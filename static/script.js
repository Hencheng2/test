```javascript
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');
    checkLoginStatus();
    setupEventListeners();
});

function checkLoginStatus() {
    fetch('/api/profile', { credentials: 'include' })
        .then(response => {
            console.log('Profile response:', response.status);
            if (response.ok) {
                showSection('home');
                loadHome();
                response.json().then(data => {
                    if (data.is_admin) {
                        document.getElementById('admin-btn').style.display = 'block';
                    }
                });
            } else {
                showModal('login-modal');
            }
        })
        .catch(err => {
            console.error('Error checking login:', err);
            showModal('login-modal');
        });
}

function setupEventListeners() {
    console.log('Setting up event listeners');
    const buttons = [
        { id: 'home-btn', handler: loadHome },
        { id: 'reels-btn', handler: loadReels },
        { id: 'friends-btn', handler: () => loadFriendsTab('friends') },
        { id: 'inbox-btn', handler: () => loadInboxTab('chats') },
        { id: 'profile-btn', handler: () => loadProfileTab('posts') },
        { id: 'search-btn', handler: () => loadSearchTab('all') },
        { id: 'addto-btn', handler: () => showSection('addto') },
        { id: 'notifications-btn', handler: loadNotifications },
        { id: 'menu-btn', handler: () => showSection('menu') },
        { id: 'admin-btn', handler: () => loadAdminTab('users') },
        { id: 'settings-btn', handler: () => showModal('settings-modal') },
        { id: 'logout-btn', handler: logout }
    ];
    buttons.forEach(({ id, handler }) => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', () => {
                console.log(`${id} clicked`);
                fetch('/api/profile', { credentials: 'include' })
                    .then(response => {
                        if (response.ok) handler();
                        else showModal('login-modal');
                    })
                    .catch(err => {
                        console.error(`Error fetching /api/profile for ${id}:`, err);
                        showModal('login-modal');
                    });
            });
        } else {
            console.error(`Button ${id} not found`);
        }
    });
    document.getElementById('login-form').addEventListener('submit', login);
    document.getElementById('register-form').addEventListener('submit', register);
    document.getElementById('forgot-form').addEventListener('submit', forgotPassword);
    document.getElementById('reset-form').addEventListener('submit', resetPassword);
    document.getElementById('create-post-form').addEventListener('submit', createContent);
    document.getElementById('create-reel-form').addEventListener('submit', createContent);
    document.getElementById('create-story-form').addEventListener('submit', createContent);
    document.getElementById('create-group-form').addEventListener('submit', createGroup);
    document.getElementById('comment-form').addEventListener('submit', commentPost);
    document.getElementById('settings-form').addEventListener('submit', updateSettings);
    document.getElementById('search-bar').addEventListener('input', search);
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', () => closeBtn.closest('.modal').style.display = 'none');
    });
}

function showSection(sectionId) {
    console.log(`Showing section: ${sectionId}`);
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
        section.style.display = 'none';
    });
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.add('active');
        section.style.display = 'block';
    } else {
        console.error(`Section ${sectionId} not found`);
    }
}

function showModal(modalId) {
    console.log(`Showing modal: ${modalId}`);
    document.querySelectorAll('.modal').forEach(modal => modal.style.display = 'none');
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
    } else {
        console.error(`Modal ${modalId} not found`);
    }
}

function login(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.fromEntries(formData)),
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'Logged in') {
            showSection('home');
            loadHome();
            document.querySelectorAll('.modal').forEach(modal => modal.style.display = 'none');
            if (data.is_admin) {
                document.getElementById('admin-btn').style.display = 'block';
            }
        } else {
            alert(data.error);
        }
    })
    .catch(err => console.error('Login error:', err));
}

function register(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.fromEntries(formData)),
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'Registered') {
            alert('Registered! Your unique key: ' + data.unique_key);
            showModal('login-modal');
        } else {
            alert(data.error);
        }
    })
    .catch(err => console.error('Register error:', err));
}

function forgotPassword(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    fetch('/api/forgot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.fromEntries(formData)),
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'Verified') {
            showModal('reset-modal');
        } else {
            alert(data.error);
        }
    })
    .catch(err => console.error('Forgot password error:', err));
}

function resetPassword(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    fetch('/api/reset_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.fromEntries(formData)),
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'Password reset') {
            showModal('login-modal');
        } else {
            alert(data.error);
        }
    })
    .catch(err => console.error('Reset password error:', err));
}

function loadHome() {
    showSection('home');
    fetch('/api/home', { credentials: 'include' })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            const stories = document.getElementById('stories');
            stories.innerHTML = data.stories.map(s => `
                <div class="story" data-id="${s.id}">
                    <img src="${s.media_url || '/static/placeholder.jpg'}" alt="Story">
                    <p>${s.user}</p>
                </div>
            `).join('');
            stories.querySelectorAll('.story').forEach(story => {
                story.addEventListener('click', () => {
                    fetch(`/api/story/${story.dataset.id}`, { credentials: 'include' })
                        .then(res => res.json())
                        .then(data => {
                            document.getElementById('story-content').innerHTML = `
                                <img src="${data.media_url}" alt="Story">
                                <p>${data.description}</p>
                                <p>By ${data.user}</p>
                            `;
                            showModal('story-modal');
                        });
                });
            });
            loadPosts();
        })
        .catch(err => {
            console.error('Home error:', err);
            showModal('login-modal');
        });
}

function loadPosts(page = 1) {
    fetch(`/api/posts?page=${page}`, { credentials: 'include' })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            const posts = document.getElementById('posts');
            posts.innerHTML = data.posts.map(p => `
                <div class="post">
                    <p><strong>${p.user.real_name}</strong> @${p.user.username}</p>
                    <p>${p.description}</p>
                    ${p.media_url ? `<img src="${p.media_url}" alt="Post">` : ''}
                    <p>${new Date(p.timestamp).toLocaleString()}</p>
                    <p>${p.likes} likes, ${p.comments} comments, ${p.views} views</p>
                    <div class="post-actions">
                        <button onclick="likePost(${p.id}, this)">${p.is_liked ? 'Unlike' : 'Like'}</button>
                        <button onclick="showComments(${p.id})">Comment</button>
                        <button onclick="repost(${p.id})">Repost</button>
                        <button onclick="savePost(${p.id}, this)">${p.is_saved ? 'Unsave' : 'Save'}</button>
                        <button onclick="followUser(${p.user.id}, this)">${p.is_own ? '' : 'Follow'}</button>
                        <button onclick="reportPost(${p.id})">Report</button>
                        <button onclick="hidePost(${p.id})">${p.is_own ? '' : 'Hide'}</button>
                        <button onclick="blockUser(${p.user.id})">${p.is_own ? '' : 'Block'}</button>
                    </div>
                </div>
            `).join('');
            if (data.has_next) {
                const loadMore = document.createElement('button');
                loadMore.textContent = 'Load More';
                loadMore.onclick = () => loadPosts(page + 1);
                posts.appendChild(loadMore);
            }
        })
        .catch(err => console.error('Posts error:', err));
}

function loadReels() {
    showSection('reels');
    fetch('/api/reels', { credentials: 'include' })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            const reels = document.getElementById('reels');
            reels.innerHTML = data.reels.map(r => `
                <div class="post">
                    <p><strong>${r.user.real_name}</strong> @${
