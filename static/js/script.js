$(document).ready(function() {
    // Initialize the application
    initApp();
    
    // Navigation handling
    $('.nav-link, .mobile-nav-link').on('click', function(e) {
        e.preventDefault();
        const section = $(this).data('section');
        loadSection(section);
        
        // Update active states
        $('.nav-link, .mobile-nav-link').removeClass('active');
        $(this).addClass('active');
        $(`.nav-link[data-section="${section}"]`).addClass('active');
    });
    
    // Dark mode toggle
    $('#dark-mode-toggle').on('click', function() {
        $('body').toggleClass('dark-mode');
        const isDarkMode = $('body').hasClass('dark-mode');
        localStorage.setItem('darkMode', isDarkMode);
        $(this).html(isDarkMode ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>');
    });
    
    // Load home section by default
    loadSection('home');
});

function initApp() {
    // Check for dark mode preference
    const darkMode = localStorage.getItem('darkMode') === 'true';
    if (darkMode) {
        $('body').addClass('dark-mode');
        $('#dark-mode-toggle').html('<i class="fas fa-sun"></i>');
    }
    
    // Check if user is logged in
    checkAuthStatus();
}

function checkAuthStatus() {
    // In a real app, this would check with the server
    // For now, we'll assume the user is logged in if they're on the main app page
    console.log('Auth status checked');
}

function loadSection(section) {
    // Show loading indicator
    $('#content-container').html('<div class="text-center">Loading...</div>');
    
    // Load section content based on the section name
    switch(section) {
        case 'home':
            loadHome();
            break;
        case 'reels':
            loadReels();
            break;
        case 'friends':
            loadFriends();
            break;
        case 'inbox':
            loadInbox();
            break;
        case 'profile':
            loadProfile();
            break;
        case 'search':
            loadSearch();
            break;
        case 'add-to':
            showAddToModal();
            break;
        case 'notifications':
            loadNotifications();
            break;
        case 'admin-dashboard':
            loadAdminDashboard();
            break;
        default:
            $('#content-container').html('<div class="text-center">Section not found</div>');
    }
}

function loadHome() {
    $.get('/api/home', function(data) {
        let html = `
            <div class="content-section home-section active">
                <div class="stories-container">
                    ${data.stories.length > 0 ? data.stories.map(story => `
                        <div class="story" data-story-id="${story.id}">
                            <img src="/static/uploads/${story.media_url}" alt="Story">
                            <div class="story-overlay"></div>
                            <img src="/static/uploads/${story.user.profile_pic}" alt="${story.user.username}" class="story-avatar">
                            <div class="story-user">${story.user.username}</div>
                        </div>
                    `).join('') : '<p>No stories available</p>'}
                </div>
                
                <div class="posts-container">
                    ${data.posts.length > 0 ? data.posts.map(post => `
                        <div class="card post-card" data-post-id="${post.id}">
                            <div class="card-header">
                                <img src="/static/uploads/${post.user.profile_pic}" alt="${post.user.username}">
                                <div class="user-details">
                                    <span class="username">${post.user.username}</span>
                                    <span class="time">${formatTime(post.created_at)}</span>
                                </div>
                                <button class="more-options"><i class="fas fa-ellipsis-h"></i></button>
                            </div>
                            
                            <div class="card-content">
                                <p>${post.content}</p>
                                ${post.media_url ? `
                                    ${post.media_type === 'image' ? 
                                        `<img src="/static/uploads/${post.media_url}" alt="Post image">` : 
                                        `<video controls src="/static/uploads/${post.media_url}"></video>`
                                    }
                                ` : ''}
                            </div>
                            
                            <div class="card-actions">
                                <button class="action-btn like-btn ${post.is_liked ? 'liked' : ''}" data-post-id="${post.id}">
                                    <i class="fas fa-thumbs-up"></i>
                                    <span>Like (${post.likes_count})</span>
                                </button>
                                <button class="action-btn comment-btn" data-post-id="${post.id}">
                                    <i class="fas fa-comment"></i>
                                    <span>Comment (${post.comments_count})</span>
                                </button>
                                <button class="action-btn share-btn" data-post-id="${post.id}">
                                    <i class="fas fa-share"></i>
                                    <span>Share (${post.shares_count})</span>
                                </button>
                                <button class="action-btn save-btn ${post.is_saved ? 'saved' : ''}" data-post-id="${post.id}">
                                    <i class="fas fa-bookmark"></i>
                                    <span>Save</span>
                                </button>
                            </div>
                        </div>
                    `).join('') : '<p>No posts available. Follow more people to see their posts.</p>'}
                </div>
            </div>
        `;
        
        $('#content-container').html(html);
        
        // Add event listeners for post actions
        $('.like-btn').on('click', function() {
            const postId = $(this).data('post-id');
            const isLiked = $(this).hasClass('liked');
            
            if (isLiked) {
                unlikePost(postId, $(this));
            } else {
                likePost(postId, $(this));
            }
        });
        
        $('.comment-btn').on('click', function() {
            const postId = $(this).data('post-id');
            showCommentModal(postId);
        });
    }).fail(function() {
        $('#content-container').html('<div class="text-center">Error loading home content</div>');
    });
}

function loadReels() {
    $.get('/api/reels', function(data) {
        let html = `
            <div class="content-section reels-section active">
                <div class="reels-container">
                    ${data.reels.length > 0 ? data.reels.map(reel => `
                        <div class="reel-container" data-reel-id="${reel.id}">
                            <video class="reel-video" controls>
                                <source src="/static/uploads/${reel.media_url}" type="video/mp4">
                                Your browser does not support the video tag.
                            </video>
                            <div class="reel-content">
                                <h3>${reel.user.username}</h3>
                                <p>${reel.content || ''}</p>
                            </div>
                            <div class="reel-actions">
                                <button class="reel-action-btn like-reel-btn ${reel.is_liked ? 'liked' : ''}" data-reel-id="${reel.id}">
                                    <i class="fas fa-heart"></i>
                                    <span>${reel.likes_count}</span>
                                </button>
                                <button class="reel-action-btn comment-reel-btn" data-reel-id="${reel.id}">
                                    <i class="fas fa-comment"></i>
                                    <span>${reel.comments_count}</span>
                                </button>
                                <button class="reel-action-btn share-reel-btn" data-reel-id="${reel.id}">
                                    <i class="fas fa-share"></i>
                                    <span>${reel.shares_count}</span>
                                </button>
                                <button class="reel-action-btn save-reel-btn ${reel.is_saved ? 'saved' : ''}" data-reel-id="${reel.id}">
                                    <i class="fas fa-bookmark"></i>
                                </button>
                            </div>
                        </div>
                    `).join('') : '<p>No reels available</p>'}
                </div>
            </div>
        `;
        
        $('#content-container').html(html);
    }).fail(function() {
        $('#content-container').html('<div class="text-center">Error loading reels</div>');
    });
}

function loadFriends() {
    $.get('/api/friends', function(data) {
        let html = `
            <div class="content-section friends-section active">
                <div class="friends-tabs">
                    <button class="friends-tab active" data-tab="friends">Friends (${data.friends.length})</button>
                    <button class="friends-tab" data-tab="followers">Followers (${data.followers.length})</button>
                    <button class="friends-tab" data-tab="following">Following (${data.following.length})</button>
                    <button class="friends-tab" data-tab="requests">Requests (${data.friend_requests.length})</button>
                    <button class="friends-tab" data-tab="suggested">Suggested (${data.suggested.length})</button>
                </div>
                
                <div class="friends-content">
                    <div class="friends-list" data-list="friends">
                        ${data.friends.length > 0 ? data.friends.map(friend => `
                            <div class="friend-item" data-user-id="${friend.id}">
                                <img src="/static/uploads/${friend.profile_pic}" alt="${friend.username}">
                                <div class="friend-info">
                                    <h4>${friend.real_name}</h4>
                                    <p>@${friend.username}</p>
                                    <p>${friend.mutual_count} mutual friends</p>
                                </div>
                                <button class="btn btn-primary message-btn" data-user-id="${friend.id}">Message</button>
                            </div>
                        `).join('') : '<p>No friends yet</p>'}
                    </div>
                    
                    <div class="friends-list hidden" data-list="followers">
                        ${data.followers.length > 0 ? data.followers.map(follower => `
                            <div class="friend-item" data-user-id="${follower.id}">
                                <img src="/static/uploads/${follower.profile_pic}" alt="${follower.username}">
                                <div class="friend-info">
                                    <h4>${follower.real_name}</h4>
                                    <p>@${follower.username}</p>
                                    <p>${follower.mutual_count} mutual friends</p>
                                </div>
                                <button class="btn btn-primary follow-btn" data-user-id="${follower.id}">Follow Back</button>
                            </div>
                        `).join('') : '<p>No followers yet</p>'}
                    </div>
                    
                    <div class="friends-list hidden" data-list="following">
                        ${data.following.length > 0 ? data.following.map(following => `
                            <div class="friend-item" data-user-id="${following.id}">
                                <img src="/static/uploads/${following.profile_pic}" alt="${following.username}">
                                <div class="friend-info">
                                    <h4>${following.real_name}</h4>
                                    <p>@${following.username}</p>
                                    <p>${following.mutual_count} mutual friends</p>
                                </div>
                                <button class="btn btn-secondary unfollow-btn" data-user-id="${following.id}">Unfollow</button>
                            </div>
                        `).join('') : '<p>Not following anyone yet</p>'}
                    </div>
                    
                    <div class="friends-list hidden" data-list="requests">
                        ${data.friend_requests.length > 0 ? data.friend_requests.map(request => `
                            <div class="friend-item" data-user-id="${request.id}">
                                <img src="/static/uploads/${request.profile_pic}" alt="${request.username}">
                                <div class="friend-info">
                                    <h4>${request.real_name}</h4>
                                    <p>@${request.username}</p>
                                    <p>${request.mutual_count} mutual friends</p>
                                </div>
                                <div class="request-actions">
                                    <button class="btn btn-primary accept-btn" data-user-id="${request.id}">Accept</button>
                                    <button class="btn btn-secondary decline-btn" data-user-id="${request.id}">Decline</button>
                                </div>
                            </div>
                        `).join('') : '<p>No friend requests</p>'}
                    </div>
                    
                    <div class="friends-list hidden" data-list="suggested">
                        ${data.suggested.length > 0 ? data.suggested.map(suggested => `
                            <div class="friend-item" data-user-id="${suggested.id}">
                                <img src="/static/uploads/${suggested.profile_pic}" alt="${suggested.username}">
                                <div class="friend-info">
                                    <h4>${suggested.real_name}</h4>
                                    <p>@${suggested.username}</p>
                                    <p>${suggested.mutual_count} mutual friends</p>
                                </div>
                                <button class="btn btn-primary follow-btn" data-user-id="${suggested.id}">Follow</button>
                            </div>
                        `).join('') : '<p>No suggestions available</p>'}
                    </div>
                </div>
            </div>
        `;
        
        $('#content-container').html(html);
        
        // Tab switching
        $('.friends-tab').on('click', function() {
            const tab = $(this).data('tab');
            $('.friends-tab').removeClass('active');
            $(this).addClass('active');
            
            $('.friends-list').addClass('hidden');
            $(`.friends-list[data-list="${tab}"]`).removeClass('hidden');
        });
        
        // Follow actions
        $('.follow-btn').on('click', function() {
            const userId = $(this).data('user-id');
            followUser(userId, $(this));
        });
        
        $('.unfollow-btn').on('click', function() {
            const userId = $(this).data('user-id');
            unfollowUser(userId, $(this));
        });
    }).fail(function() {
        $('#content-container').html('<div class="text-center">Error loading friends</div>');
    });
}

function loadInbox() {
    $.get('/api/inbox', function(data) {
        let html = `
            <div class="content-section inbox-section active">
                <div class="inbox-tabs">
                    <button class="inbox-tab active" data-tab="chats">Chats (${data.chats.length})</button>
                    <button class="inbox-tab" data-tab="groups">Groups (${data.groups.length})</button>
                </div>
                
                <div class="inbox-content">
                    <div class="chats-list" data-list="chats">
                        ${data.chats.length > 0 ? data.chats.map(chat => `
                            <div class="chat-item" data-user-id="${chat.id}">
                                <img src="/static/uploads/${chat.profile_pic}" alt="${chat.username}">
                                <div class="chat-info">
                                    <h4>${chat.real_name}</h4>
                                    <p>${chat.last_message}</p>
                                    <span class="chat-time">${formatTime(chat.last_message_time)}</span>
                                </div>
                                ${chat.unread_count > 0 ? `<span class="unread-badge">${chat.unread_count}</span>` : ''}
                            </div>
                        `).join('') : '<p>No chats yet</p>'}
                    </div>
                    
                    <div class="chats-list hidden" data-list="groups">
                        ${data.groups.length > 0 ? data.groups.map(group => `
                            <div class="chat-item" data-group-id="${group.id}">
                                <img src="/static/uploads/${group.profile_pic}" alt="${group.name}">
                                <div class="chat-info">
                                    <h4>${group.name}</h4>
                                    <p>${group.last_message}</p>
                                    <span class="chat-time">${formatTime(group.last_message_time)}</span>
                                </div>
                                ${group.unread_count > 0 ? `<span class="unread-badge">${group.unread_count}</span>` : ''}
                            </div>
                        `).join('') : '<p>No groups yet</p>'}
                    </div>
                </div>
            </div>
        `;
        
        $('#content-container').html(html);
        
        // Tab switching
        $('.inbox-tab').on('click', function() {
            const tab = $(this).data('tab');
            $('.inbox-tab').removeClass('active');
            $(this).addClass('active');
            
            $('.chats-list').addClass('hidden');
            $(`.chats-list[data-list="${tab}"]`).removeClass('hidden');
        });
    }).fail(function() {
        $('#content-container').html('<div class="text-center">Error loading inbox</div>');
    });
}

function loadProfile(userId = null) {
    // If no userId provided, load current user's profile
    if (!userId) {
        // In a real app, this would get the current user's ID from the session
        userId = 1; // Placeholder
    }
    
    $.get(`/api/profile/${userId}`, function(data) {
        let html = `
            <div class="content-section profile-section active">
                <div class="profile-header">
                    <div class="cover-photo"></div>
                    <div class="profile-info">
                        <img src="/static/uploads/${data.profile_pic}" alt="${data.username}" class="profile-avatar">
                        <div class="profile-details">
                            <h2>${data.real_name}</h2>
                            <p>@${data.username}</p>
                            <p>${data.bio || 'No bio yet'}</p>
                            
                            <div class="profile-stats">
                                <div class="stat">
                                    <span class="stat-value">${data.posts_count}</span>
                                    <span class="stat-label">Posts</span>
                                </div>
                                <div class="stat">
                                    <span class="stat-value">${data.followers_count}</span>
                                    <span class="stat-label">Followers</span>
                                </div>
                                <div class="stat">
                                    <span class="stat-value">${data.following_count}</span>
                                    <span class="stat-label">Following</span>
                                </div>
                            </div>
                            
                            ${!data.is_own_profile ? `
                                <div class="profile-actions">
                                    ${data.is_following ? 
                                        `<button class="btn btn-secondary unfollow-btn" data-user-id="${data.id}">Unfollow</button>` : 
                                        `<button class="btn btn-primary follow-btn" data-user-id="${data.id}">Follow</button>`
                                    }
                                    <button class="btn btn-primary message-btn" data-user-id="${data.id}">Message</button>
                                </div>
                            ` : `
                                <div class="profile-actions">
                                    <button class="btn btn-primary edit-profile-btn">Edit Profile</button>
                                </div>
                            `}
                        </div>
                    </div>
                </div>
                
                <div class="profile-tabs">
                    <button class="profile-tab active" data-tab="posts">Posts</button>
                    <button class="profile-tab" data-tab="reels">Reels</button>
                    <button class="profile-tab" data-tab="about">About</button>
                </div>
                
                <div class="profile-content">
                    <div class="profile-tab-content active" data-tab="posts">
                        ${data.posts.length > 0 ? data.posts.map(post => `
                            <div class="card post-card" data-post-id="${post.id}">
                                <div class="card-content">
                                    <p>${post.content}</p>
                                    ${post.media_url ? `
                                        ${post.media_type === 'image' ? 
                                            `<img src="/static/uploads/${post.media_url}" alt="Post image">` : 
                                            `<video controls src="/static/uploads/${post.media_url}"></video>`
                                        }
                                    ` : ''}
                                </div>
                                <div class="card-actions">
                                    <span><i class="fas fa-thumbs-up"></i> ${post.likes_count}</span>
                                    <span><i class="fas fa-comment"></i> ${post.comments_count}</span>
                                    <span>${formatTime(post.created_at)}</span>
                                </div>
                            </div>
                        `).join('') : '<p>No posts yet</p>'}
                    </div>
                    
                    <div class="profile-tab-content hidden" data-tab="reels">
                        ${data.reels.length > 0 ? data.reels.map(reel => `
                            <div class="card reel-card" data-reel-id="${reel.id}">
                                <div class="card-content">
                                    <video controls>
                                        <source src="/static/uploads/${reel.media_url}" type="video/mp4">
                                        Your browser does not support the video tag.
                                    </video>
                                    <p>${reel.content || ''}</p>
                                </div>
                                <div class="card-actions">
                                    <span><i class="fas fa-heart"></i> ${reel.likes_count}</span>
                                    <span><i class="fas fa-comment"></i> ${reel.comments_count}</span>
                                    <span>${formatTime(reel.created_at)}</span>
                                </div>
                            </div>
                        `).join('') : '<p>No reels yet</p>'}
                    </div>
                    
                    <div class="profile-tab-content hidden" data-tab="about">
                        <div class="card">
                            <div class="card-content">
                                <h3>About</h3>
                                <div class="about-details">
                                    ${data.date_of_birth ? `<p><strong>Birthday:</strong> ${new Date(data.date_of_birth).toLocaleDateString()}</p>` : ''}
                                    ${data.gender ? `<p><strong>Gender:</strong> ${data.gender}</p>` : ''}
                                    ${data.pronouns ? `<p><strong>Pronouns:</strong> ${data.pronouns}</p>` : ''}
                                    ${data.work ? `<p><strong>Work:</strong> ${data.work}</p>` : ''}
                                    ${data.education ? `<p><strong>Education:</strong> ${data.education}</p>` : ''}
                                    ${data.location ? `<p><strong>Location:</strong> ${data.location}</p>` : ''}
                                    ${data.website ? `<p><strong>Website:</strong> <a href="${data.website}" target="_blank">${data.website}</a></p>` : ''}
                                    ${data.relationship ? `<p><strong>Relationship:</strong> ${data.relationship}</p>` : ''}
                                    ${data.spouse ? `<p><strong>Spouse/Partner:</strong> ${data.spouse}</p>` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        $('#content-container').html(html);
        
        // Tab switching
        $('.profile-tab').on('click', function() {
            const tab = $(this).data('tab');
            $('.profile-tab').removeClass('active');
            $(this).addClass('active');
            
            $('.profile-tab-content').addClass('hidden');
            $(`.profile-tab-content[data-tab="${tab}"]`).removeClass('hidden');
        });
        
        // Follow actions
        $('.follow-btn').on('click', function() {
            const userId = $(this).data('user-id');
            followUser(userId, $(this));
        });
        
        $('.unfollow-btn').on('click', function() {
            const userId = $(this).data('user-id');
            unfollowUser(userId, $(this));
        });
        
        // Edit profile
        $('.edit-profile-btn').on('click', function() {
            showEditProfileModal(data);
        });
    }).fail(function() {
        $('#content-container').html('<div class="text-center">Error loading profile</div>');
    });
}

function loadSearch() {
    let html = `
        <div class="content-section search-section active">
            <div class="search-header">
                <div class="form-group">
                    <input type="text" class="form-control search-input" placeholder="Search for people, groups, posts...">
                </div>
                
                <div class="search-tabs">
                    <button class="search-tab active" data-tab="all">All</button>
                    <button class="search-tab" data-tab="users">People</button>
                    <button class="search-tab" data-tab="groups">Groups</button>
                    <button class="search-tab" data-tab="posts">Posts</button>
                    <button class="search-tab" data-tab="reels">Reels</button>
                </div>
            </div>
            
            <div class="search-results">
                <p class="text-center">Enter a search term to see results</p>
            </div>
        </div>
    `;
    
    $('#content-container').html(html);
    
    // Search functionality
    let searchTimeout;
    $('.search-input').on('input', function() {
        clearTimeout(searchTimeout);
        const query = $(this).val();
        const activeTab = $('.search-tab.active').data('tab');
        
        if (query.length > 2) {
            searchTimeout = setTimeout(() => {
                performSearch(query, activeTab);
            }, 500);
        } else {
            $('.search-results').html('<p class="text-center">Enter a search term to see results</p>');
        }
    });
    
    // Tab switching
    $('.search-tab').on('click', function() {
        const tab = $(this).data('tab');
        $('.search-tab').removeClass('active');
        $(this).addClass('active');
        
        const query = $('.search-input').val();
        if (query.length > 2) {
            performSearch(query, tab);
        }
    });
}

function performSearch(query, tab = 'all') {
    $.get(`/api/search?q=${encodeURIComponent(query)}&tab=${tab}`, function(data) {
        let html = '';
        
        if (tab === 'all' || tab === 'users') {
            if (data.users && data.users.length > 0) {
                html += `<h3>People</h3>`;
                data.users.forEach(user => {
                    html += `
                        <div class="search-result-item" data-user-id="${user.id}">
                            <img src="/static/uploads/${user.profile_pic}" alt="${user.username}">
                            <div class="search-result-info">
                                <span class="name">${user.real_name}</span>
                                <span class="details">@${user.username}</span>
                            </div>
                        </div>
                    `;
                });
            }
        }
        
        if (tab === 'all' || tab === 'groups') {
            if (data.groups && data.groups.length > 0) {
                html += `<h3>Groups</h3>`;
                data.groups.forEach(group => {
                    html += `
                        <div class="search-result-item" data-group-id="${group.id}">
                            <img src="/static/uploads/${group.profile_pic}" alt="${group.name}">
                            <div class="search-result-info">
                                <span class="name">${group.name}</span>
                                <span class="details">${group.members_count} members</span>
                            </div>
                        </div>
                    `;
                });
            }
        }
        
        if (tab === 'all' || tab === 'posts') {
            if (data.posts && data.posts.length > 0) {
                html += `<h3>Posts</h3>`;
                data.posts.forEach(post => {
                    html += `
                        <div class="card post-card" data-post-id="${post.id}">
                            <div class="card-header">
                                <img src="/static/uploads/${post.user.profile_pic}" alt="${post.user.username}">
                                <div class="user-details">
                                    <span class="username">${post.user.username}</span>
                                    <span class="time">${formatTime(post.created_at)}</span>
                                </div>
                            </div>
                            <div class="card-content">
                                <p>${post.content}</p>
                                ${post.media_url ? `
                                    ${post.media_type === 'image' ? 
                                        `<img src="/static/uploads/${post.media_url}" alt="Post image">` : 
                                        `<video controls src="/static/uploads/${post.media_url}"></video>`
                                    }
                                ` : ''}
                            </div>
                            <div class="card-actions">
                                <span><i class="fas fa-thumbs-up"></i> ${post.likes_count}</span>
                                <span><i class="fas fa-comment"></i> ${post.comments_count}</span>
                            </div>
                        </div>
                    `;
                });
            }
        }
        
        if (tab === 'all' || tab === 'reels') {
            if (data.reels && data.reels.length > 0) {
                html += `<h3>Reels</h3>`;
                data.reels.forEach(reel => {
                    html += `
                        <div class="card reel-card" data-reel-id="${reel.id}">
                            <div class="card-content">
                                <video controls>
                                    <source src="/static/uploads/${reel.media_url}" type="video/mp4">
                                    Your browser does not support the video tag.
                                </video>
                                <p>${reel.content || ''}</p>
                            </div>
                            <div class="card-actions">
                                <span><i class="fas fa-heart"></i> ${reel.likes_count}</span>
                                <span><i class="fas fa-comment"></i> ${reel.comments_count}</span>
                                <span>${formatTime(reel.created_at)}</span>
                            </div>
                        </div>
                    `;
                });
            }
        }
        
        if (html === '') {
            html = '<p class="text-center">No results found</p>';
        }
        
        $('.search-results').html(html);
        
        // Add click handlers for search results
        $('.search-result-item[data-user-id]').on('click', function() {
            const userId = $(this).data('user-id');
            loadProfile(userId);
        });
    }).fail(function() {
        $('.search-results').html('<p class="text-center">Error performing search</p>');
    });
}

function loadNotifications() {
    $.get('/api/notifications', function(data) {
        let html = `
            <div class="content-section notifications-section active">
                <h2>Notifications</h2>
                <div class="notifications-list">
                    ${data.notifications.length > 0 ? data.notifications.map(notification => `
                        <div class="notification-item ${notification.is_read ? '' : 'unread'}" data-notification-id="${notification.id}">
                            <img src="/static/uploads/default_profile.png" alt="Notification">
                            <div class="notification-content">
                                <p class="text">${notification.content}</p>
                                <span class="time">${formatTime(notification.created_at)}</span>
                            </div>
                        </div>
                    `).join('') : '<p>No notifications</p>'}
                </div>
            </div>
        `;
        
        $('#content-container').html(html);
    }).fail(function() {
        $('#content-container').html('<div class="text-center">Error loading notifications</div>');
    });
}

function loadAdminDashboard() {
    $.get('/api/admin/dashboard', function(data) {
        let html = `
            <div class="content-section admin-dashboard active">
                <h2>Admin Dashboard</h2>
                
                <div class="admin-stats">
                    <div class="stat-card">
                        <span class="value">${data.stats.total_users}</span>
                        <span class="label">Total Users</span>
                    </div>
                    <div class="stat-card">
                        <span class="value">${data.stats.total_posts}</span>
                        <span class="label">Total Posts</span>
                    </div>
                    <div class="stat-card">
                        <span class="value">${data.stats.total_reels}</span>
                        <span class="label">Total Reels</span>
                    </div>
                    <div class="stat-card">
                        <span class="value">${data.stats.total_groups}</span>
                        <span class="label">Total Groups</span>
                    </div>
                    <div class="stat-card">
                        <span class="value">${data.stats.total_messages}</span>
                        <span class="label">Total Messages</span>
                    </div>
                </div>
                
                <div class="admin-section">
                    <h3>Pending Reports (${data.reports.length})</h3>
                    ${data.reports.length > 0 ? `
                        <table class="admin-table">
                            <thead>
                                <tr>
                                    <th>Reporter</th>
                                    <th>Reason</th>
                                    <th>Date</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.reports.map(report => `
                                    <tr>
                                        <td>${report.reporter}</td>
                                        <td>${report.reason}</td>
                                        <td>${formatTime(report.created_at)}</td>
                                        <td>
                                            <button class="admin-action-btn btn-primary view-report-btn" data-report-id="${report.id}">View</button>
                                            <button class="admin-action-btn btn-danger resolve-report-btn" data-report-id="${report.id}">Resolve</button>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    ` : '<p>No pending reports</p>'}
                </div>
                
                <div class="admin-section">
                    <h3>Users (${data.users.length})</h3>
                    ${data.users.length > 0 ? `
                        <table class="admin-table">
                            <thead>
                                <tr>
                                    <th>Username</th>
                                    <th>Real Name</th>
                                    <th>Joined</th>
                                    <th>Posts</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.users.map(user => `
                                    <tr>
                                        <td>${user.username}</td>
                                        <td>${user.real_name}</td>
                                        <td>${formatTime(user.created_at)}</td>
                                        <td>${user.posts_count}</td>
                                        <td>
                                            <button class="admin-action-btn btn-primary view-user-btn" data-user-id="${user.id}">View</button>
                                            ${!user.is_admin ? `<button class="admin-action-btn btn-danger delete-user-btn" data-user-id="${user.id}">Delete</button>` : ''}
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    ` : '<p>No users</p>'}
                </div>
                
                <div class="admin-section">
                    <h3>Groups (${data.groups.length})</h3>
                    ${data.groups.length > 0 ? `
                        <table class="admin-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Created By</th>
                                    <th>Created</th>
                                    <th>Members</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.groups.map(group => `
                                    <tr>
                                        <td>${group.name}</td>
                                        <td>${group.created_by}</td>
                                        <td>${formatTime(group.created_at)}</td>
                                        <td>${group.members_count}</td>
                                        <td>
                                            <button class="admin-action-btn btn-primary view-group-btn" data-group-id="${group.id}">View</button>
                                            <button class="admin-action-btn btn-danger delete-group-btn" data-group-id="${group.id}">Delete</button>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    ` : '<p>No groups</p>'}
                </div>
            </div>
        `;
        
        $('#content-container').html(html);
        
        // Admin actions
        $('.delete-user-btn').on('click', function() {
            const userId = $(this).data('user-id');
            if (confirm('Are you sure you want to delete this user?')) {
                deleteUser(userId);
            }
        });
        
        $('.delete-group-btn').on('click', function() {
            const groupId = $(this).data('group-id');
            if (confirm('Are you sure you want to delete this group?')) {
                deleteGroup(groupId);
            }
        });
        
        $('.resolve-report-btn').on('click', function() {
            const reportId = $(this).data('report-id');
            resolveReport(reportId);
        });
    }).fail(function() {
        $('#content-container').html('<div class="text-center">Error loading admin dashboard</div>');
    });
}

function showAddToModal() {
    let html = `
        <div class="modal" id="add-to-modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Create New</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="add-to-options">
                        <button class="add-to-option" data-type="post">
                            <i class="fas fa-edit"></i>
                            <span>Post</span>
                        </button>
                        <button class="add-to-option" data-type="reel">
                            <i class="fas fa-film"></i>
                            <span>Reel</span>
                        </button>
                        <button class="add-to-option" data-type="story">
                            <i class="fas fa-history"></i>
                            <span>Story</span>
                        </button>
                        <button class="add-to-option" data-type="group">
                            <i class="fas fa-users"></i>
                            <span>Group</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(html);
    $('#add-to-modal').show();
    
    // Close modal
    $('.modal-close').on('click', function() {
        $('#add-to-modal').remove();
    });
    
    // Option selection
    $('.add-to-option').on('click', function() {
        const type = $(this).data('type');
        $('#add-to-modal').remove();
        
        switch(type) {
            case 'post':
                showCreatePostModal();
                break;
            case 'reel':
                showCreateReelModal();
                break;
            case 'story':
                showCreateStoryModal();
                break;
            case 'group':
                showCreateGroupModal();
                break;
        }
    });
}

function showCreatePostModal() {
    let html = `
        <div class="modal" id="create-post-modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Create Post</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="create-post-form">
                        <div class="form-group">
                            <textarea class="form-control" name="content" placeholder="What's on your mind?" rows="4"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="post-media">Add Media (optional)</label>
                            <input type="file" id="post-media" name="media" accept="image/*,video/*">
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" name="is_private"> Make this post private
                            </label>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" id="cancel-post">Cancel</button>
                    <button class="btn btn-primary" id="submit-post">Post</button>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(html);
    $('#create-post-modal').show();
    
    // Close modal
    $('.modal-close, #cancel-post').on('click', function() {
        $('#create-post-modal').remove();
    });
    
    // Submit post
    $('#submit-post').on('click', function() {
        const formData = new FormData();
        formData.append('content', $('textarea[name="content"]').val());
        formData.append('is_private', $('input[name="is_private"]').is(':checked'));
        
        const mediaFile = $('#post-media')[0].files[0];
        if (mediaFile) {
            formData.append('media', mediaFile);
        }
        
        $.ajax({
            url: '/api/create-post',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    $('#create-post-modal').remove();
                    loadSection('home'); // Reload home to show the new post
                } else {
                    alert('Error: ' + response.message);
                }
            },
            error: function() {
                alert('Error creating post');
            }
        });
    });
}

function showCreateReelModal() {
    let html = `
        <div class="modal" id="create-reel-modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Create Reel</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="create-reel-form">
                        <div class="form-group">
                            <label for="reel-media">Select Video*</label>
                            <input type="file" id="reel-media" name="media" accept="video/*" required>
                        </div>
                        <div class="form-group">
                            <textarea class="form-control" name="content" placeholder="Add a caption (optional)" rows="3"></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" id="cancel-reel">Cancel</button>
                    <button class="btn btn-primary" id="submit-reel">Create Reel</button>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(html);
    $('#create-reel-modal').show();
    
    // Close modal
    $('.modal-close, #cancel-reel').on('click', function() {
        $('#create-reel-modal').remove();
    });
    
    // Submit reel
    $('#submit-reel').on('click', function() {
        const mediaFile = $('#reel-media')[0].files[0];
        if (!mediaFile) {
            alert('Please select a video file');
            return;
        }
        
        const formData = new FormData();
        formData.append('media', mediaFile);
        formData.append('content', $('textarea[name="content"]').val());
        
        $.ajax({
            url: '/api/create-reel',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    $('#create-reel-modal').remove();
                    loadSection('reels'); // Reload reels to show the new reel
                } else {
                    alert('Error: ' + response.message);
                }
            },
            error: function() {
                alert('Error creating reel');
            }
        });
    });
}

function showCreateStoryModal() {
    alert('Story creation functionality would be implemented here');
}

function showCreateGroupModal() {
    alert('Group creation functionality would be implemented here');
}

function showCommentModal(postId) {
    let html = `
        <div class="modal" id="comment-modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Comments</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="comments-list">
                        <p>Loading comments...</p>
                    </div>
                    <div class="add-comment">
                        <textarea class="form-control" placeholder="Write a comment..." rows="2"></textarea>
                        <button class="btn btn-primary">Post</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(html);
    $('#comment-modal').show();
    
    // Close modal
    $('.modal-close').on('click', function() {
        $('#comment-modal').remove();
    });
    
    // In a real app, this would load the actual comments
    setTimeout(() => {
        $('.comments-list').html('<p>No comments yet. Be the first to comment!</p>');
    }, 1000);
}

function showEditProfileModal(userData) {
    let html = `
        <div class="modal" id="edit-profile-modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Edit Profile</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="edit-profile-form">
                        <div class="form-group">
                            <label for="profile-pic">Profile Picture</label>
                            <input type="file" id="profile-pic" name="profile_pic" accept="image/*">
                        </div>
                        <div class="form-group">
                            <label for="real-name">Real Name</label>
                            <input type="text" id="real-name" name="real_name" class="form-control" value="${userData.real_name || ''}">
                        </div>
                        <div class="form-group">
                            <label for="bio">Bio</label>
                            <textarea id="bio" name="bio" class="form-control" rows="3">${userData.bio || ''}</textarea>
                        </div>
                        <div class="form-group">
                            <label for="email">Email</label>
                            <input type="email" id="email" name="email" class="form-control" value="${userData.email || ''}">
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" name="is_private" ${userData.is_private ? 'checked' : ''}> Private Account
                            </label>
                        </div>
                        <h3>Additional Information</h3>
                        <div class="form-group">
                            <label for="date-of-birth">Date of Birth</label>
                            <input type="date" id="date-of-birth" name="date_of_birth" class="form-control" value="${userData.date_of_birth || ''}">
                        </div>
                        <div class="form-group">
                            <label for="gender">Gender</label>
                            <select id="gender" name="gender" class="form-control">
                                <option value="">Select</option>
                                <option value="Male" ${userData.gender === 'Male' ? 'selected' : ''}>Male</option>
                                <option value="Female" ${userData.gender === 'Female' ? 'selected' : ''}>Female</option>
                                <option value="Non-binary" ${userData.gender === 'Non-binary' ? 'selected' : ''}>Non-binary</option>
                                <option value="Other" ${userData.gender === 'Other' ? 'selected' : ''}>Other</option>
                                <option value="Prefer not to say" ${userData.gender === 'Prefer not to say' ? 'selected' : ''}>Prefer not to say</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="pronouns">Pronouns</label>
                            <input type="text" id="pronouns" name="pronouns" class="form-control" value="${userData.pronouns || ''}" placeholder="e.g., she/her, he/him, they/them">
                        </div>
                        <div class="form-group">
                            <label for="work">Work</label>
                            <input type="text" id="work" name="work" class="form-control" value="${userData.work || ''}">
                        </div>
                        <div class="form-group">
                            <label for="education">Education</label>
                            <input type="text" id="education" name="education" class="form-control" value="${userData.education || ''}">
                        </div>
                        <div class="form-group">
                            <label for="location">Location</label>
                            <input type="text" id="location" name="location" class="form-control" value="${userData.location || ''}">
                        </div>
                        <div class="form-group">
                            <label for="website">Website</label>
                            <input type="url" id="website" name="website" class="form-control" value="${userData.website || ''}">
                        </div>
                        <div class="form-group">
                            <label for="relationship">Relationship Status</label>
                            <select id="relationship" name="relationship" class="form-control">
                                <option value="">Select</option>
                                <option value="Single" ${userData.relationship === 'Single' ? 'selected' : ''}>Single</option>
                                <option value="In a relationship" ${userData.relationship === 'In a relationship' ? 'selected' : ''}>In a relationship</option>
                                <option value="Engaged" ${userData.relationship === 'Engaged' ? 'selected' : ''}>Engaged</option>
                                <option value="Married" ${userData.relationship === 'Married' ? 'selected' : ''}>Married</option>
                                <option value="Divorced" ${userData.relationship === 'Divorced' ? 'selected' : ''}>Divorced</option>
                                <option value="Widowed" ${userData.relationship === 'Widowed' ? 'selected' : ''}>Widowed</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="spouse">Spouse/Partner</label>
                            <input type="text" id="spouse" name="spouse" class="form-control" value="${userData.spouse || ''}">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" id="cancel-edit">Cancel</button>
                    <button class="btn btn-primary" id="save-profile">Save Changes</button>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(html);
    $('#edit-profile-modal').show();
    
    // Close modal
    $('.modal-close, #cancel-edit').on('click', function() {
        $('#edit-profile-modal').remove();
    });
    
    // Save profile
    $('#save-profile').on('click', function() {
        const formData = new FormData($('#edit-profile-form')[0]);
        
        const profilePicFile = $('#profile-pic')[0].files[0];
        if (profilePicFile) {
            formData.append('profile_pic', profilePicFile);
        }
        
        $.ajax({
            url: '/api/update-profile',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    $('#edit-profile-modal').remove();
                    loadProfile(); // Reload profile to show the updated information
                } else {
                    alert('Error: ' + response.message);
                }
            },
            error: function() {
                alert('Error updating profile');
            }
        });
    });
}

// API interaction functions
function likePost(postId, button) {
    $.post(`/api/like/post/${postId}`, function(response) {
        if (response.success) {
            button.addClass('liked');
            const likeText = button.find('span');
            const currentLikes = parseInt(likeText.text().match(/\d+/)[0]);
            likeText.text(`Like (${currentLikes + 1})`);
        } else {
            alert('Error: ' + response.message);
        }
    }).fail(function() {
        alert('Error liking post');
    });
}

function unlikePost(postId, button) {
    $.post(`/api/unlike/post/${postId}`, function(response) {
        if (response.success) {
            button.removeClass('liked');
            const likeText = button.find('span');
            const currentLikes = parseInt(likeText.text().match(/\d+/)[0]);
            likeText.text(`Like (${currentLikes - 1})`);
        } else {
            alert('Error: ' + response.message);
        }
    }).fail(function() {
        alert('Error unliking post');
    });
}

function followUser(userId, button) {
    $.post(`/api/follow/${userId}`, function(response) {
        if (response.success) {
            button.text('Unfollow').removeClass('btn-primary').addClass('btn-secondary').removeClass('follow-btn').addClass('unfollow-btn');
            button.off('click').on('click', function() {
                unfollowUser(userId, $(this));
            });
        } else {
            alert('Error: ' + response.message);
        }
    }).fail(function() {
        alert('Error following user');
    });
}

function unfollowUser(userId, button) {
    $.post(`/api/unfollow/${userId}`, function(response) {
        if (response.success) {
            button.text('Follow').removeClass('btn-secondary').addClass('btn-primary').removeClass('unfollow-btn').addClass('follow-btn');
            button.off('click').on('click', function() {
                followUser(userId, $(this));
            });
        } else {
            alert('Error: ' + response.message);
        }
    }).fail(function() {
        alert('Error unfollowing user');
    });
}

function deleteUser(userId) {
    $.post(`/api/admin/delete-user/${userId}`, function(response) {
        if (response.success) {
            alert('User deleted successfully');
            loadAdminDashboard(); // Reload admin dashboard
        } else {
            alert('Error: ' + response.message);
        }
    }).fail(function() {
        alert('Error deleting user');
    });
}

function deleteGroup(groupId) {
    $.post(`/api/admin/delete-group/${groupId}`, function(response) {
        if (response.success) {
            alert('Group deleted successfully');
            loadAdminDashboard(); // Reload admin dashboard
        } else {
            alert('Error: ' + response.message);
        }
    }).fail(function() {
        alert('Error deleting group');
    });
}

function resolveReport(reportId) {
    $.post(`/api/admin/resolve-report/${reportId}`, function(response) {
        if (response.success) {
            alert('Report resolved successfully');
            loadAdminDashboard(); // Reload admin dashboard
        } else {
            alert('Error: ' + response.message);
        }
    }).fail(function() {
        alert('Error resolving report');
    });
}

// Utility functions
function formatTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMins < 1) {
        return 'Just now';
    } else if (diffMins < 60) {
        return `${diffMins} min ago`;
    } else if (diffHours < 24) {
        return `${diffHours} hr ago`;
    } else if (diffDays < 7) {
        return `${diffDays} day ago`;
    } else {
        return date.toLocaleDateString();
    }
}
