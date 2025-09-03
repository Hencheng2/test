document.addEventListener('DOMContentLoaded', () => {
    checkLoginStatus();
    setupEventListeners();
});

function checkLoginStatus() {
    fetch('/api/profile')
        .then(response => {
            if (response.ok) {
                document.querySelectorAll('.section').forEach(section => {
                    section.classList.remove('active');
                    section.style.display = 'none';
                });
                document.getElementById('home').classList.add('active');
                document.getElementById('home').style.display = 'block';
                document.querySelectorAll('.modal').forEach(modal => modal.style.display = 'none');
                loadHome();
                fetch('/api/profile').then(res => res.json()).then(data => {
                    if (data.is_admin) {
                        document.getElementById('admin-btn').style.display = 'block';
                    }
                });
            } else {
                document.querySelectorAll('.section').forEach(section => {
                    section.classList.remove('active');
                    section.style.display = 'none';
                });
                document.querySelectorAll('.modal').forEach(modal => modal.style.display = 'none');
                document.getElementById('login-modal').style.display = 'block';
            }
        })
        .catch(() => {
            document.querySelectorAll('.section').forEach(section => {
                section.classList.remove('active');
                section.style.display = 'none';
            });
            document.querySelectorAll('.modal').forEach(modal => modal.style.display = 'none');
            document.getElementById('login-modal').style.display = 'block';
        });
}

function setupEventListeners() {
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
    document.getElementById('home-btn').addEventListener('click', () => {
        fetch('/api/profile').then(response => {
            if (response.ok) loadHome();
            else showModal('login-modal');
        });
    });
    document.getElementById('reels-btn').addEventListener('click', () => {
        fetch('/api/profile').then(response => {
            if (response.ok) loadReels();
            else showModal('login-modal');
        });
    });
    document.getElementById('friends-btn').addEventListener('click', () => {
        fetch('/api/profile').then(response => {
            if (response.ok) loadFriendsTab('friends');
            else showModal('login-modal');
        });
    });
    document.getElementById('inbox-btn').addEventListener('click', () => {
        fetch('/api/profile').then(response => {
            if (response.ok) loadInboxTab('chats');
            else showModal('login-modal');
        });
    });
    document.getElementById('profile-btn').addEventListener('click', () => {
        fetch('/api/profile').then(response => {
            if (response.ok) loadProfileTab('posts');
            else showModal('login-modal');
        });
    });
    document.getElementById('search-btn').addEventListener('click', () => {
        fetch('/api/profile').then(response => {
            if (response.ok) loadSearchTab('all');
            else showModal('login-modal');
        });
    });
    document.getElementById('addto-btn').addEventListener('click', () => {
        fetch('/api/profile').then(response => {
            if (response.ok) showSection('addto');
            else showModal('login-modal');
        });
    });
    document.getElementById('notifications-btn').addEventListener('click', () => {
        fetch('/api/profile').then(response => {
            if (response.ok) loadNotifications();
            else showModal('login-modal');
        });
    });
    document.getElementById('menu-btn').addEventListener('click', () => {
        fetch('/api/profile').then(response => {
            if (response.ok) showSection('menu');
            else showModal('login-modal');
        });
    });
    document.getElementById('admin-btn').addEventListener('click', () => {
        fetch('/api/profile').then(response => {
            if (response.ok) loadAdminTab('users');
            else showModal('login-modal');
        });
    });
}

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
        section.style.display = 'none';
    });
    const section = document.getElementById(sectionId);
    section.classList.add('active');
    section.style.display = 'block';
}

function showModal(modalId) {
    document.querySelectorAll('.modal').forEach(modal => modal.style.display = 'none');
    document.getElementById(modalId).style.display = 'block';
}

function login(e) {
    e.preventDefault();
    const identifier = document.getElementById('login-identifier').value;
    const password = document.getElementById('login-password').value;
    fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier, password })
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                document.getElementById('login-modal').style.display = 'none';
                showSection('home');
                loadHome();
                if (data.is_admin) {
                    document.getElementById('admin-btn').style.display = 'block';
                }
            } else {
                alert(data.error);
            }
        });
}

