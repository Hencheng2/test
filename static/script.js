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
let currentView = 'login';
let currentStoryIndex = 0;
let stories = [];

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
    window.addEventListener('scroll', handleInfiniteScroll);
    document.getElementById('searchInput')?.addEventListener('input', loadSearchResults);
    document.getElementById('friendsSearch')?.addEventListener('input', loadFriendsSearch);
    // Add event listeners for forms
    document.getElementById('loginForm')?.addEventListener('submit', (e) => { e.preventDefault(); login(); });
    document.getElementById('registerForm')?.addEventListener('submit', (e) => { e.preventDefault(); register(); });
    document.getElementById('forgotForm')?.addEventListener('submit', (e) => { e.preventDefault(); forgot(); });
    document.getElementById('resetForm')?.addEventListener('submit', (e) => { e.preventDefault(); resetPassword(); });
    document.getElementById('addForm')?.addEventListener('submit', (e) => { e.preventDefault(); createPost(); });
    document.getElementById('profileEditForm')?.addEventListener('submit', (e) => { e.preventDefault(); updateProfile(); });
    document.getElementById('changePasswordForm')?.addEventListener('submit', (e) => { e.preventDefault(); changePassword(); });
    document.getElementById('groupCreateForm')?.addEventListener('submit', (e) => { e.preventDefault(); createGroup(); });
    document.getElementById('groupEditForm')?.addEventListener('submit', (e) => { e.preventDefault(); editGroup(); });
    document.getElementById('chatForm')?.addEventListener('submit', (e) => { e.preventDefault(); sendChat(); });
    document.getElementById('commentForm')?.addEventListener('submit', (e) => { e.preventDefault(); addComment(); });
    document.getElementById('reportForm')?.addEventListener('submit', (e) => { e.preventDefault(); report(); });
});

function checkLoggedIn() {
    fetch(`${apiBase}/user/me`, { credentials: 'include' })
    .then(res => {
        if (res.status === 401) {
            showModal('loginModal');
            document.getElementById('navBar').style.display = 'none';
            document.getElementById('content').style.display = 'none';
        } else {
            res.json().then(user => {
                sessionStorage.setItem('user_id', user.id);
                sessionStorage.setItem('is_admin', user.is_admin);
                document.getElementById('navBar').style.display = 'flex';
                document.getElementById('content').style.display = 'block';
                if (user.is_admin) document.getElementById('adminBtn').style.display = 'block';
                applyTheme(user.theme);
                hideModal('loginModal');
                loadView('home');
            });
        }
    })
    .catch(() => {
        showModal('loginModal');
        document.getElementById('navBar').style.display = 'none';
        document.getElementById('content').style.display = 'none';
    });
}

function applyTheme(theme) {
    document.body.classList.toggle('dark', theme === 'dark');
}

function loadView(view, param = null) {
    currentView = view;
    currentPage = 1;
    const content = document.getElementById('content');
    content.innerHTML = '';
    if (view === 'home') loadHome();
    else if (view === 'reels') loadReels();
    else if (view === 'friends') loadFriends();
    else if (view === 'inbox') loadInbox();
    else if (view === 'profile') loadProfile(param || sessionStorage.getItem('user_id'));
    else if (view === 'search') loadSearch();
    else if (view === 'notifications') loadNotifications();
    else if (view === 'menu') loadMenu();
    else if (view === 'admin') loadAdmin();
}

function handleInfiniteScroll() {
    if (loading || (window.innerHeight + window.scrollY < document.body.offsetHeight - 100)) return;
    loading = true;
    currentPage++;
    if (currentView === 'home') loadMorePosts();
    else if (currentView === 'reels') loadMoreReels();
    // Add for other views if needed
}

function loadMorePosts() {
    fetch(`${apiBase}/posts/feed?page=${currentPage}`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => {
        if (data.length > 0) renderPosts(data, true);
        loading = false;
    });
}

function loadMoreReels() {
    fetch(`${apiBase}/reels?page=${currentPage}`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => {
        if (data.length > 0) renderReels(data, true);
        loading = false;
    });
}

