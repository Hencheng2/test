document.addEventListener('DOMContentLoaded', () => {
    checkLoginStatus();
    setupEventListeners();
});

// Variables for story viewer
let currentStories = [];
let currentStoryIndex = 0;
let currentStoryProgressInterval;
let isPaused = false;

function checkLoginStatus() {
    fetch('/api/profile')
        .then(response => {
            if (response.ok) {
                // User is logged in, show homepage
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
                // User is not logged in, show login modal and hide all sections
                document.querySelectorAll('.section').forEach(section => {
                    section.classList.remove('active');
                    section.style.display = 'none';
                });
                document.querySelectorAll('.modal').forEach(modal => modal.style.display = 'none');
                document.getElementById('login-modal').style.display = 'block';
            }
        })
        .catch(() => {
            // Handle network errors, show login modal
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
        closeBtn.addEventListener('click', () => {
            const modal = closeBtn.closest('.modal');
            modal.style.display = 'none';
            if (modal.id === 'story-viewer-modal') {
                stopStoryProgress();
            }
        });
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

function loadHome() {
    showSection('home');
    fetch('/api/home')
        .then(response => response.json())
        .then(data => {
            loadStories(data.stories);
            loadPosts();
        })
        .catch(() => showModal('login-modal'));
}

function loadStories(stories) {
    const storiesContainer = document.getElementById('stories-scroll');
    storiesContainer.innerHTML = '';
    
    stories.forEach(story => {
        const storyEl = document.createElement('div');
        storyEl.className = 'story-circle';
        storyEl.innerHTML = `
            <img src="${story.media_url || '/static/default.jpg'}" alt="${story.user}">
            <p>${story.user}</p>
        `;
        storyEl.addEventListener('click', () => viewStory(story));
        storiesContainer.appendChild(storyEl);
    });
}

function loadPosts() {
    fetch('/api/posts')
        .then(response => response.json())
        .then(posts => {
            const postsContainer = document.getElementById('home-posts');
            postsContainer.innerHTML = '';
            
            posts.forEach(post => {
                const postEl = createPostElement(post);
                postsContainer.appendChild(postEl);
            });
            
            // Setup infinite scroll
            setupInfiniteScroll();
        });
}

function createPostElement(post) {
    const postEl = document.createElement('div');
    postEl.className = 'post';
    
    postEl.innerHTML = `
        <div class="post-header">
            <img src="${post.user_profile_pic || '/static/default.jpg'}" alt="${post.user}">
            <div class="post-user-info">
                <span class="real-name">${post.user_real_name}</span>
                <span class="username">@${post.user}</span>
            </div>
            <span class="post-time">${new Date(post.created_at).toLocaleDateString()}</span>
        </div>
        <div class="post-content">
            ${post.description ? `<p>${post.description}</p>` : ''}
            ${post.media_url ? (post.media_type === 'video' ? 
                `<video src="${post.media_url}" controls></video>` : 
                `<img src="${post.media_url}" alt="Post image">`) : ''}
        </div>
        <div class="post-stats">
            <span>${post.likes_count || 0} likes</span>
            <span>${post.comments_count || 0} comments</span>
            <span>${post.reposts_count || 0} reposts</span>
            <span>${post.views_count || 0} views</span>
        </div>
        <div class="post-actions">
            <button onclick="likePost(${post.id})"><i class="fas fa-heart"></i> Like</button>
            <button onclick="showCommentModal(${post.id})"><i class="fas fa-comment"></i> Comment</button>
            <button onclick="sharePost(${post.id})"><i class="fas fa-share"></i> Share</button>
            <button onclick="savePost(${post.id})"><i class="fas fa-bookmark"></i> Save</button>
            <button onclick="repost(${post.id})"><i class="fas fa-retweet"></i> Repost</button>
            <div class="post-more-actions">
                <button><i class="fas fa-ellipsis-h"></i></button>
                <div class="post-more-dropdown">
                    <button onclick="followUser(${post.user_id})"><i class="fas fa-user-plus"></i> Follow</button>
                    <button onclick="reportPost(${post.id})"><i class="fas fa-flag"></i> Report</button>
                    <button onclick="hidePost(${post.id})"><i class="fas fa-eye-slash"></i> Hide</button>
                    <button onclick="togglePostNotifications(${post.id})"><i class="fas fa-bell"></i> Notifications</button>
                    <button onclick="blockUser(${post.user_id})"><i class="fas fa-ban"></i> Block</button>
                </div>
            </div>
        </div>
    `;
    
    return postEl;
}

function setupInfiniteScroll() {
    window.addEventListener('scroll', () => {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100) {
            loadMorePosts();
        }
    });
}

function loadMorePosts() {
    const postsContainer = document.getElementById('home-posts');
    const lastPostId = postsContainer.lastChild ? postsContainer.lastChild.dataset.id : 0;
    
    fetch(`/api/posts?after=${lastPostId}`)
        .then(response => response.json())
        .then(posts => {
            posts.forEach(post => {
                const postEl = createPostElement(post);
                postsContainer.appendChild(postEl);
            });
        });
}

function viewStory(story) {
    // Load all stories from friends
    fetch('/api/stories')
        .then(response => response.json())
        .then(stories => {
            currentStories = stories;
            currentStoryIndex = stories.findIndex(s => s.id === story.id);
            
            if (currentStoryIndex === -1) return;
            
            showModal('story-viewer-modal');
            loadCurrentStory();
            startStoryProgress();
        });
}

function loadCurrentStory() {
    const story = currentStories[currentStoryIndex];
    if (!story) {
        document.getElementById('story-viewer-modal').style.display = 'none';
        return;
    }
    
    document.getElementById('story-user-pic').src = story.user_profile_pic || '/static/default.jpg';
    document.getElementById('story-username').textContent = story.user;
    document.getElementById('story-time').textContent = new Date(story.created_at).toLocaleTimeString();
    
    const mediaContainer = document.getElementById('story-media-container');
    mediaContainer.innerHTML = '';
    
    if (story.media_url) {
        const mediaElement = story.media_type === 'video' ? 
            document.createElement('video') : document.createElement('img');
        
        mediaElement.src = story.media_url;
        mediaElement.style.maxWidth = '100%';
        mediaElement.style.maxHeight = '100%';
        mediaElement.style.objectFit = 'contain';
        
        if (story.media_type === 'video') {
            mediaElement.controls = false;
            mediaElement.autoplay = true;
            mediaElement.loop = false;
            mediaElement.addEventListener('ended', nextStory);
        }
        
        mediaContainer.appendChild(mediaElement);
    }
    
    document.getElementById('story-description').textContent = story.description || '';
    
    // Setup progress bars
    const progressContainer = document.getElementById('story-progress-container');
    progressContainer.innerHTML = '';
    
    currentStories.forEach((_, index) => {
        const progressBar = document.createElement('div');
        progressBar.className = 'story-progress-bar';
        progressBar.innerHTML = `<div class="story-progress-fill" style="width: ${index < currentStoryIndex ? '100%' : '0%'}"></div>`;
        progressContainer.appendChild(progressBar);
    });
}

function startStoryProgress() {
    stopStoryProgress();
    isPaused = false;
    
    const progressFill = document.querySelectorAll('.story-progress-fill')[currentStoryIndex];
    if (!progressFill) return;
    
    let width = 0;
    const duration = 5000; // 5 seconds per story
    
    currentStoryProgressInterval = setInterval(() => {
        if (!isPaused) {
            width += (100 / (duration / 100));
            progressFill.style.width = width + '%';
            
            if (width >= 100) {
                nextStory();
            }
        }
    }, 100);
}

function stopStoryProgress() {
    if (currentStoryProgressInterval) {
        clearInterval(currentStoryProgressInterval);
        currentStoryProgressInterval = null;
    }
}

function pauseStory() {
    isPaused = true;
}

function resumeStory() {
    isPaused = false;
}

function nextStory() {
    currentStoryIndex++;
    if (currentStoryIndex >= currentStories.length) {
        document.getElementById('story-viewer-modal').style.display = 'none';
        stopStoryProgress();
        return;
    }
    
    loadCurrentStory();
    startStoryProgress();
}

function prevStory() {
    if (currentStoryIndex <= 0) return;
    
    currentStoryIndex--;
    loadCurrentStory();
    startStoryProgress();
}

// Add event listeners for story navigation
document.addEventListener('DOMContentLoaded', () => {
    const storyViewer = document.getElementById('story-viewer-modal');
    
    // Swipe left for next story
    storyViewer.addEventListener('swipeleft', nextStory);
    
    // Swipe right for previous story
    storyViewer.addEventListener('swiperight', prevStory);
    
    // Swipe down to exit
    storyViewer.addEventListener('swipedown', () => {
        storyViewer.style.display = 'none';
        stopStoryProgress();
    });
    
    // Touch and hold to pause
    storyViewer.addEventListener('touchstart', pauseStory);
    storyViewer.addEventListener('touchend', resumeStory);
    storyViewer.addEventListener('touchcancel', resumeStory);
    
    // Mouse events for desktop
    storyViewer.addEventListener('mousedown', pauseStory);
    storyViewer.addEventListener('mouseup', resumeStory);
    storyViewer.addEventListener('mouseleave', resumeStory);
});

function likePost(postId) {
    fetch('/api/like', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ post_id: postId })
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                // Update like count in UI
                const postEl = document.querySelector(`.post[data-id="${postId}"]`);
                if (postEl) {
                    const likesSpan = postEl.querySelector('.post-stats span:first-child');
                    const likesCount = parseInt(likesSpan.textContent) + 1;
                    likesSpan.textContent = `${likesCount} likes`;
                }
            }
        });
}