function register(e) {
    e.preventDefault();
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;
    fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(`Registration successful! Your unique key is ${data.unique_key}. Save it for password recovery.`);
                document.getElementById('register-modal').style.display = 'none';
                showSection('home');
                loadHome();
            } else {
                alert(data.error);
            }
        });
}

function forgotPassword(e) {
    e.preventDefault();
    const username = document.getElementById('forgot-username').value;
    const key = document.getElementById('forgot-key').value;
    fetch('/api/forgot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, unique_key: key })
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                document.getElementById('forgot-modal').style.display = 'none';
                showModal('reset-modal');
            } else {
                alert(data.error);
            }
        });
}

function resetPassword(e) {
    e.preventDefault();
    const password = document.getElementById('reset-password').value;
    fetch('/api/reset_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(data.message);
                document.getElementById('reset-modal').style.display = 'none';
                showModal('login-modal');
            } else {
                alert(data.error);
            }
        });
}

let current_page = 1;
let loading = false;
let stories_list = [];
let current_story_index = 0;
let touch_start_x = 0;
let touch_start_y = 0;
let touch_end_x = 0;
let touch_end_y = 0;
let is_holding = false;

function loadHome() {
    showSection('home');
    fetch('/api/home')
        .then(response => response.json())
        .then(data => {
            stories_list = data.stories;
            const storiesContainer = document.getElementById('home-stories');
            storiesContainer.innerHTML = '';
            stories_list.forEach((story, index) => {
                const storyEl = document.createElement('div');
                storyEl.className = 'story-circle';
                storyEl.innerHTML = `
                    <img src="${story.media_url || '/static/default.jpg'}" alt="${story.user}">
                    <p>${story.user}</p>
                `;
                storyEl.addEventListener('click', () => {
                    current_story_index = index;
                    showStory();
                });
                storiesContainer.appendChild(storyEl);
            });
            current_page = 1;
            loading = false;
            document.getElementById('home-posts').innerHTML = '';
            loadPosts();
        })
        .catch(() => showModal('login-modal'));
}

function showStory() {
    const story = stories_list[current_story_index];
    const content = document.getElementById('story-content');
    content.innerHTML = '';
    const media = story.media_url.endswith('.mp4') ? document.createElement('video') : document.createElement('img');
    media.src = story.media_url || '/static/default.jpg';
    if (media.tagName === 'VIDEO') {
        media.autoplay = true;
        media.loop = true;
    }
    content.appendChild(media);
    showModal('story-modal');
    const modal = document.getElementById('story-modal');
    modal.addEventListener('touchstart', (e) => {
        touch_start_x = e.touches[0].clientX;
        touch_start_y = e.touches[0].clientY;
        if (media.tagName === 'VIDEO') {
            is_holding = true;
            media.pause();
        }
    });
    modal.addEventListener('touchmove', (e) => {
        touch_end_x = e.touches[0].clientX;
        touch_end_y = e.touches[0].clientY;
    });
    modal.addEventListener('touchend', (e) => {
        const delta_x = touch_end_x - touch_start_x;
        const delta_y = touch_end_y - touch_start_y;
        if (is_holding && media.tagName === 'VIDEO') {
            media.play();
            is_holding = false;
        }
        if (Math.abs(delta_x) > 50) {
            if (delta_x > 0) {
                // Swipe right - previous
                if (current_story_index > 0) {
                    current_story_index--;
                    showStory();
                }
            } else {
                // Swipe left - next
                if (current_story_index < stories_list.length - 1) {
                    current_story_index++;
                    showStory();
                }
            }
        } else if (delta_y > 50) {
            // Swipe down - close
            modal.style.display = 'none';
        }
    });
}

