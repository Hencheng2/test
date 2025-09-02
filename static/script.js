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
        credentials: 'include' // Ensure cookies/session are sent
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

function loadView(view) {
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
        loadProfile(sessionStorage.getItem('user_id'));
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
                renderPosts(data);
            }
            loading = false;
        })
        .catch(err => {
            console.error('Error loading more posts:', err);
            loading = false;
        });
    }
}

function loadHome() {
    const content = document.getElementById('content');
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
        content.innerHTML = '';
        content.appendChild(storiesDiv);
    })
    .catch(err => console.error('Error loading stories:', err));
    fetch(`${apiBase}/posts/feed?page=1`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => renderPosts(data))
    .catch(err => console.error('Error loading posts:', err));
}

function renderPosts(posts) {
    const content = document.getElementById('content');
    posts.forEach(post => {
        const postDiv = document.createElement('div');
        postDiv.classList.add('post');
        postDiv.innerHTML = `
            <img src="${post.profile_pic_url || '/static/default.jpg'}" class="small-circle">
            <span>${post.real_name || 'Anonymous'} (@${post.username}) - ${new Date(post.timestamp).toLocaleString()}</span>
            <p>${post.description}</p>
            ${post.media_url ? (post.type === 'reel' ? `<video src="${post.media_url}" controls class="reel-video"></video>` : `<img src="${post.media_url}">`) : ''}
            <div class="button-group">
                <button onclick="likePost(${post.id})">Like</button>
                <button onclick="showCommentModal(${post.id})">Comment</button>
                <button onclick="sharePost(${post.id})">Share</button>
                ${post.user_id != sessionStorage.getItem('user_id') ? `<button onclick="followUser(${post.user_id})">Follow</button>` : ''}
                <button onclick="savePost(${post.id})">Save</button>
                ${post.user_id != sessionStorage.getItem('user_id') ? `<button onclick="repostPost(${post.id})">Repost</button>` : ''}
                <button>Views: ${post.views}</button>
                ${post.user_id != sessionStorage.getItem('user_id') ? `<button onclick="reportPost(${post.id})">Report</button>` : ''}
                ${post.user_id != sessionStorage.getItem('user_id') ? `<button onclick="hidePost(${post.id})">Hide</button>` : ''}
                ${post.user_id != sessionStorage.getItem('user_id') ? `<button onclick="toggleNotifications(${post.id})">Turn on notifications</button>` : ''}
                ${post.user_id != sessionStorage.getItem('user_id') ? `<button onclick="blockUser(${post.user_id})">Block</button>` : ''}
            </div>
        `;
        content.appendChild(postDiv);
    });
}