function showCommentModal(postId) {
    document.getElementById('comment-post-id').value = postId;
    showModal('comment-modal');
}

function commentPost(e) {
    e.preventDefault();
    const postId = document.getElementById('comment-post-id').value;
    const text = document.getElementById('comment-text').value;
    
    fetch('/api/comment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ post_id: postId, text })
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                document.getElementById('comment-modal').style.display = 'none';
                document.getElementById('comment-text').value = '';
                
                // Update comment count in UI
                const postEl = document.querySelector(`.post[data-id="${postId}"]`);
                if (postEl) {
                    const commentsSpan = postEl.querySelector('.post-stats span:nth-child(2)');
                    const commentsCount = parseInt(commentsSpan.textContent) + 1;
                    commentsSpan.textContent = `${commentsCount} comments`;
                }
            }
        });
}

function sharePost(postId) {
    // Implementation for sharing a post
    alert(`Sharing post ${postId}`);
}

function savePost(postId) {
    fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ post_id: postId })
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert('Post saved!');
            }
        });
}

function repost(postId) {
    fetch('/api/repost', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ post_id: postId })
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                // Update repost count in UI
                const postEl = document.querySelector(`.post[data-id="${postId}"]`);
                if (postEl) {
                    const repostsSpan = postEl.querySelector('.post-stats span:nth-child(3)');
                    const repostsCount = parseInt(repostsSpan.textContent) + 1;
                    repostsSpan.textContent = `${repostsCount} reposts`;
                }
            }
        });
}