function loadHome() {
    const content = document.getElementById('content');
    fetch(`${apiBase}/stories`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => {
        stories = data;
        const storiesDiv = document.createElement('div');
        storiesDiv.classList.add('stories');
        stories.forEach((story, index) => {
            const circle = document.createElement('div');
            circle.classList.add('story-circle');
            circle.style.backgroundImage = `url(${story.profile_pic_url || '/static/default.jpg'})`;
            circle.onclick = () => showStory(index);
            const username = document.createElement('p');
            username.textContent = story.username;
            circle.appendChild(username);
            storiesDiv.appendChild(circle);
        });
        content.appendChild(storiesDiv);
    });
    fetch(`${apiBase}/posts/feed?page=1`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => renderPosts(data));
}

function renderPosts(posts, append = false) {
    const content = document.getElementById('content');
    if (!append) content.innerHTML = '';
    posts.forEach(post => {
        const postDiv = document.createElement('div');
        postDiv.classList.add('post');
        postDiv.innerHTML = `
            <img src="${post.profile_pic_url || '/static/default.jpg'}" class="small-circle">
            <span>${post.real_name || 'Anonymous'} (@${post.username}) - ${new Date(post.timestamp).toLocaleString()}</span>
            <p>${post.description || ''}</p>
            ${post.media_url ? `<img src="${post.media_url}" alt="post media">` : ''}
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
                ${post.user_id != sessionStorage.getItem('user_id') ? `<button onclick="toggleNotifications(${post.user_id})">Turn on notifications</button>` : ''}
                ${post.user_id != sessionStorage.getItem('user_id') ? `<button onclick="blockUser(${post.user_id})">Block</button>` : ''}
            </div>
        `;
        content.appendChild(postDiv);
    });
}

function loadReels() {
    const content = document.getElementById('content');
    content.innerHTML = '';
    fetch(`${apiBase}/reels?page=1`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => renderReels(data));
}

function renderReels(reels, append = false) {
    const content = document.getElementById('content');
    if (!append) content.innerHTML = '';
    reels.forEach(reel => {
        const reelDiv = document.createElement('div');
        reelDiv.classList.add('reel');
        reelDiv.innerHTML = `
            <video src="${reel.media_url}" class="reel-video" loop autoplay></video>
            <div class="reel-overlay">
                <span>${reel.real_name || 'Anonymous'} (@${reel.username})</span>
                <p>${reel.description || ''}</p>
                <div class="reel-buttons">
                    <button onclick="likePost(${reel.id})">Like</button>
                    <button onclick="showCommentModal(${reel.id})">Comment</button>
                    <button onclick="sharePost(${reel.id})">Share</button>
                    ${reel.user_id != sessionStorage.getItem('user_id') ? `<button onclick="followUser(${reel.user_id})">Follow</button>` : ''}
                    <button onclick="savePost(${reel.id})">Save</button>
                    ${reel.user_id != sessionStorage.getItem('user_id') ? `<button onclick="repostPost(${reel.id})">Repost</button>` : ''}
                    <button onclick="downloadReel('${reel.media_url}')">Download</button>
                </div>
            </div>
        `;
        reelDiv.addEventListener('click', togglePlayPause);
        content.appendChild(reelDiv);
    });
}

function togglePlayPause(e) {
    const video = e.currentTarget.querySelector('video');
    if (video.paused) video.play();
    else video.pause();
}

function downloadReel(url) {
    const a = document.createElement('a');
    a.href = url;
    a.download = 'reel.mp4';
    a.click();
}

function showStory(index) {
    currentStoryIndex = index;
    const modal = document.getElementById('storyModal');
    updateStoryView();
    showModal('storyModal');
    let touchStartX = 0, touchEndX = 0, touchStartY = 0, touchEndY = 0;
    let holdTimer;
    modal.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
        holdTimer = setTimeout(() => pauseStory(), 500);
    });
    modal.addEventListener('touchend', e => {
        clearTimeout(holdTimer);
        touchEndX = e.changedTouches[0].screenX;
        touchEndY = e.changedTouches[0].screenY;
        if (touchEndX < touchStartX - 50) nextStory();
        else if (touchEndX > touchStartX + 50) prevStory();
        if (touchEndY > touchStartY + 50) hideModal('storyModal');
        resumeStory();
    });
}

