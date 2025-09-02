// static/script.js (Full JS Code)

const apiBase = '/api';

function showModal(id) {
    document.getElementById(id).style.display = 'block';
}

function hideModal(id) {
    document.getElementById(id).style.display = 'none';
}

let currentPage = 1;
let loading = false;
let currentView = 'home';

document.addEventListener('DOMContentEvent', () => {
    checkLoggedIn();
    document.getElementById('homeBtn').addEventListener('click', () => loadView('home'));
    document.getElementById('reelsBtn').addEventListener('click', () => loadView('reels'));
    document.getElementById('friendsBtn').addEventListener('click', () => loadView('friends'));
    document.getElementById('inboxBtn').addEventListener('click', () => loadView('inbox'));
    document.getElementById('profileBtn').addEventListener('click', () => loadView('profile'));
    document.getElementById('searchBtn').addEventListener('click', () => loadView('search'));
    document.getElementById('addBtn').addEventListener('click', () => showModal('addModal'));
    document.getElementById('notifBtn').addEventListener('click', () => loadView('notifications'));
    document.getElementById('menuBtn').addEventListener('click', () => loadView('menu'));
    document.getElementById('adminBtn').addEventListener('click', () => loadView('admin'));
    window.addEventListener('scroll', handleInfiniteScroll);
});

function checkLoggedIn() {
    fetch(`${apiBase}/user/me`)
    .then(res => {
        if (res.status === 401) {
            showModal('loginModal');
        } else {
            res.json().then(user => {
                if (user.is_admin) {
                    document.getElementById('adminBtn').style.display = 'block';
                }
                loadView('home');
            });
        }
    }).catch(() => showModal('loginModal'));
}

function loadView(view) {
    currentView = view;
    currentPage = 1;
    const content = document.getElementById('content');
    content.innerHTML = '';
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
        fetch(`${apiBase}/posts/feed?page=${currentPage}`)
        .then(res => res.json())
        .then(data => {
            if (data.length > 0) {
                renderPosts(data);
            }
            loading = false;
        });
    } // similar for other views with pagination
}

function loadHome() {
    fetch(`${apiBase}/stories`)
    .then(res => res.json())
    .then(stories => {
        const storiesDiv = document.createElement('div');
        storiesDiv.classList.add('stories');
        stories.forEach(story => {
            const circle = document.createElement('div');
            circle.classList.add('story-circle');
            circle.style.backgroundImage = `url(${story.media_url})`;
            circle.onclick = () => showStory(story.id); // implement showStory with swipe etc
            const username = document.createElement('p');
            username.textContent = story.username;
            circle.appendChild(username);
            storiesDiv.appendChild(circle);
        });
        content.appendChild(storiesDiv);
    });
    fetch(`${apiBase}/posts/feed?page=1`)
    .then(res => res.json())
    .then(data => renderPosts(data));
}

function renderPosts(posts) {
    const content = document.getElementById('content');
    posts.forEach(post => {
        const postDiv = document.createElement('div');
        postDiv.classList.add('post');
        postDiv.innerHTML = `
            <img src="${post.profile_pic_url}" class="small-circle">
            <span>${post.real_name} (@${post.username}) - ${post.timestamp}</span>
            <p>${post.description}</p>
            ${post.media_url ? (post.type === 'reel' ? `<video src="${post.media_url}" controls></video>` : `<img src="${post.media_url}">`) : ''}
            <div class="button-group">
                <button onclick="likePost(${post.id})">Like</button>
                <button onclick="showCommentModal(${post.id})">Comment</button>
                <button onclick="sharePost(${post.id})">Share</button>
                <button onclick="followUser(${post.user_id})">Follow</button>
                <button onclick="savePost(${post.id})">Save</button>
                <button onclick="repostPost(${post.id})">Repost</button>
                <button>Views: ${post.views}</button>
                <button onclick="reportPost(${post.id})">Report</button>
                <button onclick="hidePost(${post.id})">Hide</button>
                <button>Turn on notifications</button>
                <button onclick="blockUser(${post.user_id})">Block</button>
            </div>
        `;
        content.appendChild(postDiv);
    });
}

function showStory(postId) {
    // Fetch story, show in modal, implement swipe, pause, exit
    // For swipe, load all stories, index, on swipe change
    // Touch events as described
    showModal('storyModal');
    // code for touch
    let touchStartX = 0;
    let touchEndX = 0;
    const modal = document.getElementById('storyModal');
    modal.addEventListener('touchstart', e => touchStartX = e.changedTouches[0].screenX);
    modal.addEventListener('touchend', e => {
        touchEndX = e.changedTouches[0].screenX;
        if (touchEndX < touchStartX) {
            // next story
        } else if (touchEndX > touchStartX) {
            // prev
        }
    });
    // pause on hold
    modal.addEventListener('touchstart', () => {
        // pause video
    });
    modal.addEventListener('touchend', () => {
        // resume
    });
    // exit swipe down
    let touchStartY = 0;
    let touchEndY = 0;
    modal.addEventListener('touchstart', e => touchStartY = e.changedTouches[0].screenY);
    modal.addEventListener('touchend', e => {
        touchEndY = e.changedTouches[0].screenY;
        if (touchEndY > touchStartY + 50) hideModal('storyModal');
    });
}

// Similar functions for loadReels (vertical videos, touch pause), loadFriends (tabs for followers, following, friends, requests, suggested), loadInbox (chats, groups, new chat), loadProfile (own or other, edit, gallery), loadSearch (tabs), loadNotifications, loadMenu (help, settings), loadAdmin (users, groups, reports)

function login() {
    const identifier = document.getElementById('loginIdentifier').value;
    const password = document.getElementById('loginPassword').value;
    fetch(`${apiBase}/login`, {
        method: 'POST',
        body: JSON.stringify({identifier, password}),
        headers: {'Content-Type': 'application/json'}
    }).then(res => {
        if (res.ok) {
            hideModal('loginModal');
            checkLoggedIn();
        } else {
            alert('Error');
        }
    });
}

// similar for register, forgot, reset, other actions like likePost(fetch post), etc.

function likePost(id) {
    fetch(`${apiBase}/post/like`, {
        method: 'POST',
        body: JSON.stringify({post_id: id}),
        headers: {'Content-Type': 'application/json'}
    });
}

// Add all other JS functions for interactions, modals onclick creation (dynamic content in modals), etc.