function loadPosts(page = 1) {
    if (loading) return;
    loading = true;
    fetch(`/api/posts?page=${page}`)
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            const postsContainer = document.getElementById('home-posts');
            data.posts.forEach(post => {
                const postEl = document.createElement('div');
                postEl.className = 'post';
                postEl.innerHTML = `
                    <div class="post-header">
                        <img src="${post.user.profile_pic || '/static/default.jpg'}" alt="${post.user.username}">
                        <div>
                            <span>${post.user.real_name}</span>
                            <span>@${post.user.username}</span>
                            <small>${new Date(post.timestamp).toLocaleDateString()}</small>
                        </div>
                    </div>
                    <p class="post-description">${post.description}</p>
                    ${post.media_url ? post.media_url.includes('.mp4') ? 
                        `<video controls src="${post.media_url}"></video>` : 
                        `<img src="${post.media_url}" alt="Post media" class="post-media">` : ''}
                    <div class="post-actions">
                        <button onclick="likePost(${post.id}, this)"><i class="fa fa-heart"></i> ${post.likes}</button>
                        <button onclick="showCommentModal(${post.id})"><i class="fa fa-comment"></i> ${post.comments}</button>
                        <button onclick="sharePost(${post.id})"><i class="fa fa-share"></i> Share</button>
                        ${post.is_own ? '' : `<button onclick="follow(${post.user.id})"><i class="fa fa-user-plus"></i> Follow</button>`}
                        <button onclick="savePost(${post.id}, this)"><i class="fa fa-bookmark"></i> Save</button>
                        ${post.is_own ? '' : `<button onclick="repost(${post.id})"><i class="fa fa-retweet"></i> Repost</button>`}
                        <span>Views: ${post.views}</span>
                        ${post.is_own ? '' : `
                            <button onclick="report(${post.id}, 'post')"><i class="fa fa-flag"></i> Report</button>
                            <button onclick="hidePost(${post.id})"><i class="fa fa-eye-slash"></i> Hide</button>
                            <button onclick="toggleNotification(${post.id})"><i class="fa fa-bell"></i> Turn on notifications</button>
                            <button onclick="blockUser(${post.user.id})"><i class="fa fa-ban"></i> Block</button>
                        `}
                    </div>
                `;
                postsContainer.appendChild(postEl);
            });
            loading = false;
            if (data.has_next) {
                current_page++;
            } else {
                window.removeEventListener('scroll', scrollListener);
            }
        })
        .catch(() => {
            loading = false;
            showModal('login-modal');
        });
}

let current_page = 1;
let loading = false;

function scrollListener() {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100 && !loading) {
        loadPosts(current_page);
    }
}

window.addEventListener('scroll', scrollListener);

function toggleNotification(postId) {
    // Stub for turning on notifications
    alert('Notifications turned on for this type of post');
}

function sharePost(postId) {
    // Stub for sharing
    alert('Post shared');
}

function blockUser(userId) {
    fetch(`/api/block/user/${userId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadHome();
        });
}

function loadReels(page = 1) {
    showSection('reels');
    fetch(`/api/reels?page=${page}`)
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            const reelsContainer = document.getElementById('reels');
            if (page === 1) reelsContainer.innerHTML = '';
            data.reels.forEach(reel => {
                const reelEl = document.createElement('div');
                reelEl.className = 'post';
                reelEl.innerHTML = `
                    <div class="post-header">
                        <img src="${reel.user.profile_pic || '/static/default.jpg'}" alt="${reel.user.username}">
                        <span>${reel.user.real_name}</span>
                    </div>
                    <video controls src="${reel.media_url}"></video>
                    <p>${reel.description}</p>
                    <div class="post-actions">
                        <button onclick="likePost(${reel.id}, this)"><i class="fa fa-heart"></i> ${reel.likes}</button>
                        <button onclick="showCommentModal(${reel.id})"><i class="fa fa-comment"></i> ${reel.comments}</button>
                        <button onclick="sharePost(${reel.id})"><i class="fa fa-share"></i> Share</button>
                        ${reel.is_own ? '' : `<button onclick="follow(${reel.user.id})"><i class="fa fa-user-plus"></i> Follow</button>`}
                        <button onclick="savePost(${reel.id}, this)"><i class="fa fa-bookmark"></i> Save</button>
                        ${reel.is_own ? '' : `<button onclick="repost(${reel.id})"><i class="fa fa-retweet"></i> Repost</button>`}
                        <span>Views: ${reel.views}</span>
                        ${reel.is_own ? '' : `
                            <button onclick="report(${reel.id}, 'reel')"><i class="fa fa-flag"></i> Report</button>
                            <button onclick="hidePost(${reel.id})"><i class="fa fa-eye-slash"></i> Hide</button>
                            <button onclick="toggleNotification(${reel.id})"><i class="fa fa-bell"></i> Turn on notifications</button>
                            <button onclick="blockUser(${reel.user.id})"><i class="fa fa-ban"></i> Block</button>
                        `}
                    </div>
                `;
                reelsContainer.appendChild(reelEl);
            });
            if (data.has_next) {
                const loadMore = document.createElement('button');
                loadMore.textContent = 'Load More';
                loadMore.onclick = () => loadReels(page + 1);
                reelsContainer.appendChild(loadMore);
            }
        })
        .catch(() => showModal('login-modal'));
}

function viewStory(storyId) {
    fetch(`/api/story/${storyId}`)
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
                    ${data.media_url.includes('.mp4') ? 
                        `<video controls src="${data.media_url}"></video>` : 
                        `<img src="${data.media_url}" alt="Story">`}
                    <p>${data.description}</p>
                    <p>By ${data.user}</p>
                </div>
            `;
            document.body.appendChild(modal);
            modal.style.display = 'block';
        })
        .catch(() => showModal('login-modal'));
}