function updateStoryView() {
    const storyView = document.getElementById('storyView');
    const story = stories[currentStoryIndex];
    storyView.innerHTML = story.media_url.endsWith('.mp4') ? `<video src="${story.media_url}" autoplay loop></video>` : `<img src="${story.media_url}">`;
    storyView.querySelector('video, img').style.width = '100%';
    storyView.querySelector('video, img').style.height = '100vh';
    storyView.querySelector('video, img').style.objectFit = 'contain';
}

function nextStory() {
    if (currentStoryIndex < stories.length - 1) {
        currentStoryIndex++;
        updateStoryView();
    }
}

function prevStory() {
    if (currentStoryIndex > 0) {
        currentStoryIndex--;
        updateStoryView();
    }
}

function pauseStory() {
    const video = document.getElementById('storyView').querySelector('video');
    if (video) video.pause();
}

function resumeStory() {
    const video = document.getElementById('storyView').querySelector('video');
    if (video) video.play();
}

function loadFriends() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <input id="friendsSearch" type="text" placeholder="Search users">
        <div id="friendsNav">
            <button onclick="loadFollowers()">Followers</button>
            <button onclick="loadFollowing()">Following</button>
            <button onclick="loadFriendsList()">Friends</button>
            <button onclick="loadRequests()">Requests</button>
            <button onclick="loadSuggested()">Suggested</button>
        </div>
        <div id="friendsList"></div>
    `;
    loadFollowers();
}

function loadFollowers() {
    fetch(`${apiBase}/friends/followers`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => renderFriendsList(data, 'followers'));
}

function loadFollowing() {
    fetch(`${apiBase}/friends/following`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => renderFriendsList(data, 'following'));
}

function loadFriendsList() {
    fetch(`${apiBase}/friends/friends`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => renderFriendsList(data, 'friends'));
}

function loadRequests() {
    fetch(`${apiBase}/friends/requests`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => renderFriendsList(data, 'requests'));
}

function loadSuggested() {
    fetch(`${apiBase}/friends/suggested`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => renderFriendsList(data, 'suggested'));
}

function renderFriendsList(users, type) {
    const list = document.getElementById('friendsList');
    list.innerHTML = '';
    users.forEach(user => {
        const item = document.createElement('div');
        item.classList.add('friends-item');
        item.innerHTML = `
            <img src="${user.profile_pic_url || '/static/default.jpg'}" class="small-circle">
            <span>${user.real_name || 'Anonymous'} (@${user.username})<br><small>${user.mutual} mutual</small></span>
        `;
        const buttons = document.createElement('div');
        if (type === 'followers') {
            buttons.innerHTML = `
                <button onclick="messageUser(${user.id})"><i class="fa fa-message"></i></button>
                <button onclick="blockUser(${user.id})">Block</button>
            `;
        } else if (type === 'following' || type === 'friends') {
            buttons.innerHTML = `
                <button onclick="messageUser(${user.id})"><i class="fa fa-message"></i></button>
                <button onclick="showDropdown(${user.id}, '${type}')"><i class="fa fa-ellipsis-v"></i></button>
            `;
        } else if (type === 'requests') {
            buttons.innerHTML = `
                <button onclick="acceptRequest(${user.id})">Accept</button>
                <button onclick="declineRequest(${user.id})">Decline</button>
                <button onclick="blockUser(${user.id})">Block</button>
            `;
        } else if (type === 'suggested') {
            buttons.innerHTML = `
                <button onclick="followUser(${user.id})">Follow</button>
                <button onclick="removeSuggested(${user.id})">Remove</button>
                <button onclick="blockUser(${user.id})">Block</button>
            `;
        }
        item.appendChild(buttons);
        item.onclick = () => loadProfile(user.id);
        list.appendChild(item);
    });
}

function loadFriendsSearch() {
    const query = document.getElementById('friendsSearch').value;
    if (query) {
        fetch(`${apiBase}/search?query=${query}`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => renderFriendsList(data.users, 'search'));
    }
}

function acceptRequest(id) {
    fetch(`${apiBase}/follow/accept`, {
        method: 'POST',
        body: JSON.stringify({ from_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => loadRequests());
}

function declineRequest(id) {
    fetch(`${apiBase}/follow/decline`, {
        method: 'POST',
        body: JSON.stringify({ from_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => loadRequests());
}

function removeSuggested(id) {
    alert('Removed from suggested');
}

function showDropdown(id, type) {
    if (confirm('Unfollow?')) unfollowUser(id);
    else if (confirm('Block?')) blockUser(id);
}

function unfollowUser(id) {
    fetch(`${apiBase}/follow/unfollow`, {
        method: 'POST',
        body: JSON.stringify({ target_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => loadView('friends'));
}

function loadInbox() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div id="inboxNav">
            <button onclick="loadChats()">Chats</button>
            <button onclick="loadGroupChats()">Groups</button>
        </div>
        <div id="inboxList"></div>
    `;
    loadChats();
}

