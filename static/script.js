// static/script.js (fully adjusted for frontend functionality)

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
        } else {
            res.json().then(user => {
                sessionStorage.setItem('user_id', user.id);
                sessionStorage.setItem('is_admin', user.is_admin);
                if (user.is_admin) document.getElementById('adminBtn').style.display = 'block';
                applyTheme(user.theme);
                loadView('home');
            });
        }
    })
    .catch(() => showModal('loginModal'));
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
    // Placeholder for download with watermark
    const a = document.createElement('a');
    a.href = url;
    a.download = 'reel.mp4';
    a.click();
    // For watermark, would need canvas or server-side
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
    loadFollowers();  // Default
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
    // Client-side remove for now
    alert('Removed from suggested');
}

function showDropdown(id, type) {
    // Placeholder for dropdown: unfollow, block
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
    loadChats();  // Default
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
    // Load header: back, profile, dropdown
    chatHeader.innerHTML = `
        <button onclick="hideModal('chatModal')"><i class="fa fa-arrow-left"></i></button>
        <img src="profile_pic" class="small-circle">
        <span>Name</span>
        <button onclick="showChatDropdown(${chat_id}, ${is_group})"><i class="fa fa-ellipsis-v"></i></button>
    `;
    // Fetch name/pic
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
    // Load custom: nickname, wallpaper
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
    // Dropdown: customize name, change wallpaper, search, view user/group, disappearing, block, report
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
    // Placeholder: upload and set
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
            // Display in modal or something
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
        // Set for future messages, existing handled in backend
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
        fetch(`${apiBase}/post/report`, {  // Reuse report for chat
            method: 'POST',
            body: JSON.stringify({ post_id: chat_id, reason }),  // Misuse post_id for chat_id
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

// Update the loadProfile function
function loadProfile(userId) {
    fetch(`${apiBase}/user/${userId}`, { credentials: 'include' })
    .then(res => {
        if (res.status === 403) {
            alert('This profile is private');
            return;
        }
        return res.json();
    })
    .then(user => {
        if (!user) return;
        
        const content = document.getElementById('content');
        const isOwnProfile = userId == sessionStorage.getItem('user_id');
        const isGroup = user.hasOwnProperty('creator_id'); // Check if it's a group
        
        if (isGroup) {
            renderGroupProfile(user);
            return;
        }
        
        // Count friends, followers, following (these would need backend endpoints)
        const friendsCount = 0; // Would come from API
        const followersCount = 0; // Would come from API
        const followingCount = 0; // Would come from API
        const postsCount = 0; // Would come from API
        const likesCount = 0; // Would come from API
        
        content.innerHTML = `
            <div class="profile-header">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div style="position: relative;">
                        <img src="${user.profile_pic_url || '/static/default.jpg'}" class="profile-pic-large">
                        ${isOwnProfile ? `
                            <label for="profilePhotoUpload" class="camera-button">
                                <i class="fa fa-camera"></i>
                            </label>
                            <input id="profilePhotoUpload" type="file" accept="image/*" style="display: none;" onchange="uploadProfilePhoto(this)">
                        ` : ''}
                    </div>
                    <div style="margin-left: 15px;">
                        <h2>${user.real_name || 'Anonymous'}</h2>
                        <p><strong>Unique Key: ${user.unique_key || 'N/A'}</strong></p>
                        <div class="profile-stats">
                            <span>Friends: ${friendsCount}</span>
                            <span>Followers: ${followersCount}</span>
                            <span>Following: ${followingCount}</span>
                            <span>Posts: ${postsCount}</span>
                            <span>Likes: ${likesCount}</span>
                        </div>
                        <div class="profile-actions">
                            ${isOwnProfile ? `
                                <button onclick="showModal('profileEditModal')">Edit Profile</button>
                                <button onclick="shareProfile()">Share Profile</button>
                            ` : `
                                <button onclick="followUser(${userId})">Follow</button>
                                <button onclick="messageUser(${userId})">Message</button>
                            `}
                        </div>
                    </div>
                </div>
                
                ${user.bio ? `<p class="profile-bio">${user.bio}</p>` : ''}
                
                ${!isOwnProfile ? `
                    <div class="mutual-friends">
                        <p>Mutual friends: User1, User2, User3</p>
                    </div>
                ` : ''}
                
                <div class="profile-info">
                    ${user.username ? `<p><strong>Username:</strong> ${user.username}</p>` : ''}
                    ${user.dob ? `<p><strong>Date of Birth:</strong> ${user.dob}</p>` : ''}
                    ${user.gender ? `<p><strong>Gender:</strong> ${user.gender}</p>` : ''}
                    ${user.pronouns ? `<p><strong>Pronouns:</strong> ${user.pronouns}</p>` : ''}
                    ${user.work ? `<p><strong>Work:</strong> ${user.work}</p>` : ''}
                    ${user.education ? `<p><strong>Education:</strong> ${user.education}</p>` : ''}
                    ${user.places ? `<p><strong>Places:</strong> ${user.places}</p>` : ''}
                    ${user.relationship ? `<p><strong>Relationship:</strong> ${user.relationship}</p>` : ''}
                    ${user.spouse ? `<p><strong>Spouse/Partner:</strong> ${user.spouse}</p>` : ''}
                    ${user.email ? `<p><strong>Email:</strong> ${user.email}</p>` : ''}
                    ${user.phone ? `<p><strong>Phone:</strong> ${user.phone}</p>` : ''}
                </div>
            </div>
            
            <div class="profile-nav">
                <button onclick="loadUserPosts(${userId})"><i class="fa fa-image"></i> Posts</button>
                <button onclick="loadUserReels(${userId})"><i class="fa fa-video"></i> Reels</button>
                ${isOwnProfile ? `
                    <button onclick="loadLockedPosts()"><i class="fa fa-lock"></i> Locked</button>
                    <button onclick="loadSavedPosts()"><i class="fa fa-bookmark"></i> Saved</button>
                    <button onclick="loadReposts()"><i class="fa fa-retweet"></i> Reposts</button>
                    <button onclick="loadLikedContent()"><i class="fa fa-heart"></i> Liked</button>
                ` : ''}
            </div>
            
            <div id="profileContent"></div>
        `;
        
        loadUserPosts(userId);  // Default
        
        if (isOwnProfile) {
            fillProfileEdit(user);
            // Populate day dropdown
            const daySelect = document.getElementById('editDobDay');
            for (let i = 1; i <= 31; i++) {
                const option = document.createElement('option');
                option.value = i;
                option.textContent = i;
                daySelect.appendChild(option);
            }
        }
    });
}

// Add function to render group profile
function renderGroupProfile(group) {
    const content = document.getElementById('content');
    const isAdmin = false; // Would need to check if current user is admin
    
    content.innerHTML = `
        <div class="group-profile-header">
            <img src="${group.profile_pic_url || '/static/default.jpg'}" class="group-pic-large">
            <h2>${group.name}</h2>
            <p>${group.members_count || 0} members</p>
            
            <div class="group-actions">
                <button onclick="messageGroup(${group.id})">Message</button>
                <button onclick="addToGroup(${group.id})">Add</button>
            </div>
            
            <div class="group-link">
                <p>Group Link: ${window.location.origin}/group/${group.link}</p>
                <button onclick="copyGroupLink('${window.location.origin}/group/${group.link}')">Copy Link</button>
            </div>
            
            <p class="group-description">${group.description || ''}</p>
            
            ${isAdmin ? `
                <div class="group-permissions">
                    <h3>Permissions</h3>
                    <label><input type="checkbox" id="allowMessages" ${group.allow_messages_nonadmin ? 'checked' : ''}> Allow non-admins to send messages</label>
                    <label><input type="checkbox" id="allowAddMembers" ${group.allow_add_nonadmin ? 'checked' : ''}> Allow non-admins to add members</label>
                    <label><input type="checkbox" id="approveNewMembers" ${group.approve_new_members ? 'checked' : ''}> Approve new members</label>
                    <button onclick="saveGroupPermissions(${group.id})">Save Permissions</button>
                </div>
            ` : ''}
            
            <div class="group-members">
                <h3>Members</h3>
                <div id="membersList"></div>
                <button onclick="loadAllMembers(${group.id})">Show All</button>
            </div>
            
            <div class="group-nav">
                <button onclick="loadGroupMedia(${group.id})"><i class="fa fa-image"></i> Media</button>
                <button onclick="loadGroupLinks(${group.id})"><i class="fa fa-link"></i> Links</button>
                <button onclick="loadGroupDocs(${group.id})"><i class="fa fa-file"></i> Documents</button>
            </div>
            
            <div class="exit-options">
                <button onclick="exitGroup(${group.id})">Exit Group</button>
                <button onclick="reportAndExit(${group.id})">Report & Exit</button>
            </div>
        </div>
        
        <div id="groupContent"></div>
    `;
    
    loadGroupMedia(group.id);  // Default
}

// Add function to toggle spouse field based on relationship status
function toggleSpouseField() {
    const relationship = document.getElementById('editRelationship').value;
    const spouseField = document.getElementById('editSpouse');
    spouseField.style.display = (relationship === 'married' || relationship === 'engaged') ? 'block' : 'none';
}

// Add function to preview profile photo
function previewProfilePhoto(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('profilePreview').src = e.target.result;
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// Add function to upload profile photo
function uploadProfilePhoto(input) {
    if (input.files && input.files[0]) {
        const formData = new FileReader();
        formData.append('file', input.files[0]);
        
        fetch(`${apiBase}/upload`, { 
            method: 'POST', 
            body: formData, 
            credentials: 'include' 
        })
        .then(res => res.json())
        .then(data => {
            // Update profile with new photo URL
            fetch(`${apiBase}/user/update`, {
                method: 'POST',
                body: JSON.stringify({ profile_pic_url: data.url }),
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            }).then(() => {
                loadProfile(sessionStorage.getItem('user_id'));
            });
        });
    }
}

// Add function to share profile
function shareProfile() {
    const profileLink = `${window.location.origin}/profile/${sessionStorage.getItem('user_id')}`;
    
    // Show modal with options to share
    showModal('shareProfileModal');
    document.getElementById('shareProfileLink').value = profileLink;
    
    // Also load friends list to suggest sharing
    fetch(`${apiBase}/friends/friends`, { credentials: 'include' })
    .then(res => res.json())
    .then(friends => {
        const friendsList = document.getElementById('shareFriendsList');
        friendsList.innerHTML = '';
        
        friends.forEach(friend => {
            const item = document.createElement('div');
            item.innerHTML = `
                <input type="checkbox" id="friend-${friend.id}" value="${friend.id}">
                <label for="friend-${friend.id}">${friend.real_name} (@${friend.username})</label>
            `;
            friendsList.appendChild(item);
        });
    });
}

// Add function to copy group link
function copyGroupLink(link) {
    navigator.clipboard.writeText(link).then(() => {
        alert('Link copied to clipboard');
    });
}

// Update the fillProfileEdit function
function fillProfileEdit(user) {
    document.getElementById('editRealName').value = user.real_name || '';
    document.getElementById('editUsername').value = user.username || '';
    document.getElementById('editBio').value = user.bio || '';
    
    // Set basic info
    if (user.dob) {
        const dobParts = user.dob.split('-');
        if (dobParts.length === 3) {
            document.getElementById('editDobDay').value = parseInt(dobParts[2]);
            document.getElementById('editDobMonth').value = parseInt(dobParts[1]);
            document.getElementById('editDobYear').value = parseInt(dobParts[0]);
        }
    }
    
    document.getElementById('editGender').value = user.gender || '';
    document.getElementById('editPronouns').value = user.pronouns || '';
    
    // Set work & education
    document.getElementById('editWork').value = user.work || '';
    document.getElementById('editUniversity').value = user.education || ''; // Using university field for education
    // Note: You might need to adjust this based on your database structure
    
    // Set location
    document.getElementById('editLocation').value = user.places || '';
    
    // Set contact info
    document.getElementById('editPhone').value = user.phone || '';
    document.getElementById('editEmail').value = user.email || '';
    // Social link and website would need to be added to the user model
    
    // Set relationship
    document.getElementById('editRelationship').value = user.relationship || '';
    document.getElementById('editSpouse').value = user.spouse || '';
    toggleSpouseField();
    
    // Set profile preview
    if (user.profile_pic_url) {
        document.getElementById('profilePreview').src = user.profile_pic_url;
    }
}

// Update the updateProfile function
function updateProfile() {
    // Get all form values
    const day = document.getElementById('editDobDay').value;
    const month = document.getElementById('editDobMonth').value;
    const year = document.getElementById('editDobYear').value;
    const dob = year && month && day ? `${year}-${month}-${day}` : '';
    
    const data = {
        real_name: document.getElementById('editRealName').value,
        username: document.getElementById('editUsername').value,
        bio: document.getElementById('editBio').value,
        dob: dob,
        gender: document.getElementById('editGender').value,
        pronouns: document.getElementById('editPronouns').value,
        work: document.getElementById('editWork').value,
        education: document.getElementById('editUniversity').value, // Using university for education
        places: document.getElementById('editLocation').value,
        phone: document.getElementById('editPhone').value,
        email: document.getElementById('editEmail').value,
        relationship: document.getElementById('editRelationship').value,
        spouse: document.getElementById('editSpouse').value,
        // Add social_link and website if you add those fields to the user model
    };
    
    fetch(`${apiBase}/user/update`, {
        method: 'POST',
        body: JSON.stringify(data),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(res => {
        if (res.ok) {
            hideModal('profileEditModal');
            loadProfile(sessionStorage.getItem('user_id'));
        } else {
            res.json().then(data => alert(data.error));
        }
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
    // Fetch posts for user, render similar to feed
    // Placeholder
    document.getElementById('profileContent').innerHTML = 'Posts...';
}

function loadUserReels(userId) {
    // Similar
    document.getElementById('profileContent').innerHTML = 'Reels...';
}

function loadUserStories(userId) {
    // Similar
    document.getElementById('profileContent').innerHTML = 'Stories...';
}

function loadSavedPosts() {
    // Fetch saves
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
    .then(() => location.reload());
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
    loadAdminUsers();  // Default
}

function loadAdminUsers() {
    fetch(`${apiBase}/admin/users`, { credentials: 'include' })
    .then(res => res.json())
    .then(users => {
        const adminContent = document.getElementById('adminContent');
        adminContent.innerHTML = '';
        users.forEach(user => {
            const item = document.createElement('div');
            item.innerHTML = `
                ${user.username} - ${user.real_name}
                <button onclick="deleteUser(${user.id})">Delete</button>
                <button onclick="banUser(${user.id})">Ban</button>
                <button onclick="warnUser(${user.id})">Warn</button>
            `;
            adminContent.appendChild(item);
        });
    });
}

function deleteUser(id) {
    if (confirm('Delete?')) {
        fetch(`${apiBase}/admin/user/delete`, {
            method: 'POST',
            body: JSON.stringify({ user_id: id }),
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        }).then(() => loadAdminUsers());
    }
}

function banUser(id) {
    const duration = prompt('Duration (days or forever):');
    if (duration) {
        fetch(`${apiBase}/admin/user/ban`, {
            method: 'POST',
            body: JSON.stringify({ user_id: id, duration }),
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        }).then(() => alert('Banned'));
    }
}

function warnUser(id) {
    const message = prompt('Warning message:');
    if (message) {
        fetch(`${apiBase}/admin/warning`, {
            method: 'POST',
            body: JSON.stringify({ user_id: id, message }),
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        }).then(() => alert('Sent'));
    }
}

function loadAdminGroups() {
    // Similar to users
    document.getElementById('adminContent').innerHTML = 'Groups...';
}

function loadAdminReports() {
    // Similar
    document.getElementById('adminContent').innerHTML = 'Reports...';
}

function loadAdminInbox() {
    // Similar to inbox
    document.getElementById('adminContent').innerHTML = 'Admin Inbox...';
}

function login() {
    const identifier = document.getElementById('loginIdentifier').value;
    const password = document.getElementById('loginPassword').value;
    fetch(`${apiBase}/login`, {
        method: 'POST',
        body: JSON.stringify({ identifier, password }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(res => {
        if (res.ok) {
            hideModal('loginModal');
            checkLoggedIn();
        } else res.json().then(data => alert(data.error));
    });
}

function register() {
    const username = document.getElementById('regUsername').value;
    const password = document.getElementById('regPassword').value;
    fetch(`${apiBase}/register`, {
        method: 'POST',
        body: JSON.stringify({ username, password }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(res => {
        if (res.ok) res.json().then(data => {
            alert('Registered! Key: ' + data.unique_key);
            hideModal('registerModal');
            checkLoggedIn();
        });
        else res.json().then(data => alert(data.error));
    });
}

function forgot() {
    const username = document.getElementById('forgotUsername').value;
    const unique_key = document.getElementById('forgotKey').value;
    fetch(`${apiBase}/forgot`, {
        method: 'POST',
        body: JSON.stringify({ username, unique_key }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(res => {
        if (res.ok) {
            hideModal('forgotModal');
            setTimeout(() => showModal('resetModal'), 5000);
        } else res.json().then(data => alert(data.error));
    });
}

function resetPassword() {
    const password = document.getElementById('newPassword').value;
    fetch(`${apiBase}/reset_password`, {
        method: 'POST',
        body: JSON.stringify({ password }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(res => {
        if (res.ok) {
            hideModal('resetModal');
            showModal('loginModal');
        } else res.json().then(data => alert(data.error));
    });
}

function createPost() {
    const type = document.getElementById('addType').value;
    const description = document.getElementById('addDescription').value;
    const file = document.getElementById('addMedia').files[0];
    const formData = new FormData();
    formData.append('file', file);
    fetch(`${apiBase}/upload`, { method: 'POST', body: formData, credentials: 'include' })
    .then(res => res.json())
    .then(data => {
        fetch(`${apiBase}/post/create`, {
            method: 'POST',
            body: JSON.stringify({ type, description, media_url: data.url }),
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        }).then(() => {
            hideModal('addModal');
            loadView('home');
        });
    });
}

function likePost(id) {
    fetch(`${apiBase}/post/like`, {
        method: 'POST',
        body: JSON.stringify({ post_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => alert('Liked/Unliked'));
}

function showCommentModal(id) {
    showModal('commentModal');
    sessionStorage.setItem('currentPostId', id);
    fetch(`${apiBase}/post/comments/${id}`, { credentials: 'include' })
    .then(res => res.json())
    .then(comments => {
        const commentList = document.getElementById('commentList');
        commentList.innerHTML = '';
        comments.forEach(comment => {
            const item = document.createElement('div');
            item.textContent = `${comment.real_name}: ${comment.text}`;
            commentList.appendChild(item);
        });
    });
}

function addComment() {
    const text = document.getElementById('commentText').value;
    const post_id = sessionStorage.getItem('currentPostId');
    fetch(`${apiBase}/post/comment`, {
        method: 'POST',
        body: JSON.stringify({ post_id, text }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => {
        document.getElementById('commentText').value = '';
        showCommentModal(post_id);
    });
}

function sharePost(id) {
    alert('Share link: /post/' + id);
}

function followUser(id) {
    fetch(`${apiBase}/follow/request`, {
        method: 'POST',
        body: JSON.stringify({ target_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => alert('Requested'));
}

function savePost(id) {
    fetch(`${apiBase}/post/save`, {
        method: 'POST',
        body: JSON.stringify({ post_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => alert('Saved/Unsaved'));
}

function repostPost(id) {
    fetch(`${apiBase}/post/repost`, {
        method: 'POST',
        body: JSON.stringify({ post_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => alert('Reposted'));
}

function reportPost(id) {
    const reason = prompt('Reason:');
    if (reason) {
        fetch(`${apiBase}/post/report`, {
            method: 'POST',
            body: JSON.stringify({ post_id: id, reason }),
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        }).then(() => alert('Reported'));
    }
}

function hidePost(id) {
    fetch(`${apiBase}/post/hide`, {
        method: 'POST',
        body: JSON.stringify({ post_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => alert('Hidden'));
}

function toggleNotifications(user_id) {
    fetch(`${apiBase}/post/subscribe`, {
        method: 'POST',
        body: JSON.stringify({ post_user_id: user_id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => alert('Toggled'));
}

function blockUser(id) {
    fetch(`${apiBase}/block`, {
        method: 'POST',
        body: JSON.stringify({ target_id: id }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => alert('Blocked'));
}

function messageUser(id) {
    showChatModal(id, false);
}

function createGroup() {
    const name = document.getElementById('groupName').value;
    const description = document.getElementById('groupDescription').value;
    // Upload pic if any
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

function editGroup() {
    const group_id = sessionStorage.getItem('currentGroupId');
    const name = document.getElementById('editGroupName').value;
    const description = document.getElementById('editGroupDescription').value;
    fetch(`${apiBase}/group/edit`, {
        method: 'POST',
        body: JSON.stringify({ group_id, name, description }),
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    }).then(() => {
        hideModal('groupEditModal');
        showChatModal(group_id, true);
    });
}

function report() {
    // Generic report
    alert('Reported');
}