function createContent(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    fetch('/api/create', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            if (data.message) {
                form.closest('.modal').style.display = 'none';
                form.reset();
                if (formData.get('type') === 'post') loadPosts();
                else if (formData.get('type') === 'reel') loadReels();
                else loadHome();
            } else {
                alert(data.error);
            }
        })
        .catch(() => showModal('login-modal'));
}

function likePost(postId, button) {
    fetch(`/api/like/${postId}`, { method: 'POST' })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            button.innerHTML = `<i class="fa fa-heart"></i> ${data.message === 'liked' ? 'Unlike' : 'Like'}`;
            // Update likes count if needed
            loadHome();
        })
        .catch(() => showModal('login-modal'));
}

function showCommentModal(postId) {
    fetch('/api/profile').then(response => {
        if (response.ok) {
            document.getElementById('comment-post-id').value = postId;
            showModal('comment-modal');
        } else {
            showModal('login-modal');
        }
    });
}

function commentPost(e) {
    e.preventDefault();
    const postId = document.getElementById('comment-post-id').value;
    const text = document.getElementById('comment-text').value;
    fetch(`/api/comment/${postId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            if (data.message) {
                document.getElementById('comment-modal').style.display = 'none';
                document.getElementById('comment-form').reset();
                loadPosts();
                loadReels();
            } else {
                alert(data.error);
            }
        })
        .catch(() => showModal('login-modal'));
}

function repost(postId) {
    fetch(`/api/repost/${postId}`, { method: 'POST' })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => alert(data.message))
        .catch(() => showModal('login-modal'));
}

function savePost(postId, button) {
    fetch(`/api/save/${postId}`, { method: 'POST' })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            button.innerHTML = `<i class="fa fa-bookmark"></i> ${data.message === 'saved' ? 'Unsave' : 'Save'}`;
        })
        .catch(() => showModal('login-modal'));
}

function report(reportedId, type) {
    const description = prompt('Reason for reporting:');
    if (description) {
        fetch(`/api/report/${reportedId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type, description })
        })
            .then(response => {
                if (!response.ok) throw new Error('Not logged in');
                return response.json();
            })
            .then(data => alert(data.message))
            .catch(() => showModal('login-modal'));
    }
}

function hidePost(postId) {
    fetch(`/api/hide/${postId}`, { method: 'POST' })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => alert(data.message))
        .catch(() => showModal('login-modal'));
}

function follow(userId) {
    fetch(`/api/follow/${userId}`, { method: 'POST' })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => alert(data.message))
        .catch(() => showModal('login-modal'));
}

function unfollow(userId) {
    fetch(`/api/unfollow/${userId}`, { method: 'POST' })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => alert(data.message))
        .catch(() => showModal('login-modal'));
}