function loadChats() {
    fetch(`${apiBase}/inbox/chats`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => renderInboxList(data, false));
}

function loadGroupChats() {
    fetch(`${apiBase}/inbox/groups`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => renderInboxList(data, true));
}

function renderInboxList(items, isGroup) {
    const list = document.getElementById('inboxList');
    list.innerHTML = '';
    items.forEach(item => {
        const chatItem = document.createElement('div');
        chatItem.classList.add('chat-item');
        chatItem.innerHTML = `
            <img src="${item.profile_pic_url || '/static/default.jpg'}" class="small-circle">
            <span>${item.real_name || item.name} (${item.username || ''})<br><small>${item.last_message}</small></span>
            <small>${new Date(item.last_timestamp).toLocaleTimeString()}</small>
            ${item.unread > 0 ? `<span class="unread">${item.unread}</span>` : ''}
        `;
        chatItem.onclick = () => showChatModal(item.chat_id, isGroup);
        list.appendChild(chatItem);
    });
}

function showChatModal(chat_id, is_group) {
    showModal('chatModal');
    const chatHeader = document.getElementById('chatHeader');
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = 'Loading...';
    fetch(`${apiBase}/messages/${chat_id}?is_group=${is_group}`, { credentials: 'include' })
    .then(res => res.json())
    .then(messages => {
        chatMessages.innerHTML = '';
        messages.forEach(msg => {
            const msgDiv = document.createElement('div');
            msgDiv.classList.add(msg.sender_id == sessionStorage.getItem('user_id') ? 'sent' : 'received');
            msgDiv.innerHTML = `
                <p>${msg.text || ''}</p>
                ${msg.media_url ? `<img src="${msg.media_url}">` : ''}
                <small>${new Date(msg.timestamp).toLocaleString()}</small>
            `;
            chatMessages.appendChild(msgDiv);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
    chatHeader.innerHTML = `
        <button onclick="hideModal('chatModal')"><i class="fa fa-arrow-left"></i></button>
        <img src="profile_pic" class="small-circle">
        <span>Name</span>
        <button onclick="showChatDropdown(${chat_id}, ${is_group})"><i class="fa fa-ellipsis-v"></i></button>
    `;
    if (!is_group) {
        fetch(`${apiBase}/user/${chat_id}`, { credentials: 'include' })
        .then(res => res.json())
        .then(user => {
            chatHeader.querySelector('img').src = user.profile_pic_url || '/static/default.jpg';
            chatHeader.querySelector('span').textContent = user.real_name + ' (@' + user.username + ')';
        });
    } else {
        fetch(`${apiBase}/group/${chat_id}`, { credentials: 'include' })
        .then(res => res.json())
        .then(group => {
            chatHeader.querySelector('img').src = group.profile_pic_url || '/static/default.jpg';
            chatHeader.querySelector('span').textContent = group.name;
        });
    }
    fetch(`${apiBase}/chat/custom?chat_id=${chat_id}&is_group=${is_group}`, { credentials: 'include' })
    .then(res => res.json())
    .then(custom => {
        if (custom.nickname) chatHeader.querySelector('span').textContent = custom.nickname;
        if (custom.wallpaper_url) document.getElementById('chatModal').style.backgroundImage = `url(${custom.wallpaper_url})`;
    });
    document.getElementById('chatInput').focus();
    sessionStorage.setItem('currentChatId', chat_id);
    sessionStorage.setItem('currentIsGroup', is_group);
}

function showChatDropdown(chat_id, is_group) {
    showModal('chatDropdownModal');
    const dropdownContent = document.getElementById('chatDropdownContent');
    dropdownContent.innerHTML = `
        <button onclick="customizeName(${chat_id}, ${is_group})">Customize Name</button>
        <button onclick="changeWallpaper(${chat_id}, ${is_group})">Change Wallpaper</button>
        <button onclick="searchChat(${chat_id}, ${is_group})">Search</button>
        <button onclick="viewProfile(${chat_id}, ${is_group})">View ${is_group ? 'Group' : 'User'}</button>
        <button onclick="toggleDisappearing(${chat_id}, ${is_group})">Disappearing Messages</button>
        <button onclick="blockChat(${chat_id}, ${is_group})">Block</button>
        <button onclick="reportChat(${chat_id}, ${is_group})">Report</button>
    `;
}

function customizeName(chat_id, is_group) {
    const name = prompt('New name:');
    if (name) {
        fetch(`${apiBase}/chat/customize`, {
            method: 'POST',
            body: JSON.stringify({ chat_id, is_group, nickname: name }),
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        }).then(() => showChatModal(chat_id, is_group));
    }
}

function changeWallpaper(chat_id, is_group) {
    const url = prompt('Wallpaper URL:');
    if (url) {
        fetch(`${apiBase}/chat/customize`, {
            method: 'POST',
            body: JSON.stringify({ chat_id, is_group, wallpaper_url: url }),
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        }).then(() => showChatModal(chat_id, is_group));
    }
}

function searchChat(chat_id, is_group) {
    const query = prompt('Search query:');
    if (query) {
        fetch(`${apiBase}/chat/search?chat_id=${chat_id}&query=${query}&is_group=${is_group}`, { credentials: 'include' })
        .then(res => res.json())
        .then(messages => {
            alert('Found ' + messages.length + ' messages');
        });
    }
}

function viewProfile(chat_id, is_group) {
    hideModal('chatModal');
    loadView('profile', chat_id);
}

function toggleDisappearing(chat_id, is_group) {
    const after = prompt('Disappearing after (off, 24h, 1w, 1m):');
    if (after) {
        alert('Set to ' + after);
    }
}

function blockChat(chat_id, is_group) {
    if (confirm('Block?')) {
        blockUser(chat_id);
        hideModal('chatModal');
    }
}

function reportChat(chat_id, is_group) {
    const reason = prompt('Reason:');
    if (reason) {
        fetch(`${apiBase}/post/report`, {
            method: 'POST',
            body: JSON.stringify({ post_id: chat_id, reason }),
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        }).then(() => alert('Reported'));
    }
}

function sendChat() {
    const text = document.getElementById('chatInput').value;
    const chat_id = sessionStorage.getItem('currentChatId');
    const is_group = sessionStorage.getItem('currentIsGroup');
    fetch(`${apiBase}/message/send`, {
        method: 'POST',
        body: JSON.stringify({ receiver_id: chat_id, text, is_group }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => {
        document.getElementById('chatInput').value = '';
        showChatModal(chat_id, is_group);
    });
}

function loadProfile(userId) {
    fetch(`${apiBase}/user/${userId}`, { credentials: 'include' })
    .then(res => res.json())
    .then(user => {
        const content = document.getElementById('content');
        content.innerHTML = `
            <img src="${user.profile_pic_url || '/static/default.jpg'}" class="profile-pic">
            <h2>${user.real_name || 'Anonymous'} (@${user.username})</h2>
            <p>${user.bio || ''}</p>
            <div id="profileNav">
                <button onclick="loadUserPosts(${userId})">Posts</button>
                <button onclick="loadUserReels(${userId})">Reels</button>
                <button onclick="loadUserStories(${userId})">Stories</button>
                <button onclick="loadSavedPosts()">Saved</button>
            </div>
            ${userId == sessionStorage.getItem('user_id') ? `<button onclick="showModal('profileEditModal')">Edit Profile</button>` : ''}
            ${userId != sessionStorage.getItem('user_id') ? `<button onclick="messageUser(${userId})">Message</button>` : ''}
            ${userId != sessionStorage.getItem('user_id') ? `<button onclick="followUser(${userId})">Follow</button>` : ''}
            ${userId != sessionStorage.getItem('user_id') ? `<button onclick="blockUser(${userId})">Block</button>` : ''}
            <div id="profileContent"></div>
        `;
        loadUserPosts(userId);
        if (userId == sessionStorage.getItem('user_id')) fillProfileEdit(user);
    });
}

function fillProfileEdit(user) {
    document.getElementById('editRealName').value = user.real_name || '';
    document.getElementById('editBio').value = user.bio || '';
}

function updateProfile() {
    const data = {
        real_name: document.getElementById('editRealName').value,
        bio: document.getElementById('editBio').value,
    };
    fetch(`${apiBase}/user/update`, {
        method: 'POST',
        body: JSON.stringify(data),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => {
        hideModal('profileEditModal');
        loadProfile(sessionStorage.getItem('user_id'));
    });
}

function changePassword() {
    const old_password = document.getElementById('oldPassword').value;
    const new_password = document.getElementById('newPasswordChange').value;
    fetch(`${apiBase}/user/change_password`, {
        method: 'POST',
        body: JSON.stringify({ old_password, new_password }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(res => {
        if (res.ok) alert('Changed');
        else res.json().then(data => alert(data.error));
    });
}

function loadUserPosts(userId) {
    document.getElementById('profileContent').innerHTML = 'Posts...';
}

function loadUserReels(userId) {
    document.getElementById('profileContent').innerHTML = 'Reels...';
}

function loadUserStories(userId) {
    document.getElementById('profileContent').innerHTML = 'Stories...';
}

function loadSavedPosts() {
    document.getElementById('profileContent').innerHTML = 'Saved...';
}

function loadSearch() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <input id="searchInput" type="text" placeholder="Search">
        <div id="searchResults"></div>
    `;
}

function loadSearchResults() {
    const query = document.getElementById('searchInput').value;
    if (query) {
        fetch(`${apiBase}/search?query=${query}`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            const results = document.getElementById('searchResults');
            results.innerHTML = '';
            data.users.forEach(user => {
                const item = document.createElement('div');
                item.innerHTML = `
                    <img src="${user.profile_pic_url || '/static/default.jpg'}" class="small-circle">
                    <span>${user.real_name} (@${user.username})</span>
                `;
                item.onclick = () => loadProfile(user.id);
                results.appendChild(item);
            });
        });
    }
}

function loadNotifications() {
    fetch(`${apiBase}/notifications`, { credentials: 'include' })
    .then(res => res.json())
    .then(notifs => {
        const content = document.getElementById('content');
        content.innerHTML = '';
        notifs.forEach(notif => {
            const item = document.createElement('div');
            item.textContent = `${notif.type}: ${notif.text || ''} from ${notif.from_user_id}`;
            content.appendChild(item);
        });
    });
}

function loadMenu() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <button onclick="showModal('settingsModal')">Settings</button>
        <button onclick="showModal('supportModal')">Support</button>
        <button onclick="logout()">Logout</button>
    `;
}

function logout() {
    fetch(`${apiBase}/logout`, { method: 'POST', credentials: 'include' })
    .then(() => {
        document.getElementById('navBar').style.display = 'none';
        document.getElementById('content').style.display = 'none';
        showModal('loginModal');
    });
}

function loadAdmin() {
    if (sessionStorage.getItem('is_admin') != 1) return;
    const content = document.getElementById('content');
    content.innerHTML = `
        <div id="adminNav">
            <button onclick="loadAdminUsers()">Users</button>
            <button onclick="loadAdminGroups()">Groups</button>
            <button onclick="loadAdminReports()">Reports</button>
            <button onclick="loadAdminInbox()">Inbox</button>
        </div>
        <div id="adminContent"></div>
    `;
    loadAdminUsers();
}

function loadAdminUsers() {
    fetch(`${apiBase}/admin/users`, { credentials: 'include' })
    .then(res => res.json())
    .then(users => {
        const adminContent = document.getElementById('adminContent');
        adminContent.innerHTML = '';
        users.forEach(user => {
            const item = document.create