function followUser(userId) {
    fetch('/api/follow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert('User followed!');
            }
        });
}

function reportPost(postId) {
    const reason = prompt('Please enter the reason for reporting this post:');
    if (reason) {
        fetch('/api/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ post_id: postId, reason })
        })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    alert('Post reported!');
                }
            });
    }
}

function hidePost(postId) {
    fetch('/api/hide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ post_id: postId })
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                // Remove post from UI
                const postEl = document.querySelector(`.post[data-id="${postId}"]`);
                if (postEl) {
                    postEl.remove();
                }
            }
        });
}

function togglePostNotifications(postId) {
    fetch('/api/toggle_notifications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ post_id: postId })
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(`Post notifications ${data.enabled ? 'enabled' : 'disabled'}!`);
            }
        });
}

function blockUser(userId) {
    if (confirm('Are you sure you want to block this user?')) {
        fetch('/api/block', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    alert('User blocked!');
                    // Remove all posts from this user
                    document.querySelectorAll('.post').forEach(postEl => {
                        if (postEl.dataset.userId == userId) {
                            postEl.remove();
                        }
                    });
                }
            });
    }
}

function createContent(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    fetch('/api/create_content', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                e.target.reset();
                document.getElementById(e.target.closest('.modal').id).style.display = 'none';
                alert('Content created successfully!');
                if (data.type === 'story') {
                    loadHome(); // Reload home to show the new story
                }
            } else {
                alert(data.error);
            }
        });
}

function createGroup(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    fetch('/api/create_group', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                e.target.reset();
                document.getElementById('create-group-modal').style.display = 'none';
                alert('Group created successfully!');
            } else {
                alert(data.error);
            }
        });
}

function updateSettings(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    fetch('/api/update_settings', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert('Settings updated!');
                document.getElementById('settings-modal').style.display = 'none';
            } else {
                alert(data.error);
            }
        });
}

function search() {
    const query = document.getElementById('search-bar').value;
    if (query.length < 2) return;
    
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(results => {
            const resultsContainer = document.getElementById('search-results');
            resultsContainer.innerHTML = '';
            
            results.forEach(result => {
                const resultEl = document.createElement('div');
                resultEl.className = 'search-result';
                resultEl.textContent = result.name || result.title;
                resultsContainer.appendChild(resultEl);
            });
        });
}