function loadFriendsTab(tab) {
    showSection('friends');
    fetch(`/api/friends/${tab}`)
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            const list = document.getElementById('friends-list');
            list.innerHTML = '';
            const items = data[tab] || [];
            items.forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <div>
                        <img src="${item.profile_pic || '/static/default.jpg'}" alt="${item.real_name}">
                        <span>${item.real_name}</span>
                        <span>${item.mutual ? `${item.mutual} mutual friends` : ''}</span>
                    </div>
                    ${tab === 'requests' ? `
                        <div>
                            <button onclick="acceptRequest(${item.id})">Accept</button>
                            <button onclick="declineRequest(${item.id})">Decline</button>
                        </div>
                    ` : tab === 'suggested' ? `
                        <button onclick="follow(${item.id})">Follow</button>
                    ` : `
                        <button onclick="unfollow(${item.id})">Unfollow</button>
                    `}
                `;
                list.appendChild(li);
            });
        })
        .catch(() => showModal('login-modal'));
}

function acceptRequest(userId) {
    fetch(`/api/accept_request/${userId}`, { method: 'POST' })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            alert(data.message);
            loadFriendsTab('requests');
        })
        .catch(() => showModal('login-modal'));
}

function declineRequest(userId) {
    fetch(`/api/decline_request/${userId}`, { method: 'POST' })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            alert(data.message);
            loadFriendsTab('requests');
        })
        .catch(() => showModal('login-modal'));
}

function loadInboxTab(tab) {
    showSection('inbox');
    fetch(`/api/inbox/${tab}`)
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            const list = document.getElementById('inbox-list');
            list.innerHTML = '';
            const items = data[tab] || [];
            items.forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <div>
                        <img src="${item.profile_pic || '/static/default.jpg'}" alt="${item.real_name || item.name}">
                        <span>${item.real_name || item.name}</span>
                        <span>${item.last_msg_snippet}</span>
                        ${item.unread ? `<span>${item.unread} unread</span>` : ''}
                    </div>
                `;
                li.addEventListener('click', () => {
                    if (tab === 'chats') {
                        loadChat(item.other_id);
                    } else {
                        loadGroupChat(item.group_id);
                    }
                });
                list.appendChild(li);
            });
        })
        .catch(() => showModal('login-modal'));
}

function loadChat(otherId) {
    fetch(`/api/messages/private/${otherId}`)
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            document.getElementById('chat-name').textContent = data.messages[0]?.sender_id === otherId ? data.messages[0].sender_name : data.messages[0]?.receiver_name;
            document.getElementById('chat-profile-pic').src = data.messages[0]?.sender_id === otherId ? data.messages[0].sender_profile_pic : data.messages[0]?.receiver_profile_pic || '/static/default.jpg';
            const messages = document.getElementById('chat-messages');
            messages.innerHTML = '';
            data.messages.forEach(msg => {
                const msgEl = document.createElement('div');
                msgEl.className = `message ${msg.sender_id === getCurrentUserId() ? 'sent' : 'received'}`;
                msgEl.innerHTML = `
                    <p>${msg.text}</p>
                    ${msg.media_url ? msg.media_url.includes('.mp4') ? 
                        `<video controls src="${msg.media_url}"></video>` : 
                        `<img src="${msg.media_url}" alt="Message media">` : ''}
                    <small>${new Date(msg.timestamp).toLocaleString()}</small>
                `;
                messages.appendChild(msgEl);
            });
            messages.scrollTop = messages.scrollHeight;
            showModal('chat-modal');
            document.getElementById('chat-input-text').dataset.otherId = otherId;
        })
        .catch(() => showModal('login-modal'));
}

function sendMessage() {
    const otherId = document.getElementById('chat-input-text').dataset.otherId;
    const text = document.getElementById('chat-input-text').value;
    const file = document.getElementById('chat-input-file').files[0];
    const formData = new FormData();
    if (text) formData.append('text', text);
    if (file) formData.append('file', file);
    fetch(`/api/messages/private/${otherId}`, {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            if (data.message) {
                document.getElementById('chat-input-text').value = '';
                document.getElementById('chat-input-file').value = '';
                loadChat(otherId);
            } else {
                alert(data.error);
            }
        })
        .catch(() => showModal('login-modal'));
}