function showStory(postId) {
    const modal = document.getElementById('storyModal');
    const storyView = document.getElementById('storyView');
    fetch(`${apiBase}/post/${postId}`, { credentials: 'include' })
    .then(res => res.json())
    .then(story => {
        storyView.innerHTML = `<img src="${story.media_url || '/static/default.jpg'}" style="width:100%;height:100vh;object-fit:contain;">`;
        showModal('storyModal');
        let touchStartX = 0, touchEndX = 0, touchStartY = 0, touchEndY = 0;
        let isPaused = false;
        modal.addEventListener('touchstart', e => {
            touchStartX = e.changedTouches[0].screenX;
            touchStartY = e.changedTouches[0].screenY;
            if (story.type === 'story' && story.media_url.endsWith('.mp4')) {
                isPaused = true;
                document.querySelector('video')?.pause();
            }
        });
        modal.addEventListener('touchend', e => {
            touchEndX = e.changedTouches[0].screenX;
            touchEndY = e.changedTouches[0].screenY;
            if (touchEndX < touchStartX - 50) {
                // Next story (implement fetch next story)
            } else if (touchEndX > touchStartX + 50) {
                // Previous story
            }
            if (touchEndY > touchStartY + 50) {
                hideModal('storyModal');
            }
            if (isPaused) {
                document.querySelector('video')?.play();
                isPaused = false;
            }
        });
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
    .then(res => {
        if (res.ok) {
            hideModal('loginModal');
            checkLoggedIn();
        } else {
            res.json().then(data => alert(data.error || 'Login failed'));
        }
    })
    .catch(err => alert('Error: ' + err));
}

function register() {
    const username = document.getElementById('regUsername').value;
    const password = document.getElementById('regPassword').value;
    fetch(`${apiBase}/register`, {
        method: 'POST',
        body: JSON.stringify({ username, password }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => {
        if (res.ok) {
            res.json().then(data => {
                alert('Registered! Your unique key: ' + data.unique_key);
                hideModal('registerModal');
                checkLoggedIn();
            });
        } else {
            res.json().then(data => alert(data.error || 'Registration failed'));
        }
    })
    .catch(err => alert('Error: ' + err));
}

function forgot() {
    const username = document.getElementById('forgotUsername').value;
    const unique_key = document.getElementById('forgotKey').value;
    fetch(`${apiBase}/forgot`, {
        method: 'POST',
        body: JSON.stringify({ username, unique_key }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => {
        if (res.ok) {
            showModal('resetModal');
            hideModal('forgotModal');
            setTimeout(() => {
                showModal('resetModal');
            }, 5000); // Simulate 5s delay
        } else {
            res.json().then(data => alert(data.error || 'Verification failed'));
        }
    })
    .catch(err => alert('Error: ' + err));
}

function resetPassword() {
    const password = document.getElementById('newPassword').value;
    fetch(`${apiBase}/reset_password`, {
        method: 'POST',
        body: JSON.stringify({ password }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => {
        if (res.ok) {
            hideModal('resetModal');
            showModal('loginModal');
        } else {
            res.json().then(data => alert(data.error || 'Reset failed'));
        }
    })
    .catch(err => alert('Error: ' + err));
}

function createPost() {
    const type = document.getElementById('addType').value;
    const description = document.getElementById('addDescription').value;
    const file = document.getElementById('addMedia').files[0];
    if (!file && type !== 'post') {
        alert('Media required for reels/stories');
        return;
    }
    const formData = new FormData();
    if (file) formData.append('file', file);
    fetch(`${apiBase}/upload`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        const media_url = data.url || '';
        fetch(`${apiBase}/post/create`, {
            method: 'POST',
            body: JSON.stringify({ type, description, media_url }),
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        })
        .then(res => {
            if (res.ok) {
                hideModal('addModal');
                loadView('home');
            } else {
                res.json().then(data => alert(data.error || 'Post creation failed'));
            }
        });
    })
    .catch(err => alert('Error: ' + err));
}

function likePost(id) {
    fetch(`${apiBase}/post/like`, {
        method: 'POST',
        body: JSON.stringify({ post_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => {
        if (res.ok) alert('Post liked');
    })
    .catch(err => alert('Error: ' + err));
}

// Placeholder functions (implement as needed)
function showCommentModal(id) { alert('Comment modal for post ' + id); }
function sharePost(id) { alert('Share post ' + id); }
function followUser(id) { 
    fetch(`${apiBase}/follow/request`, {
        method: 'POST',
        body: JSON.stringify({ target_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => {
        if (res.ok) alert('Follow request sent');
    });
}
function savePost(id) { 
    fetch(`${apiBase}/post/save`, {
        method: 'POST',
        body: JSON.stringify({ post_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => {
        if (res.ok) alert('Post saved');
    });
}
function repostPost(id) { 
    fetch(`${apiBase}/post/repost`, {
        method: 'POST',
        body: JSON.stringify({ post_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => {
        if (res.ok) alert('Post reposted');
    });
}
function reportPost(id) { 
    fetch(`${apiBase}/post/report`, {
        method: 'POST',
        body: JSON.stringify({ post_id: id, reason: 'Reported' }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => {
        if (res.ok) alert('Post reported');
    });
}
function hidePost(id) { alert('Hide post ' + id); }
function toggleNotifications(id) { alert('Toggle notifications for post ' + id); }
function blockUser(id) { 
    fetch(`${apiBase}/block`, {
        method: 'POST',
        body: JSON.stringify({ target_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(res => {
        if (res.ok) alert('User blocked');
    });
}
function loadReels() { document.getElementById('content').innerHTML = '<p>Reels view (implement)</p>'; }
function loadFriends() { document.getElementById('content').innerHTML = '<p>Friends view (implement)</p>'; }
function loadInbox() { document.getElementById('content').innerHTML = '<p>Inbox view (implement)</p>'; }
function loadProfile(userId) { document.getElementById('content').innerHTML = '<p>Profile view (implement)</p>'; }
function loadSearch() { document.getElementById('content').innerHTML = '<p>Search view (implement)</p>'; }
function loadNotifications() { document.getElementById('content').innerHTML = '<p>Notifications view (implement)</p>'; }
function loadMenu() { document.getElementById('content').innerHTML = '<p>Menu view (implement)</p>'; }
function loadAdmin() { document.getElementById('content').innerHTML = '<p>Admin view (implement)</p>'; }
function sendChat() { alert('Send chat message'); }