function loadReels() {
    showSection('reels');
    // Implementation for loading reels
}

function loadFriendsTab(tab) {
    showSection('friends');
    fetch(`/api/friends?tab=${tab}`)
        .then(response => response.json())
        .then(friends => {
            const list = document.getElementById('friends-list');
            list.innerHTML = '';
            
            friends.forEach(friend => {
                const li = document.createElement('li');
                li.textContent = friend.name;
                list.appendChild(li);
            });
        });
}

function loadInboxTab(tab) {
    showSection('inbox');
    fetch(`/api/inbox?tab=${tab}`)
        .then(response => response.json())
        .then(chats => {
            const list = document.getElementById('inbox-list');
            list.innerHTML = '';
            
            chats.forEach(chat => {
                const li = document.createElement('li');
                li.textContent = chat.name;
                list.appendChild(li);
            });
        });
}

function loadProfileTab(tab) {
    showSection('profile');
    fetch(`/api/profile?tab=${tab}`)
        .then(response => response.json())
        .then(profile => {
            document.getElementById('profile-name').textContent = profile.name;
            document.getElementById('profile-bio').textContent = profile.bio;
            document.getElementById('profile-posts').textContent = `${profile.posts_count} Posts`;
            document.getElementById('profile-friends').textContent = `${profile.friends_count} Friends`;
            document.getElementById('profile-followers').textContent = `${profile.followers_count} Followers`;
            document.getElementById('profile-following').textContent = `${profile.following_count} Following`;
            
            const content = document.getElementById('profile-content');
            content.innerHTML = '';
            
            if (tab === 'posts') {
                profile.posts.forEach(post => {
                    const postEl = createPostElement(post);
                    content.appendChild(postEl);
                });
            }
        });
}

function loadNotifications() {
    showSection('notifications');
    fetch('/api/notifications')
        .then(response => response.json())
        .then(notifications => {
            const list = document.getElementById('notifications-list');
            list.innerHTML = '';
            
            notifications.forEach(notification => {
                const li = document.createElement('li');
                li.textContent = notification.text;
                list.appendChild(li);
            });
        });
}

function loadAdminTab(tab) {
    showSection('admin');
    fetch(`/api/admin?tab=${tab}`)
        .then(response => response.json())
        .then(data => {
            const content = document.getElementById('admin-content');
            content.innerHTML = '';
            
            if (tab === 'users') {
                data.users.forEach(user => {
                    const userEl = document.createElement('div');
                    userEl.textContent = user.username;
                    content.appendChild(userEl);
                });
            } else if (tab === 'reports') {
                data.reports.forEach(report => {
                    const reportEl = document.createElement('div');
                    reportEl.textContent = report.reason;
                    content.appendChild(reportEl);
                });
            }
        });
}

function logout() {
    fetch('/api/logout')
        .then(() => {
            document.querySelectorAll('.section').forEach(section => {
                section.classList.remove('active');
                section.style.display = 'none';
            });
            showModal('login-modal');
        });
}

// Add swipe detection
(function() {
    let touchstartX = 0;
    let touchstartY = 0;
    let touchendX = 0;
    let touchendY = 0;
    
    document.addEventListener('touchstart', e => {
        touchstartX = e.changedTouches[0].screenX;
        touchstartY = e.changedTouches[0].screenY;
    }, false);
    
    document.addEventListener('touchend', e => {
        touchendX = e.changedTouches[0].screenX;
        touchendY = e.changedTouches[0].screenY;
        handleSwipe();
    }, false);
    
    function handleSwipe() {
        const dx = touchendX - touchstartX;
        const dy = touchendY - touchstartY;
        
        // Minimum swipe distance
        if (Math.abs(dx) < 30 && Math.abs(dy) < 30) return;
        
        const event = new CustomEvent('swipe');
        if (Math.abs(dx) > Math.abs(dy)) {
            // Horizontal swipe
            if (dx > 0) {
                event.swipeDirection = 'right';
            } else {
                event.swipeDirection = 'left';
            }
        } else {
            // Vertical swipe
            if (dy > 0) {
                event.swipeDirection = 'down';
            } else {
                event.swipeDirection = 'up';
            }
        }
        
        document.dispatchEvent(event);
    }
    
    // Create specific swipe events
    document.addEventListener('swipe', e => {
        const specificEvent = new CustomEvent(`swipe${e.swipeDirection}`);
        document.dispatchEvent(specificEvent);
    });
})();