function loadGroupChat(groupId) {
    fetch(`/api/group/${groupId}`)
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(group => {
            document.getElementById('group-name').textContent = group.name;
            document.getElementById('group-profile-pic').src = group.profile_pic || '/static/default.jpg';
            fetch(`/api/messages/group/${groupId}`)
                .then(response => {
                    if (!response.ok) throw new Error('Not logged in');
                    return response.json();
                })
                .then(data => {
                    const messages = document.getElementById('group-chat-messages');
                    messages.innerHTML = '';
                    data.messages.forEach(msg => {
                        const msgEl = document.createElement('div');
                        msgEl.className = `message ${msg.sender_id === getCurrentUserId() ? 'sent' : 'received'}`;
                        msgEl.innerHTML = `
                            <p><strong>${msg.sender_name}</strong>: ${msg.text}</p>
                            ${msg.media_url ? msg.media_url.includes('.mp4') ? 
                                `<video controls src="${msg.media_url}"></video>` : 
                                `<img src="${msg.media_url}" alt="Message media">` : ''}
                            <small>${new Date(msg.timestamp).toLocaleString()}</small>
                        `;
                        messages.appendChild(msgEl);
                    });
                    messages.scrollTop = messages.scrollHeight;
                    showModal('group-chat-modal');
                    document.getElementById('group-chat-input-text').dataset.groupId = groupId;
                })
                .catch(() => showModal('login-modal'));
        })
        .catch(() => showModal('login-modal'));
}

function sendGroupMessage() {
    const groupId = document.getElementById('group-chat-input-text').dataset.groupId;
    const text = document.getElementById('group-chat-input-text').value;
    const file = document.getElementById('group-chat-input-file').files[0];
    const formData = new FormData();
    if (text) formData.append('text', text);
    if (file) formData.append('file', file);
    fetch(`/api/messages/group/${groupId}`, {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            if (data.message) {
                document.getElementById('group-chat-input-text').value = '';
                document.getElementById('group-chat-input-file').value = '';
                loadGroupChat(groupId);
            } else {
                alert(data.error);
            }
        })
        .catch(() => showModal('login-modal'));
}

function createGroup(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    fetch('/api/create_group', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            if (data.message) {
                form.closest('.modal').style.display = 'none';
                form.reset();
                loadInboxTab('groups');
            } else {
                alert(data.error);
            }
        })
        .catch(() => showModal('login-modal'));
}

function loadProfileTab(tab) {
    showSection('profile');
    fetch('/api/profile')
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            document.getElementById('profile-pic-img').src = data.profile_pic || '/static/default.jpg';
            document.getElementById('profile-name').textContent = data.real_name;
            document.getElementById('profile-bio').textContent = data.bio || '';
            document.getElementById('profile-posts').textContent = `Posts: ${data.posts_count}`;
            document.getElementById('profile-friends').textContent = `Friends: ${data.friends_count}`;
            document.getElementById('profile-followers').textContent = `Followers: ${data.followers_count}`;
            document.getElementById('profile-following').textContent = `Following: ${data.following_count}`;
            const content = document.getElementById('profile-content');
            content.innerHTML = '';
            if (tab === 'posts' || tab === 'reels' || tab === 'saved') {
                const posts = tab === 'posts' ? data.posts : tab === 'reels' ? data.reels : data.saved;
                posts.forEach(postId => {
                    fetch(`/api/posts?page=1`)
                        .then(response => response.json())
                        .then(data => {
                            const post = data.posts.find(p => p.id === postId);
                            if (post) {
                                const postEl = document.createElement('div');
                                postEl.className = 'post';
                                postEl.innerHTML = `
                                    <div class="post-header">
                                        <img src="${post.user.profile_pic || '/static/default.jpg'}" alt="${post.user.username}">
                                        <span>${post.user.real_name}</span>
                                    </div>
                                    <p>${post.description}</p>
                                    ${post.media_url ? post.media_url.includes('.mp4') ? 
                                        `<video controls src="${post.media_url}"></video>` : 
                                        `<img src="${post.media_url}" alt="Post media">` : ''}
                                    <div class="post-actions">
                                        <button onclick="likePost(${post.id}, this)">${post.is_liked ? 'Unlike' : 'Like'} (${post.likes})</button>
                                        <button onclick="showCommentModal(${post.id})">Comment (${post.comments})</button>
                                        <button onclick="repost(${post.id})">Repost</button>
                                        <button onclick="savePost(${post.id}, this)">${post.is_saved ? 'Unsave' : 'Save'}</button>
                                    </div>
                                `;
                                content.appendChild(postEl);
                            }
                        });
                });
            } else if (tab === 'info') {
                content.innerHTML = `
                    <form id="profile-form">
                        <label>Username: <input type="text" name="username" value="${data.username}"></label>
                        <label>Real Name: <input type="text" name="real_name" value="${data.real_name}"></label>
                        <label>Bio: <textarea name="bio">${data.bio || ''}</textarea></label>
                        <label>Profile Picture: <input type="file" name="file" accept="image/*"></label>
                        <label>Date of Birth: <input type="date" name="dob" value="${data.user_info.dob || ''}"></label>
                        <label>Gender: <input type="text" name="gender" value="${data.user_info.gender || ''}"></label>
                        <label>Pronouns: <input type="text" name="pronouns" value="${data.user_info.pronouns || ''}"></label>
                        <label>Work: <input type="text" name="work" value="${data.user_info.work || ''}"></label>
                        <label>Education: <input type="text" name="education" value="${data.user_info.education || ''}"></label>
                        <label>Location: <input type="text" name="location" value="${data.user_info.location || ''}"></label>
                        <label>Email: <input type="email" name="email" value="${data.user_info.email || ''}"></label>
                        <label>Phone: <input type="tel" name="phone" value="${data.user_info.phone || ''}"></label>
                        <label>Social Links: <input type="text" name="social_links" value="${data.user_info.social_links || ''}"></label>
                        <label>Website: <input type="url" name="website" value="${data.user_info.website || ''}"></label>
                        <label>Relationship: <input type="text" name="relationship" value="${data.user_info.relationship || ''}"></label>
                        <label>Spouse: <input type="text" name="spouse" value="${data.user_info.spouse || ''}"></label>
                        <button type="submit">Update Profile</button>
                    </form>
                `;
                document.getElementById('profile-form').addEventListener('submit', updateProfile);
            }
            document.querySelectorAll('.profile-navbar button').forEach(btn => btn.classList.remove('active'));
            document.querySelector(`.profile-navbar button[onclick="loadProfileTab('${tab}')"]`).classList.add('active');
        })
        .catch(() => showModal('login-modal'));
}

function updateProfile(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    fetch('/api/profile/update', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            if (data.message) {
                alert(data.message);
                loadProfileTab('info');
            } else {
                alert(data.error);
            }
        })
        .catch(() => showModal('login-modal'));
}

function search() {
    const query = document.getElementById('search-bar').value;
    const tab = document.querySelector('.tabs button.active')?.textContent.toLowerCase() || 'all';
    fetch(`/api/search?query=${encodeURIComponent(query)}&tab=${tab}`)
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            const results = document.getElementById('search-results');
            results.innerHTML = '';
            for (const [type, items] of Object.entries(data)) {
                const section = document.createElement('div');
                section.innerHTML = `<h3>${type.charAt(0).toUpperCase() + type.slice(1)}</h3>`;
                items.forEach(item => {
                    const itemEl = document.createElement('div');
                    itemEl.innerHTML = `
                        <img src="${item.profile_pic || '/static/default.jpg'}" alt="${item.real_name || item.name}">
                        <span>${item.real_name || item.name || item.user}</span>
                        ${item.description ? `<p>${item.description}</p>` : ''}
                    `;
                    section.appendChild(itemEl);
                });
                results.appendChild(section);
            }
        })
        .catch(() => showModal('login-modal'));
}

function loadSearchTab(tab) {
    showSection('search');
    document.querySelectorAll('.tabs button').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`.tabs button[onclick="loadSearchTab('${tab}')"]`).classList.add('active');
    search();
}

function loadNotifications() {
    showSection('notifications');
    fetch('/api/notifications')
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            const list = document.getElementById('notifications-list');
            list.innerHTML = '';
            data.notifications.forEach(notif => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <span>${notif.message}</span>
                    <small>${new Date(notif.timestamp).toLocaleString()}</small>
                    ${!notif.is_read ? `<button onclick="markRead(${notif.id})">Mark Read</button>` : ''}
                `;
                list.appendChild(li);
            });
        })
        .catch(() => showModal('login-modal'));
}

function markRead(notifId) {
    fetch(`/api/notification/mark_read/${notifId}`, { method: 'POST' })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            alert(data.message);
            loadNotifications();
        })
        .catch(() => showModal('login-modal'));
}

function updateSettings(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            alert(data.message);
            form.closest('.modal').style.display = 'none';
        })
        .catch(() => showModal('login-modal'));
}

function loadAdminTab(tab) {
    showSection('admin');
    fetch(`/api/admin/${tab}`)
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => {
            const content = document.getElementById('admin-content');
            content.innerHTML = '';
            if (tab === 'users') {
                data.users.forEach(user => {
                    const userEl = document.createElement('div');
                    userEl.innerHTML = `
                        <p>${user.username} (${user.real_name}) - Joined: ${new Date(user.created_at).toLocaleString()}</p>
                        <button onclick="adminDeleteUser(${user.id})">Delete</button>
                        <button onclick="adminBanUser(${user.id})">${user.is_banned ? 'Unban' : 'Ban'}</button>
                        <button onclick="adminWarnUser(${user.id})">Warn</button>
                    `;
                    content.appendChild(userEl);
                });
            } else if (tab === 'reports') {
                data.reports.forEach(report => {
                    const reportEl = document.createElement('div');
                    reportEl.innerHTML = `
                        <p>Reported by ${report.reporter}: ${report.type} (ID: ${report.reported_id}) - ${report.description}</p>
                        <button onclick="adminDeleteContent(${report.reported_id}, '${report.type}')">Delete Content</button>
                    `;
                    content.appendChild(reportEl);
                });
            }
            document.querySelectorAll('.tabs button').forEach(btn => btn.classList.remove('active'));
            document.querySelector(`.tabs button[onclick="loadAdminTab('${tab}')"]`).classList.add('active');
        })
        .catch(() => showModal('login-modal'));
}

function adminDeleteUser(userId) {
    if (confirm('Delete user?')) {
        fetch(`/api/admin/delete/user/${userId}`, { method: 'POST' })
            .then(response => {
                if (!response.ok) throw new Error('Not logged in');
                return response.json();
            })
            .then(data => {
                alert(data.message);
                loadAdminTab('users');
            })
            .catch(() => showModal('login-modal'));
    }
}

function adminBanUser(userId) {
    if (confirm('Ban/Unban user?')) {
        fetch(`/api/admin/ban/user/${userId}`, { method: 'POST' })
            .then(response => {
                if (!response.ok) throw new Error('Not logged in');
                return response.json();
            })
            .then(data => {
                alert(data.message);
                loadAdminTab('users');
            })
            .catch(() => showModal('login-modal'));
    }
}

function adminWarnUser(userId) {
    const message = prompt('Warning message:');
    if (message) {
        fetch(`/api/admin/warn/user/${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        })
            .then(response => {
                if (!response.ok) throw new Error('Not logged in');
                return response.json();
            })
            .then(data => {
                alert(data.message);
            })
            .catch(() => showModal('login-modal'));
    }
}

function adminDeleteContent(contentId, type) {
    if (confirm('Delete content?')) {
        const endpoint = type === 'group' ? `/api/admin/delete/group/${contentId}` : `/api/admin/delete/content/${contentId}`;
        fetch(endpoint, { method: 'POST' })
            .then(response => {
                if (!response.ok) throw new Error('Not logged in');
                return response.json();
            })
            .then(data => {
                alert(data.message);
                loadAdminTab('reports');
            })
            .catch(() => showModal('login-modal'));
    }
}

function logout() {
    fetch('/api/logout', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            document.getElementById('admin-btn').style.display = 'none';
            document.querySelectorAll('.section').forEach(section => {
                section.classList.remove('active');
                section.style.display = 'none';
            });
            showModal('login-modal');
        });
}

function getCurrentUserId() {
    return fetch('/api/profile')
        .then(response => {
            if (!response.ok) throw new Error('Not logged in');
            return response.json();
        })
        .then(data => data.id)
        .catch(() => null);
}
