// script.js
document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentUser = null;
    let activePage = 'home';
    let activeModal = null;
    let storyIndex = 0;
    let storiesData = [];
    
    // DOM elements
    const navbarLinks = document.querySelectorAll('.navbar-link');
    const pages = document.querySelectorAll('.page');
    const modals = document.querySelectorAll('.modal');
    const storyModal = document.getElementById('storyModal');
    const chatModal = document.getElementById('chatModal');
    const groupChatModal = document.getElementById('groupChatModal');
    const addModal = document.getElementById('addModal');
    const profileModal = document.getElementById('profileModal');
    const searchModal = document.getElementById('searchModal');
    const notificationsModal = document.getElementById('notificationsModal');
    const menuModal = document.getElementById('menuModal');
    const adminModal = document.getElementById('adminModal');
    
    // Initialize the app
    function init() {
        // Check if user is logged in
        checkAuthStatus();
        
        // Set up event listeners
        setupEventListeners();
        
        // Show the appropriate page
        showPage(activePage);
    }
    
    // Check if user is logged in
    function checkAuthStatus() {
        // In a real app, we would check the session
        // For now, we'll assume the user is logged in if currentUser is set
        if (!currentUser) {
            // Show login page
            showLoginPage();
        }
    }
    
    // Show login page
    function showLoginPage() {
        document.getElementById('app').innerHTML = `
            <div class="auth-container">
                <div class="auth-logo">SociaFam</div>
                <form class="auth-form" id="loginForm">
                    <input type="text" class="auth-input" id="username" placeholder="Username or email" required>
                    <input type="password" class="auth-input" id="password" placeholder="Password" required>
                    <button type="submit" class="auth-button">Log In</button>
                </form>
                <div class="auth-footer">
                    Don't have an account? <a href="#" id="showRegister">Sign up</a>
                </div>
            </div>
        `;
        
        document.getElementById('loginForm').addEventListener('submit', handleLogin);
        document.getElementById('showRegister').addEventListener('click', showRegisterPage);
    }
    
    // Show register page
    function showRegisterPage(e) {
        e.preventDefault();
        document.getElementById('app').innerHTML = `
            <div class="auth-container">
                <div class="auth-logo">SociaFam</div>
                <form class="auth-form" id="registerForm">
                    <input type="text" class="auth-input" id="username" placeholder="Username" required>
                    <input type="password" class="auth-input" id="password" placeholder="Password" required>
                    <div class="auth-info">Password must be at least 6 characters long and contain numbers, letters, and special characters.</div>
                    <button type="submit" class="auth-button">Register</button>
                </form>
                <div class="auth-footer">
                    Already have an account? <a href="#" id="showLogin">Log in</a>
                </div>
            </div>
        `;
        
        document.getElementById('registerForm').addEventListener('submit', handleRegister);
        document.getElementById('showLogin').addEventListener('click', showLoginPage);
    }
    
    // Handle login
    function handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        // In a real app, we would send this to the server
        // For now, we'll just simulate a successful login
        fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentUser = data.user;
                document.getElementById('app').innerHTML = '<div id="mainApp"></div>';
                initApp();
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }
    
    // Handle registration
    function handleRegister(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                showLoginPage();
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }
    
    // Initialize the main app
    function initApp() {
        // Load the main app structure
        loadMainApp();
        
        // Load initial data
        loadData();
    }
    
    // Load the main app structure
    function loadMainApp() {
        document.getElementById('mainApp').innerHTML = `
            <!-- Navbar -->
            <nav class="navbar">
                <div class="navbar-container">
                    <a href="#" class="logo">SociaFam</a>
                    <div class="navbar-links">
                        <a href="#" class="navbar-link active" data-page="home"><i class="fa fa-home"></i></a>
                        <a href="#" class="navbar-link" data-page="reels"><i class="fa fa-video-camera"></i></a>
                        <a href="#" class="navbar-link" data-page="friends"><i class="fa fa-users"></i></a>
                        <a href="#" class="navbar-link" data-page="inbox"><i class="fa fa-inbox"></i></a>
                        <a href="#" class="navbar-link" data-page="profile"><i class="fa fa-user"></i></a>
                        <a href="#" class="navbar-link" data-page="search"><i class="fa fa-search"></i></a>
                        <a href="#" class="navbar-link" data-page="add"><i class="fa fa-plus"></i></a>
                        <a href="#" class="navbar-link" data-page="notifications"><i class="fa fa-bell"></i></a>
                        <a href="#" class="navbar-link" data-page="menu"><i class="fa fa-bars"></i></a>
                        <a href="#" class="navbar-link" data-page="admin" id="adminLink" style="display: none;"><i class="fa fa-cog"></i></a>
                    </div>
                </div>
            </nav>
            
            <!-- Main Content -->
            <div class="container main-content">
                <!-- Home Page -->
                <div class="page" id="home">
                    <!-- Stories -->
                    <div class="stories">
                        <div class="stories-header">
                            <h3>Your Stories</h3>
                        </div>
                        <div class="stories-container" id="storiesContainer">
                            <!-- Stories will be added here -->
                        </div>
                    </div>
                    
                    <!-- Posts -->
                    <div id="postsContainer">
                        <!-- Posts will be added here -->
                    </div>
                </div>
                
                <!-- Reels Page -->
                <div class="page" id="reels" style="display: none;">
                    <div class="reels-container" id="reelsContainer">
                        <!-- Reels will be added here -->
                    </div>
                </div>
                
                <!-- Friends Page -->
                <div class="page" id="friends" style="display: none;">
                    <div class="friends-container">
                        <div class="friends-header">
                            <div class="friends-tab active" data-tab="followers">Followers <span id="followersCount">0</span></div>
                            <div class="friends-tab" data-tab="following">Following <span id="followingCount">0</span></div>
                            <div class="friends-tab" data-tab="friends">Friends <span id="friendsCount">0</span></div>
                            <div class="friends-tab" data-tab="requests">Requests <span id="requestsCount">0</span></div>
                            <div class="friends-tab" data-tab="suggested">Suggested <span id="suggestedCount">0</span></div>
                        </div>
                        <div class="friends-list" id="friendsList">
                            <!-- Friends list will be added here -->
                        </div>
                    </div>
                </div>
                
                <!-- Inbox Page -->
                <div class="page" id="inbox" style="display: none;">
                    <div class="inbox-container">
                        <div class="inbox-header">
                            <div class="inbox-tab active" data-tab="chats">Chats <span id="chatsCount">0</span></div>
                            <div class="inbox-tab" data-tab="groups">Groups <span id="groupsCount">0</span></div>
                            <div class="inbox-tab" data-tab="new">+</div>
                        </div>
                        <div class="inbox-list" id="inboxList">
                            <!-- Inbox list will be added here -->
                        </div>
                    </div>
                </div>
                
                <!-- Profile Page -->
                <div class="page" id="profile" style="display: none;">
                    <div class="profile-container">
                        <div class="profile-header">
                            <div class="profile-avatar">
                                <img src="default.jpg" alt="Profile Picture" id="profileAvatar">
                                <div class="edit-btn" id="editProfilePic">
                                    <i class="fa fa-camera"></i>
                                </div>
                            </div>
                            <div class="profile-info">
                                <div class="profile-username" id="profileUsername">Username</div>
                                <div class="profile-recovery-key" id="profileRecoveryKey">Recovery Key: ABC123</div>
                                <div class="profile-counts">
                                    <div class="profile-count">
                                        <div class="profile-count-number" id="postsCount">0</div>
                                        <div class="profile-count-label">Posts</div>
                                    </div>
                                    <div class="profile-count">
                                        <div class="profile-count-number" id="followersCountProfile">0</div>
                                        <div class="profile-count-label">Followers</div>
                                    </div>
                                    <div class="profile-count">
                                        <div class="profile-count-number" id="followingCountProfile">0</div>
                                        <div class="profile-count-label">Following</div>
                                    </div>
                                    <div class="profile-count">
                                        <div class="profile-count-number" id="likesCount">0</div>
                                        <div class="profile-count-label">Likes</div>
                                    </div>
                                </div>
                                <div class="profile-actions">
                                    <button class="profile-action edit" id="editProfile">Edit Profile</button>
                                    <button class="profile-action share" id="shareProfile">Share Profile</button>
                                </div>
                            </div>
                        </div>
                        <div class="profile-bio" id="profileBio">
                            <!-- Bio will be added here -->
                        </div>
                        <div class="profile-info-section" id="profileInfoSection" style="display: none;">
                            <!-- Info will be added here -->
                        </div>
                        <div class="profile-tabs">
                            <div class="profile-tab active" data-tab="posts">Posts</div>
                            <div class="profile-tab" data-tab="saved">Saved</div>
                            <div class="profile-tab" data-tab="reposts">Reposts</div>
                            <div class="profile-tab" data-tab="liked">Liked</div>
                            <div class="profile-tab" data-tab="reels">Reels</div>
                        </div>
                        <div class="profile-content" id="profileContent">
                            <!-- Content will be added here -->
                        </div>
                    </div>
                </div>
                
                <!-- Search Page -->
                <div class="page" id="search" style="display: none;">
                    <div class="search-container">
                        <div class="search-header">
                            <input type="text" class="search-input" placeholder="Search" id="searchInput">
                        </div>
                        <div class="search-tabs">
                            <div class="search-tab active" data-tab="all">All</div>
                            <div class="search-tab" data-tab="users">Users</div>
                            <div class="search-tab" data-tab="groups">Groups</div>
                            <div class="search-tab" data-tab="posts">Posts</div>
                            <div class="search-tab" data-tab="reels">Reels</div>
                        </div>
                        <div class="search-results" id="searchResults">
                            <!-- Results will be added here -->
                        </div>
                    </div>
                </div>
                
                <!-- Add Page -->
                <div class="page" id="add" style="display: none;">
                    <div class="add-container">
                        <div class="add-options">
                            <div class="add-option active" data-option="post">Post</div>
                            <div class="add-option" data-option="reel">Reel</div>
                            <div class="add-option" data-option="story">Story</div>
                        </div>
                        <div class="add-content">
                            <i class="fa fa-cloud-upload"></i>
                            <p>Choose a file to upload</p>
                            <div class="add-buttons">
                                <button class="add-button photo" data-type="photo">Photo</button>
                                <button class="add-button video" data-type="video">Video</button>
                                <button class="add-button text" data-type="text">Text</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Notifications Page -->
                <div class="page" id="notifications" style="display: none;">
                    <div class="notifications-container">
                        <div class="notification" id="systemNotification">
                            <div class="notification-avatar">
                                <img src="default.jpg" alt="SociaFam">
                            </div>
                            <div class="notification-content">
                                <div class="notification-text">Welcome to SociaFam! We're excited to have you here.</div>
                                <div class="notification-time">Just now</div>
                            </div>
                        </div>
                        <!-- More notifications will be added here -->
                    </div>
                </div>
                
                <!-- Menu Page -->
                <div class="page" id="menu" style="display: none;">
                    <div class="menu-container">
                        <div class="menu-item" id="helpSupport">
                            <i class="fa fa-question-circle"></i>
                            <div class="menu-item-text">Help & Support</div>
                            <i class="fa fa-chevron-right menu-item-arrow"></i>
                        </div>
                        <div class="menu-item" id="settingsPrivacy">
                            <i class="fa fa-cog"></i>
                            <div class="menu-item-text">Settings & Privacy</div>
                            <i class="fa fa-chevron-right menu-item-arrow"></i>
                        </div>
                        <div class="menu-item" id="logout">
                            <i class="fa fa-sign-out"></i>
                            <div class="menu-item-text">Log Out</div>
                            <i class="fa fa-chevron-right menu-item-arrow"></i>
                        </div>
                    </div>
                </div>
                
                <!-- Admin Dashboard -->
                <div class="page" id="admin" style="display: none;">
                    <div class="admin-container">
                        <div class="admin-header">
                            <h2>Admin Dashboard</h2>
                        </div>
                        <div class="admin-content">
                            <div class="admin-section">
                                <h3>Users</h3>
                                <table class="admin-table">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Username</th>
                                            <th>Real Name</th>
                                            <th>Status</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="adminUsers">
                                        <!-- Users will be added here -->
                                    </tbody>
                                </table>
                            </div>
                            <div class="admin-section">
                                <h3>Reports</h3>
                                <table class="admin-table">
                                    <thead>
                                        <tr>
                                            <th>Type</th>
                                            <th>Content</th>
                                            <th>Reporter</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="adminReports">
                                        <!-- Reports will be added here -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Modals -->
            <!-- Story Modal -->
            <div class="modal" id="storyModal">
                <div class="story-modal">
                    <div class="story-container">
                        <div class="story-nav prev" id="storyPrev">&#8249;</div>
                        <img src="" alt="Story" class="story-item" id="storyImage">
                        <div class="story-nav next" id="storyNext">&#8250;</div>
                    </div>
                    <div class="story-info" id="storyInfo"></div>
                </div>
            </div>
            
            <!-- Chat Modal -->
            <div class="modal" id="chatModal">
                <div class="chat-box">
                    <div class="chat-header">
                        <div class="back" id="chatBack">&#8249;</div>
                        <div class="chat-header-info">
                            <div class="chat-header-avatar">
                                <img src="default.jpg" alt="User">
                            </div>
                            <div>
                                <div class="chat-header-name">Username</div>
                                <div class="chat-header-username">@username</div>
                            </div>
                        </div>
                        <div class="chat-header-menu" id="chatMenu">
                            <i class="fa fa-ellipsis-v"></i>
                        </div>
                    </div>
                    <div class="chat-messages" id="chatMessages">
                        <!-- Messages will be added here -->
                    </div>
                    <div class="chat-input">
                        <i class="fa fa-smile-o"></i>
                        <i class="fa fa-paperclip"></i>
                        <input type="text" placeholder="Message..." id="chatInput">
                        <button id="sendChat">Send</button>
                    </div>
                </div>
            </div>
            
            <!-- Group Chat Modal -->
            <div class="modal" id="groupChatModal">
                <div class="group-chat-box">
                    <div class="group-chat-header">
                        <div class="back" id="groupChatBack">&#8249;</div>
                        <div class="group-chat-header-info">
                            <div class="group-chat-header-avatar">
                                <img src="group_default.jpg" alt="Group">
                            </div>
                            <div>
                                <div class="group-chat-header-name">Group Name</div>
                            </div>
                        </div>
                        <div class="group-chat-header-menu" id="groupChatMenu">
                            <i class="fa fa-ellipsis-v"></i>
                        </div>
                    </div>
                    <div class="group-chat-messages" id="groupChatMessages">
                        <!-- Messages will be added here -->
                    </div>
                    <div class="group-chat-input">
                        <i class="fa fa-smile-o"></i>
                        <i class="fa fa-paperclip"></i>
                        <input type="text" placeholder="Message..." id="groupChatInput">
                        <button id="sendGroupChat">Send</button>
                    </div>
                </div>
            </div>
            
            <!-- Add Modal -->
            <div class="modal" id="addModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <div class="back" id="addBack">&#8249;</div>
                        <h3>Add Post</h3>
                        <div class="modal-close" id="addClose">&times;</div>
                    </div>
                    <div class="modal-body">
                        <div class="add-options">
                            <div class="add-option active" data-option="post">Post</div>
                            <div class="add-option" data-option="reel">Reel</div>
                            <div class="add-option" data-option="story">Story</div>
                        </div>
                        <div class="add-content">
                            <input type="file" id="addFile" accept="image/*,video/*">
                            <textarea id="addDescription" placeholder="Write a caption..."></textarea>
                            <div class="add-visibility">
                                <label>Visibility:</label>
                                <select id="addVisibility">
                                    <option value="public">Public</option>
                                    <option value="friends">Friends only</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" id="cancelAdd">Cancel</button>
                        <button class="btn btn-primary" id="postAdd">Share</button>
                    </div>
                </div>
            </div>
            
            <!-- Profile Modal -->
            <div class="modal" id="profileModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <div class="back" id="profileBack">&#8249;</div>
                        <h3>Profile</h3>
                        <div class="modal-close" id="profileClose">&times;</div>
                    </div>
                    <div class="modal-body">
                        <!-- Profile content will be added here -->
                    </div>
                </div>
            </div>
            
            <!-- Search Modal -->
            <div class="modal" id="searchModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <div class="back" id="searchBack">&#8249;</div>
                        <h3>Search</h3>
                        <div class="modal-close" id="searchClose">&times;</div>
                    </div>
                    <div class="modal-body">
                        <input type="text" class="input" placeholder="Search..." id="globalSearch">
                        <div class="search-results" id="globalSearchResults">
                            <!-- Results will be added here -->
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Notifications Modal -->
            <div class="modal" id="notificationsModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <div class="back" id="notificationsBack">&#8249;</div>
                        <h3>Notifications</h3>
                        <div class="modal-close" id="notificationsClose">&times;</div>
                    </div>
                    <div class="modal-body">
                        <div class="notifications-container">
                            <!-- Notifications will be added here -->
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Menu Modal -->
            <div class="modal" id="menuModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <div class="back" id="menuBack">&#8249;</div>
                        <h3>Menu</h3>
                        <div class="modal-close" id="menuClose">&times;</div>
                    </div>
                    <div class="modal-body">
                        <div class="menu-container">
                            <div class="menu-item" id="helpSupportModal">
                                <i class="fa fa-question-circle"></i>
                                <div class="menu-item-text">Help & Support</div>
                                <i class="fa fa-chevron-right menu-item-arrow"></i>
                            </div>
                            <div class="menu-item" id="settingsPrivacyModal">
                                <i class="fa fa-cog"></i>
                                <div class="menu-item-text">Settings & Privacy</div>
                                <i class="fa fa-chevron-right menu-item-arrow"></i>
                            </div>
                            <div class="menu-item" id="logoutModal">
                                <i class="fa fa-sign-out"></i>
                                <div class="menu-item-text">Log Out</div>
                                <i class="fa fa-chevron-right menu-item-arrow"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Admin Modal -->
            <div class="modal" id="adminModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <div class="back" id="adminBack">&#8249;</div>
                        <h3>Admin Dashboard</h3>
                        <div class="modal-close" id="adminClose">&times;</div>
                    </div>
                    <div class="modal-body">
                        <div class="admin-container">
                            <div class="admin-header">
                                <h2>Admin Dashboard</h2>
                            </div>
                            <div class="admin-content">
                                <!-- Admin content will be added here -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Update navbar links
        navbarLinks = document.querySelectorAll('.navbar-link');
        pages = document.querySelectorAll('.page');
        
        // Check if user is admin
        if (currentUser && currentUser.is_admin) {
            document.getElementById('adminLink').style.display = 'block';
        }
    }
    
    // Set up event listeners
    function setupEventListeners() {
        // Navbar links
        navbarLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const page = this.getAttribute('data-page');
                showPage(page);
            });
        });
        
        // Story modal
        document.getElementById('storyPrev').addEventListener('click', showPrevStory);
        document.getElementById('storyNext').addEventListener('click', showNextStory);
        
        // Chat modal
        document.getElementById('chatBack').addEventListener('click', closeChatModal);
        document.getElementById('chatMenu').addEventListener('click', showChatMenu);
        document.getElementById('sendChat').addEventListener('click', sendChatMessage);
        document.getElementById('chatInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
        
        // Group chat modal
        document.getElementById('groupChatBack').addEventListener('click', closeGroupChatModal);
        document.getElementById('groupChatMenu').addEventListener('click', showGroupChatMenu);
        document.getElementById('sendGroupChat').addEventListener('click', sendGroupChatMessage);
        document.getElementById('groupChatInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendGroupChatMessage();
            }
        });
        
        // Add modal
        document.getElementById('addBack').addEventListener('click', closeAddModal);
        document.getElementById('addClose').addEventListener('click', closeAddModal);
        document.getElementById('cancelAdd').addEventListener('click', closeAddModal);
        document.getElementById('postAdd').addEventListener('click', postAddContent);
        
        // Profile modal
        document.getElementById('profileBack').addEventListener('click', closeProfileModal);
        document.getElementById('profileClose').addEventListener('click', closeProfileModal);
        
        // Search modal
        document.getElementById('searchBack').addEventListener('click', closeSearchModal);
        document.getElementById('searchClose').addEventListener('click', closeSearchModal);
        document.getElementById('globalSearch').addEventListener('input', searchContent);
        
        // Notifications modal
        document.getElementById('notificationsBack').addEventListener('click', closeNotificationsModal);
        document.getElementById('notificationsClose').addEventListener('click', closeNotificationsModal);
        
        // Menu modal
        document.getElementById('menuBack').addEventListener('click', closeMenuModal);
        document.getElementById('menuClose').addEventListener('click', closeMenuModal);
        
        // Admin modal
        document.getElementById('adminBack').addEventListener('click', closeAdminModal);
        document.getElementById('adminClose').addEventListener('click', closeAdminModal);
        
        // Page-specific events
        setupFriendsPageEvents();
        setupInboxPageEvents();
        setupProfilePageEvents();
        setupSearchPageEvents();
        setupMenuPageEvents();
    }
    
    // Set up friends page events
    function setupFriendsPageEvents() {
        const friendsTabs = document.querySelectorAll('.friends-tab');
        friendsTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const tabName = this.getAttribute('data-tab');
                showFriendsTab(tabName);
            });
        });
    }
    
    // Set up inbox page events
    function setupInboxPageEvents() {
        const inboxTabs = document.querySelectorAll('.inbox-tab');
        inboxTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const tabName = this.getAttribute('data-tab');
                showInboxTab(tabName);
            });
        });
    }
    
    // Set up profile page events
    function setupProfilePageEvents() {
        const profileTabs = document.querySelectorAll('.profile-tab');
        profileTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const tabName = this.getAttribute('data-tab');
                showProfileTab(tabName);
            });
        });
        
        document.getElementById('editProfile').addEventListener('click', openEditProfileModal);
        document.getElementById('shareProfile').addEventListener('click', shareProfile);
        document.getElementById('editProfilePic').addEventListener('click', changeProfilePicture);
    }
    
    // Set up search page events
    function setupSearchPageEvents() {
        const searchTabs = document.querySelectorAll('.search-tab');
        searchTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const tabName = this.getAttribute('data-tab');
                showSearchTab(tabName);
            });
        });
        
        document.getElementById('searchInput').addEventListener('input', function() {
            const query = this.value;
            if (query.length > 0) {
                performSearch(query);
            } else {
                document.getElementById('searchResults').innerHTML = '';
            }
        });
    }
    
    // Set up menu page events
    function setupMenuPageEvents() {
        document.getElementById('helpSupport').addEventListener('click', showHelpSupport);
        document.getElementById('settingsPrivacy').addEventListener('click', showSettingsPrivacy);
        document.getElementById('logout').addEventListener('click', logout);
        
        document.getElementById('helpSupportModal').addEventListener('click', showHelpSupport);
        document.getElementById('settingsPrivacyModal').addEventListener('click', showSettingsPrivacy);
        document.getElementById('logoutModal').addEventListener('click', logout);
    }
    
    // Show a page
    function showPage(page) {
        // Hide all pages
        pages.forEach(p => {
            p.style.display = 'none';
        });
        
        // Show the requested page
        document.getElementById(page).style.display = 'block';
        
        // Update active link
        navbarLinks.forEach(link => {
            if (link.getAttribute('data-page') === page) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
        
        // Update active page
        activePage = page;
        
        // Load data for the page
        loadPageData(page);
    }
    
    // Load data for a page
    function loadPageData(page) {
        switch (page) {
            case 'home':
                loadHomeData();
                break;
            case 'reels':
                loadReelsData();
                break;
            case 'friends':
                loadFriendsData();
                break;
            case 'inbox':
                loadInboxData();
                break;
            case 'profile':
                loadProfileData();
                break;
            case 'search':
                loadSearchData();
                break;
            case 'add':
                loadAddData();
                break;
            case 'notifications':
                loadNotificationsData();
                break;
            case 'menu':
                loadMenuData();
                break;
            case 'admin':
                loadAdminData();
                break;
        }
    }
    
    // Load initial data
    function loadData() {
        // In a real app, we would fetch data from the server
        // For now, we'll use mock data
        currentUser = {
            id: 1,
            username: 'john_doe',
            real_name: 'John Doe',
            profile_pic: 'default.jpg',
            bio: 'Just a regular user',
            is_admin: 0
        };
        
        // Load data for the current page
        loadPageData(activePage);
    }
    
    // Load home page data
    function loadHomeData() {
        // Load stories
        loadStories();
        
        // Load posts
        loadPosts();
    }
    
    // Load stories
    function loadStories() {
        const storiesContainer = document.getElementById('storiesContainer');
        storiesContainer.innerHTML = '';
        
        // Mock data
        const mockStories = [
            { id: 1, user: { id: 2, username: 'jane_doe', real_name: 'Jane Doe', profile_pic: 'default.jpg' }, content_url: 'https://placehold.co/60x60', created_at: '2023-05-15T10:30:00Z' },
            { id: 2, user: { id: 3, username: 'bob_smith', real_name: 'Bob Smith', profile_pic: 'default.jpg' }, content_url: 'https://placehold.co/60x60', created_at: '2023-05-15T09:15:00Z' },
            { id: 3, user: { id: 4, username: 'alice_jones', real_name: 'Alice Jones', profile_pic: 'default.jpg' }, content_url: 'https://placehold.co/60x60', created_at: '2023-05-15T08:45:00Z' }
        ];
        
        // Add "Add Story" item
        const addStory = document.createElement('div');
        addStory.className = 'story';
        addStory.innerHTML = `
            <div class="story-avatar add">
                <i class="fa fa-plus"></i>
            </div>
            <div class="story-username">Add Story</div>
        `;
        addStory.addEventListener('click', openAddModal);
        storiesContainer.appendChild(addStory);
        
        // Add stories
        mockStories.forEach(story => {
            const storyEl = document.createElement('div');
            storyEl.className = 'story';
            storyEl.innerHTML = `
                <div class="story-avatar">
                    <img src="${story.user.profile_pic}" alt="${story.user.real_name}">
                </div>
                <div class="story-username">${story.user.real_name}</div>
            `;
            storyEl.addEventListener('click', () => showStory(story));
            storiesContainer.appendChild(storyEl);
        });
        
        // Store stories data
        storiesData = mockStories;
    }
    
    // Show a story
    function showStory(story) {
        const storyImage = document.getElementById('storyImage');
        storyImage.src = story.content_url;
        
        const storyInfo = document.getElementById('storyInfo');
        storyInfo.textContent = story.user.real_name;
        
        storyIndex = storiesData.findIndex(s => s.id === story.id);
        
        storyModal.classList.add('active');
    }
    
    // Show previous story
    function showPrevStory() {
        if (storyIndex > 0) {
            storyIndex--;
            const story = storiesData[storyIndex];
            document.getElementById('storyImage').src = story.content_url;
            document.getElementById('storyInfo').textContent = story.user.real_name;
        }
    }
    
    // Show next story
    function showNextStory() {
        if (storyIndex < storiesData.length - 1) {
            storyIndex++;
            const story = storiesData[storyIndex];
            document.getElementById('storyImage').src = story.content_url;
            document.getElementById('storyInfo').textContent = story.user.real_name;
        } else {
            closeStoryModal();
        }
    }
    
    // Close story modal
    function closeStoryModal() {
        storyModal.classList.remove('active');
    }
    
    // Load posts
    function loadPosts() {
        const postsContainer = document.getElementById('postsContainer');
        postsContainer.innerHTML = '';
        
        // Mock data
        const mockPosts = [
            {
                post: {
                    id: 1,
                    user_id: 2,
                    content_type: 'image',
                    content: '',
                    description: 'Beautiful sunset at the beach',
                    media_url: 'https://placehold.co/600x400',
                    visibility: 'public',
                    likes: 24,
                    comments: 8,
                    shares: 3,
                    saves: 5,
                    views: 156,
                    created_at: '2023-05-15T14:30:00Z',
                    username: 'jane_doe',
                    real_name: 'Jane Doe',
                    profile_pic: 'default.jpg'
                },
                comments: [
                    { id: 1, user_id: 3, content: 'Amazing photo!', created_at: '2023-05-15T14:35:00Z', username: 'bob_smith', real_name: 'Bob Smith', profile_pic: 'default.jpg' },
                    { id: 2, user_id: 1, content: 'Thanks!', created_at: '2023-05-15T14:40:00Z', username: 'jane_doe', real_name: 'Jane Doe', profile_pic: 'default.jpg' }
                ]
            },
            {
                post: {
                    id: 2,
                    user_id: 3,
                    content_type: 'text',
                    content: 'Just finished reading an amazing book about AI and its impact on society. Highly recommend it to anyone interested in technology and the future.',
                    description: '',
                    media_url: '',
                    visibility: 'public',
                    likes: 18,
                    comments: 12,
                    shares: 7,
                    saves: 3,
                    views: 89,
                    created_at: '2023-05-14T10:15:00Z',
                    username: 'bob_smith',
                    real_name: 'Bob Smith',
                    profile_pic: 'default.jpg'
                },
                comments: [
                    { id: 3, user_id: 1, content: 'What book was it?', created_at: '2023-05-14T10:20:00Z', username: 'john_doe', real_name: 'John Doe', profile_pic: 'default.jpg' },
                    { id: 4, user_id: 3, content: 'It\'s called "The Future of AI" by Dr. Emily Johnson.', created_at: '2023-05-14T10:25:00Z', username: 'bob_smith', real_name: 'Bob Smith', profile_pic: 'default.jpg' }
                ]
            }
        ];
        
        mockPosts.forEach(item => {
            const post = item.post;
            const postEl = document.createElement('div');
            postEl.className = 'post';
            postEl.innerHTML = `
                <div class="post-header">
                    <img src="${post.profile_pic}" alt="${post.real_name}" class="post-avatar">
                    <div class="post-user-info">
                        <div class="post-username">${post.real_name}</div>
                        <div class="post-time">${formatTimeAgo(post.created_at)}</div>
                    </div>
                    <div class="post-more">
                        <i class="fa fa-ellipsis-h"></i>
                    </div>
                </div>
                ${post.media_url ? `<img src="${post.media_url}" alt="Post image" class="post-image">` : ''}
                <div class="post-actions">
                    <div class="post-action like">
                        <i class="fa fa-heart-o"></i>
                    </div>
                    <div class="post-action">
                        <i class="fa fa-comment-o"></i>
                    </div>
                    <div class="post-action">
                        <i class="fa fa-paper-plane-o"></i>
                    </div>
                    <div class="post-action save">
                        <i class="fa fa-bookmark-o"></i>
                    </div>
                </div>
                <div class="post-likes">${post.likes} likes</div>
                <div class="post-description">
                    <strong>${post.real_name}</strong> ${post.description || post.content}
                </div>
                <div class="post-comments">${item.comments.length} comments</div>
                <div class="post-add-comment">
                    <input type="text" placeholder="Add a comment...">
                    <button disabled>Post</button>
                </div>
            `;
            
            // Add event listeners
            const likeBtn = postEl.querySelector('.post-action.like');
            likeBtn.addEventListener('click', function() {
                const isLiked = this.classList.contains('liked');
                if (isLiked) {
                    this.innerHTML = '<i class="fa fa-heart-o"></i>';
                    this.classList.remove('liked');
                    post.likes--;
                } else {
                    this.innerHTML = '<i class="fa fa-heart"></i>';
                    this.classList.add('liked');
                    post.likes++;
                }
                postEl.querySelector('.post-likes').textContent = `${post.likes} likes`;
            });
            
            const commentInput = postEl.querySelector('.post-add-comment input');
            const commentBtn = postEl.querySelector('.post-add-comment button');
            commentInput.addEventListener('input', function() {
                commentBtn.disabled = this.value.trim() === '';
            });
            
            commentBtn.addEventListener('click', function() {
                const comment = commentInput.value.trim();
                if (comment) {
                    item.comments.unshift({
                        id: item.comments.length + 1,
                        user_id: currentUser.id,
                        content: comment,
                        created_at: new Date().toISOString(),
                        username: currentUser.username,
                        real_name: currentUser.real_name,
                        profile_pic: currentUser.profile_pic
                    });
                    postEl.querySelector('.post-comments').textContent = `${item.comments.length} comments`;
                    commentInput.value = '';
                    commentBtn.disabled = true;
                }
            });
            
            postsContainer.appendChild(postEl);
        });
    }
    
    // Load reels data
    function loadReelsData() {
        const reelsContainer = document.getElementById('reelsContainer');
        reelsContainer.innerHTML = '';
        
        // Mock data
        const mockReels = [
            {
                reel: {
                    id: 1,
                    user_id: 2,
                    video_url: 'https://placehold.co/300x600',
                    description: 'Dancing to my favorite song',
                    visibility: 'public',
                    likes: 156,
                    comments: 23,
                    shares: 12,
                    saves: 45,
                    views: 2345,
                    created_at: '2023-05-15T16:20:00Z',
                    username: 'jane_doe',
                    real_name: 'Jane Doe',
                    profile_pic: 'default.jpg'
                },
                comments: [
                    { id: 1, user_id: 3, content: 'Great dance!', created_at: '2023-05-15T16:25:00Z', username: 'bob_smith', real_name: 'Bob Smith', profile_pic: 'default.jpg' },
                    { id: 2, user_id: 1, content: 'You killed it!', created_at: '2023-05-15T16:30:00Z', username: 'john_doe', real_name: 'John Doe', profile_pic: 'default.jpg' }
                ]
            },
            {
                reel: {
                    id: 2,
                    user_id: 3,
                    video_url: 'https://placehold.co/300x600',
                    description: 'Cooking my favorite recipe',
                    visibility: 'public',
                    likes: 89,
                    comments: 15,
                    shares: 8,
                    saves: 23,
                    views: 1567,
                    created_at: '2023-05-14T18:45:00Z',
                    username: 'bob_smith',
                    real_name: 'Bob Smith',
                    profile_pic: 'default.jpg'
                },
                comments: [
                    { id: 3, user_id: 1, content: 'Looks delicious!', created_at: '2023-05-14T18:50:00Z', username: 'john_doe', real_name: 'John Doe', profile_pic: 'default.jpg' },
                    { id: 4, user_id: 2, content: 'Can I get the recipe?', created_at: '2023-05-14T18:55:00Z', username: 'jane_doe', real_name: 'Jane Doe', profile_pic: 'default.jpg' }
                ]
            }
        ];
        
        mockReels.forEach(item => {
            const reel = item.reel;
            const reelEl = document.createElement('div');
            reelEl.className = 'reel';
            reelEl.innerHTML = `
                <video class="reel-video" src="${reel.video_url}" muted loop></video>
                <div class="reel-actions">
                    <div class="reel-action follow">
                        <i class="fa fa-plus"></i>
                        <span>Follow</span>
                    </div>
                    <div class="reel-action like">
                        <i class="fa fa-heart-o"></i>
                        <span>${reel.likes}</span>
                    </div>
                    <div class="reel-action">
                        <i class="fa fa-comment-o"></i>
                        <span>${reel.comments}</span>
                    </div>
                    <div class="reel-action">
                        <i class="fa fa-paper-plane-o"></i>
                        <span>${reel.shares}</span>
                    </div>
                    <div class="reel-action save">
                        <i class="fa fa-bookmark-o"></i>
                        <span>${reel.saves}</span>
                    </div>
                    <div class="reel-action">
                        <i class="fa fa-download"></i>
                        <span>Save</span>
                    </div>
                </div>
                <div class="reel-info">
                    <div class="reel-username">${reel.real_name}</div>
                    <div class="reel-description">${reel.description}</div>
                    <div class="reel-music">
                        <i class="fa fa-music"></i>
                        <span>Original Sound</span>
                    </div>
                </div>
            `;
            
            // Add event listeners
            const likeBtn = reelEl.querySelector('.reel-action.like');
            likeBtn.addEventListener('click', function() {
                const isLiked = this.classList.contains('liked');
                if (isLiked) {
                    this.querySelector('i').className = 'fa fa-heart-o';
                    this.classList.remove('liked');
                    reel.likes--;
                } else {
                    this.querySelector('i').className = 'fa fa-heart';
                    this.classList.add('liked');
                    reel.likes++;
                }
                this.querySelector('span').textContent = reel.likes;
            });
            
            reelsContainer.appendChild(reelEl);
        });
    }
    
    // Load friends data
    function loadFriendsData() {
        showFriendsTab('followers');
    }
    
    // Show a friends tab
    function showFriendsTab(tabName) {
        // Update active tab
        document.querySelectorAll('.friends-tab').forEach(tab => {
            if (tab.getAttribute('data-tab') === tabName) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
        
        // Load data for the tab
        const friendsList = document.getElementById('friendsList');
        friendsList.innerHTML = '';
        
        // Mock data
        const mockData = {
            followers: [
                { id: 2, username: 'jane_doe', real_name: 'Jane Doe', profile_pic: 'default.jpg', mutual_friends: 3 },
                { id: 3, username: 'bob_smith', real_name: 'Bob Smith', profile_pic: 'default.jpg', mutual_friends: 1 },
                { id: 4, username: 'alice_jones', real_name: 'Alice Jones', profile_pic: 'default.jpg', mutual_friends: 0 }
            ],
            following: [
                { id: 2, username: 'jane_doe', real_name: 'Jane Doe', profile_pic: 'default.jpg', mutual_friends: 3 },
                { id: 5, username: 'charlie_brown', real_name: 'Charlie Brown', profile_pic: 'default.jpg', mutual_friends: 2 }
            ],
            friends: [
                { id: 2, username: 'jane_doe', real_name: 'Jane Doe', profile_pic: 'default.jpg', mutual_friends: 3 },
                { id: 5, username: 'charlie_brown', real_name: 'Charlie Brown', profile_pic: 'default.jpg', mutual_friends: 2 }
            ],
            requests: [
                { id: 6, username: 'david_wilson', real_name: 'David Wilson', profile_pic: 'default.jpg', mutual_friends: 1 },
                { id: 7, username: 'emily_davis', real_name: 'Emily Davis', profile_pic: 'default.jpg', mutual_friends: 0 }
            ],
            suggested: [
                { id: 8, username: 'frank_miller', real_name: 'Frank Miller', profile_pic: 'default.jpg', mutual_friends: 4 },
                { id: 9, username: 'grace_taylor', real_name: 'Grace Taylor', profile_pic: 'default.jpg', mutual_friends: 3 }
            ]
        };
        
        const data = mockData[tabName] || [];
        
        data.forEach(user => {
            const friendEl = document.createElement('div');
            friendEl.className = 'friend-item';
            
            if (tabName === 'requests') {
                friendEl.innerHTML = `
                    <img src="${user.profile_pic}" alt="${user.real_name}" class="friend-avatar">
                    <div class="friend-info">
                        <div class="friend-name">${user.real_name}</div>
                        <div class="friend-mutual">${user.mutual_friends} mutual friend${user.mutual_friends !== 1 ? 's' : ''}</div>
                    </div>
                    <div class="friend-actions">
                        <button class="friend-action accept">Accept</button>
                        <button class="friend-action decline">Decline</button>
                        <button class="friend-action block">Block</button>
                    </div>
                `;
                
                // Add event listeners
                friendEl.querySelector('.friend-action.accept').addEventListener('click', function() {
                    alert('Friend request accepted');
                    loadFriendsData();
                });
                
                friendEl.querySelector('.friend-action.decline').addEventListener('click', function() {
                    alert('Friend request declined');
                    loadFriendsData();
                });
                
                friendEl.querySelector('.friend-action.block').addEventListener('click', function() {
                    alert('User blocked');
                    loadFriendsData();
                });
            } else if (tabName === 'suggested') {
                friendEl.innerHTML = `
                    <img src="${user.profile_pic}" alt="${user.real_name}" class="friend-avatar">
                    <div class="friend-info">
                        <div class="friend-name">${user.real_name}</div>
                        <div class="friend-mutual">${user.mutual_friends} mutual friend${user.mutual_friends !== 1 ? 's' : ''}</div>
                    </div>
                    <div class="friend-actions">
                        <button class="friend-action follow">Follow</button>
                        <button class="friend-action remove">Remove</button>
                        <button class="friend-action block">Block</button>
                    </div>
                `;
                
                // Add event listeners
                friendEl.querySelector('.friend-action.follow').addEventListener('click', function() {
                    alert('Followed user');
                    loadFriendsData();
                });
                
                friendEl.querySelector('.friend-action.remove').addEventListener('click', function() {
                    alert('Removed from suggestions');
                    loadFriendsData();
                });
                
                friendEl.querySelector('.friend-action.block').addEventListener('click', function() {
                    alert('User blocked');
                    loadFriendsData();
                });
            } else {
                friendEl.innerHTML = `
                    <img src="${user.profile_pic}" alt="${user.real_name}" class="friend-avatar">
                    <div class="friend-info">
                        <div class="friend-name">${user.real_name}</div>
                        <div class="friend-mutual">${user.mutual_friends} mutual friend${user.mutual_friends !== 1 ? 's' : ''}</div>
                    </div>
                    <div class="friend-actions">
                        <button class="friend-action message">Message</button>
                        <button class="friend-action unfollow">Unfollow</button>
                    </div>
                `;
                
                // Add event listeners
                friendEl.querySelector('.friend-action.message').addEventListener('click', function() {
                    openChatModal(user);
                });
                
                friendEl.querySelector('.friend-action.unfollow').addEventListener('click', function() {
                    if (tabName === 'following') {
                        alert('Unfollowed user');
                        loadFriendsData();
                    } else {
                        alert('Unfollow user');
                        loadFriendsData();
                    }
                });
            }
            
            // Add click event to open profile
            friendEl.addEventListener('click', function(e) {
                if (!e.target.closest('.friend-action')) {
                    openProfileModal(user);
                }
            });
            
            friendsList.appendChild(friendEl);
        });
        
        // Update counts
        document.getElementById('followersCount').textContent = mockData.followers.length;
        document.getElementById('followingCount').textContent = mockData.following.length;
        document.getElementById('friendsCount').textContent = mockData.friends.length;
        document.getElementById('requestsCount').textContent = mockData.requests.length;
        document.getElementById('suggestedCount').textContent = mockData.suggested.length;
    }
    
    // Load inbox data
    function loadInboxData() {
        showInboxTab('chats');
    }
    
    // Show an inbox tab
    function showInboxTab(tabName) {
        // Update active tab
        document.querySelectorAll('.inbox-tab').forEach(tab => {
            if (tab.getAttribute('data-tab') === tabName) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
        
        // Load data for the tab
        const inboxList = document.getElementById('inboxList');
        inboxList.innerHTML = '';
        
        // Mock data
        const mockData = {
            chats: [
                { id: 2, username: 'jane_doe', real_name: 'Jane Doe', profile_pic: 'default.jpg', last_message: 'Hey, how are you doing?', time: '2:30 PM', unread_count: 1 },
                { id: 3, username: 'bob_smith', real_name: 'Bob Smith', profile_pic: 'default.jpg', last_message: 'Did you see the new movie?', time: '1:15 PM', unread_count: 0 },
                { id: 4, username: 'alice_jones', real_name: 'Alice Jones', profile_pic: 'default.jpg', last_message: 'Thanks for the help!', time: '12:45 PM', unread_count: 0 }
            ],
            groups: [
                { id: 1, name: 'Family', profile_pic: 'group_default.jpg', last_message: 'Mom: Dinner at 7?', time: '3:20 PM', unread_count: 2 },
                { id: 2, name: 'Work Team', profile_pic: 'group_default.jpg', last_message: 'John: Meeting moved to Friday', time: '2:10 PM', unread_count: 0 }
            ]
        };
        
        const data = mockData[tabName] || [];
        
        data.forEach(item => {
            const chatEl = document.createElement('div');
            chatEl.className = 'chat-item';
            
            if (tabName === 'chats') {
                chatEl.innerHTML = `
                    <img src="${item.profile_pic}" alt="${item.real_name}" class="chat-avatar">
                    <div class="chat-info">
                        <div class="chat-name">${item.real_name}</div>
                        <div class="chat-last-message">${item.last_message}</div>
                    </div>
                    <div class="chat-time">${item.time}</div>
                    ${item.unread_count > 0 ? `<div class="chat-unread">${item.unread_count}</div>` : ''}
                `;
                
                chatEl.addEventListener('click', () => openChatModal(item));
            } else {
                chatEl.innerHTML = `
                    <img src="${item.profile_pic}" alt="${item.name}" class="chat-avatar">
                    <div class="chat-info">
                        <div class="chat-name">${item.name}</div>
                        <div class="chat-last-message">${item.last_message}</div>
                    </div>
                    <div class="chat-time">${item.time}</div>
                    ${item.unread_count > 0 ? `<div class="chat-unread">${item.unread_count}</div>` : ''}
                `;
                
                chatEl.addEventListener('click', () => openGroupChatModal(item));
            }
            
            inboxList.appendChild(chatEl);
        });
        
        // Update counts
        document.getElementById('chatsCount').textContent = mockData.chats.length;
        document.getElementById('groupsCount').textContent = mockData.groups.length;
    }
    
    // Open chat modal
    function openChatModal(user) {
        // Update header
        document.querySelector('.chat-header-name').textContent = user.real_name;
        document.querySelector('.chat-header-username').textContent = `@${user.username}`;
        document.querySelector('.chat-header-avatar img').src = user.profile_pic;
        
        // Clear messages
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';
        
        // Mock messages
        const mockMessages = [
            { id: 1, sender_id: user.id, content: 'Hey, how are you doing?', created_at: '2023-05-15T14:30:00Z', type: 'received' },
            { id: 2, sender_id: currentUser.id, content: 'I\'m good, thanks! How about you?', created_at: '2023-05-15T14:32:00Z', type: 'sent' },
            { id: 3, sender_id: user.id, content: 'Doing well! Just finished work.', created_at: '2023-05-15T14:35:00Z', type: 'received' }
        ];
        
        mockMessages.forEach(msg => {
            const messageEl = document.createElement('div');
            messageEl.className = `message ${msg.type}`;
            messageEl.innerHTML = `
                ${msg.content}
                <div class="message-time">${formatTimeAgo(msg.created_at)}</div>
            `;
            chatMessages.appendChild(messageEl);
        });
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Show modal
        chatModal.classList.add('active');
    }
    
    // Close chat modal
    function closeChatModal() {
        chatModal.classList.remove('active');
    }
    
    // Show chat menu
    function showChatMenu() {
        alert('Chat menu');
    }
    
    // Send chat message
    function sendChatMessage() {
        const input = document.getElementById('chatInput');
        const content = input.value.trim();
        
        if (content) {
            const chatMessages = document.getElementById('chatMessages');
            const messageEl = document.createElement('div');
            messageEl.className = 'message sent';
            messageEl.innerHTML = `
                ${content}
                <div class="message-time">Just now</div>
            `;
            chatMessages.appendChild(messageEl);
            
            // Clear input
            input.value = '';
            document.getElementById('sendChat').disabled = true;
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Simulate response
            setTimeout(() => {
                const responseEl = document.createElement('div');
                responseEl.className = 'message received';
                responseEl.innerHTML = `
                    Thanks for your message!
                    <div class="message-time">Just now</div>
                `;
                chatMessages.appendChild(responseEl);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 1000);
        }
    }
    
    // Open group chat modal
    function openGroupChatModal(group) {
        // Update header
        document.querySelector('.group-chat-header-name').textContent = group.name;
        document.querySelector('.group-chat-header-avatar img').src = group.profile_pic;
        
        // Clear messages
        const groupChatMessages = document.getElementById('groupChatMessages');
        groupChatMessages.innerHTML = '';
        
        // Mock messages
        const mockMessages = [
            { id: 1, sender_id: 2, content: 'Hey everyone, how are you doing?', created_at: '2023-05-15T14:30:00Z', username: 'jane_doe', real_name: 'Jane Doe', profile_pic: 'default.jpg' },
            { id: 2, sender_id: currentUser.id, content: 'I\'m good, thanks!', created_at: '2023-05-15T14:32:00Z', username: currentUser.username, real_name: currentUser.real_name, profile_pic: currentUser.profile_pic },
            { id: 3, sender_id: 3, content: 'Doing well! Just finished work.', created_at: '2023-05-15T14:35:00Z', username: 'bob_smith', real_name: 'Bob Smith', profile_pic: 'default.jpg' }
        ];
        
        mockMessages.forEach(msg => {
            const messageEl = document.createElement('div');
            messageEl.className = `group-message ${msg.sender_id === currentUser.id ? 'sent' : 'received'}`;
            messageEl.innerHTML = `
                <div class="group-message-header">
                    ${msg.sender_id !== currentUser.id ? `
                        <img src="${msg.profile_pic}" alt="${msg.real_name}" class="group-message-avatar">
                        <div class="group-message-username">${msg.real_name}</div>
                    ` : ''}
                </div>
                ${msg.content}
                <div class="group-message-time">${formatTimeAgo(msg.created_at)}</div>
            `;
            groupChatMessages.appendChild(messageEl);
        });
        
        // Scroll to bottom
        groupChatMessages.scrollTop = groupChatMessages.scrollHeight;
        
        // Show modal
        groupChatModal.classList.add('active');
    }
    
    // Close group chat modal
    function closeGroupChatModal() {
        groupChatModal.classList.remove('active');
    }
    
    // Show group chat menu
    function showGroupChatMenu() {
        alert('Group chat menu');
    }
    
    // Send group chat message
    function sendGroupChatMessage() {
        const input = document.getElementById('groupChatInput');
        const content = input.value.trim();
        
        if (content) {
            const groupChatMessages = document.getElementById('groupChatMessages');
            const messageEl = document.createElement('div');
            messageEl.className = 'group-message sent';
            messageEl.innerHTML = `
                <div class="group-message-header"></div>
                ${content}
                <div class="group-message-time">Just now</div>
            `;
            groupChatMessages.appendChild(messageEl);
            
            // Clear input
            input.value = '';
            document.getElementById('sendGroupChat').disabled = true;
            
            // Scroll to bottom
            groupChatMessages.scrollTop = groupChatMessages.scrollHeight;
            
            // Simulate response
            setTimeout(() => {
                const responseEl = document.createElement('div');
                responseEl.className = 'group-message received';
                responseEl.innerHTML = `
                    <div class="group-message-header">
                        <img src="default.jpg" alt="Jane Doe" class="group-message-avatar">
                        <div class="group-message-username">Jane Doe</div>
                    </div>
                    Thanks for your message!
                    <div class="group-message-time">Just now</div>
                `;
                groupChatMessages.appendChild(responseEl);
                groupChatMessages.scrollTop = groupChatMessages.scrollHeight;
            }, 1000);
        }
    }
    
    // Load profile data
    function loadProfileData() {
        // Update profile info
        document.getElementById('profileAvatar').src = currentUser.profile_pic;
        document.getElementById('profileUsername').textContent = currentUser.real_name;
        document.getElementById('profileRecoveryKey').textContent = `Recovery Key: ${currentUser.unique_key || 'ABC123'}`;
        
        // Mock counts
        document.getElementById('postsCount').textContent = '12';
        document.getElementById('followersCountProfile').textContent = '245';
        document.getElementById('followingCountProfile').textContent = '189';
        document.getElementById('likesCount').textContent = '1.2K';
        
        // Update bio
        document.getElementById('profileBio').textContent = currentUser.bio || 'No bio available';
        
        // Show posts tab
        showProfileTab('posts');
    }
    
    // Show a profile tab
    function showProfileTab(tabName) {
        // Update active tab
        document.querySelectorAll('.profile-tab').forEach(tab => {
            if (tab.getAttribute('data-tab') === tabName) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
        
        // Load data for the tab
        const profileContent = document.getElementById('profileContent');
        profileContent.innerHTML = '';
        
        // Mock data
        const mockData = {
            posts: Array(12).fill().map((_, i) => ({
                id: i + 1,
                media_url: `https://placehold.co/300x300?text=Post+${i + 1}`,
                content_type: 'image'
            })),
            saved: Array(9).fill().map((_, i) => ({
                id: i + 1,
                media_url: `https://placehold.co/300x300?text=Saved+${i + 1}`,
                content_type: 'image'
            })),
            reposts: Array(6).fill().map((_, i) => ({
                id: i + 1,
                media_url: `https://placehold.co/300x300?text=Repost+${i + 1}`,
                content_type: 'image',
                original_user: 'jane_doe',
                original_real_name: 'Jane Doe'
            })),
            liked: Array(15).fill().map((_, i) => ({
                id: i + 1,
                media_url: `https://placehold.co/300x300?text=Liked+${i + 1}`,
                content_type: 'image'
            })),
            reels: Array(8).fill().map((_, i) => ({
                id: i + 1,
                media_url: `https://placehold.co/300x600?text=Reel+${i + 1}`,
                content_type: 'video'
            }))
        };
        
        const data = mockData[tabName] || [];
        
        data.forEach(item => {
            const itemEl = document.createElement('div');
            itemEl.className = 'profile-item';
            itemEl.innerHTML = `
                <img src="${item.media_url}" alt="Content">
                ${tabName !== 'posts' ? '<div class="profile-item delete"><i class="fa fa-trash"></i></div>' : ''}
            `;
            
            // Add delete event
            const deleteBtn = itemEl.querySelector('.delete');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    if (confirm('Are you sure you want to delete this content?')) {
                        alert('Content deleted');
                        loadProfileData();
                    }
                });
            }
            
            profileContent.appendChild(itemEl);
        });
    }
    
    // Open edit profile modal
    function openEditProfileModal() {
        alert('Edit profile');
    }
    
    // Share profile
    function shareProfile() {
        alert('Profile shared');
    }
    
    // Change profile picture
    function changeProfilePicture() {
        alert('Change profile picture');
    }
    
    // Open profile modal
    function openProfileModal(user) {
        const modalBody = document.querySelector('#profileModal .modal-body');
        modalBody.innerHTML = `
            <div class="profile-container">
                <div class="profile-header">
                    <div class="profile-avatar">
                        <img src="${user.profile_pic}" alt="${user.real_name}" id="modalProfileAvatar">
                    </div>
                    <div class="profile-info">
                        <div class="profile-username" id="modalProfileUsername">${user.real_name}</div>
                        <div class="profile-counts">
                            <div class="profile-count">
                                <div class="profile-count-number" id="modalPostsCount">8</div>
                                <div class="profile-count-label">Posts</div>
                            </div>
                            <div class="profile-count">
                                <div class="profile-count-number" id="modalFollowersCount">156</div>
                                <div class="profile-count-label">Followers</div>
                            </div>
                            <div class="profile-count">
                                <div class="profile-count-number" id="modalFollowingCount">123</div>
                                <div class="profile-count-label">Following</div>
                            </div>
                        </div>
                        <div class="profile-actions">
                            <button class="profile-action follow" id="followUser">Follow</button>
                            <button class="profile-action message" id="messageUser">Message</button>
                        </div>
                    </div>
                </div>
                <div class="profile-bio" id="modalProfileBio">
                    ${user.bio || 'No bio available'}
                </div>
                ${user.mutual_friends && user.mutual_friends.length > 0 ? `
                    <div class="profile-info-section">
                        <h3>2 mutual friends</h3>
                        <div class="profile-info-item">${user.mutual_friends[0].real_name}</div>
                        <div class="profile-info-item">${user.mutual_friends[1].real_name}</div>
                    </div>
                ` : ''}
                <div class="profile-tabs">
                    <div class="profile-tab active" data-tab="posts">Posts</div>
                    <div class="profile-tab" data-tab="reels">Reels</div>
                </div>
                <div class="profile-content" id="modalProfileContent">
                    <!-- Content will be added here -->
                </div>
            </div>
        `;
        
        // Add event listeners
        document.getElementById('followUser').addEventListener('click', function() {
            const isFollowing = this.textContent === 'Following';
            if (isFollowing) {
                this.textContent = 'Follow';
                this.classList.remove('following');
            } else {
                this.textContent = 'Following';
                this.classList.add('following');
            }
        });
        
        document.getElementById('messageUser').addEventListener('click', function() {
            closeProfileModal();
            openChatModal(user);
        });
        
        // Show posts tab
        showModalProfileTab('posts');
        
        // Show modal
        profileModal.classList.add('active');
    }
    
    // Show a modal profile tab
    function showModalProfileTab(tabName) {
        // Update active tab
        document.querySelectorAll('#profileModal .profile-tab').forEach(tab => {
            if (tab.getAttribute('data-tab') === tabName) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
        
        // Load data for the tab
        const profileContent = document.getElementById('modalProfileContent');
        profileContent.innerHTML = '';
        
        // Mock data
        const mockData = {
            posts: Array(8).fill().map((_, i) => ({
                id: i + 1,
                media_url: `https://placehold.co/300x300?text=Post+${i + 1}`,
                content_type: 'image'
            })),
            reels: Array(5).fill().map((_, i) => ({
                id: i + 1,
                media_url: `https://placehold.co/300x600?text=Reel+${i + 1}`,
                content_type: 'video'
            }))
        };
        
        const data = mockData[tabName] || [];
        
        data.forEach(item => {
            const itemEl = document.createElement('div');
            itemEl.className = 'profile-item';
            itemEl.innerHTML = `
                <img src="${item.media_url}" alt="Content">
            `;
            profileContent.appendChild(itemEl);
        });
    }
    
    // Close profile modal
    function closeProfileModal() {
        profileModal.classList.remove('active');
    }
    
    // Load search data
    function loadSearchData() {
        // Clear results
        document.getElementById('searchResults').innerHTML = '';
    }
    
    // Perform search
    function performSearch(query) {
        const searchResults = document.getElementById('searchResults');
        searchResults.innerHTML = '';
        
        // Mock data
        const mockResults = {
            users: [
                { id: 2, username: 'jane_doe', real_name: 'Jane Doe', profile_pic: 'default.jpg' },
                { id: 3, username: 'bob_smith', real_name: 'Bob Smith', profile_pic: 'default.jpg' },
                { id: 4, username: 'alice_jones', real_name: 'Alice Jones', profile_pic: 'default.jpg' }
            ],
            groups: [
                { id: 1, name: 'Family', profile_pic: 'group_default.jpg', members_count: 5 },
                { id: 2, name: 'Work Team', profile_pic: 'group_default.jpg', members_count: 8 }
            ],
            posts: [
                { id: 1, user_id: 2, description: 'Beautiful sunset at the beach', media_url: 'https://placehold.co/300x300', username: 'jane_doe', real_name: 'Jane Doe', profile_pic: 'default.jpg' },
                { id: 2, user_id: 3, description: 'Just finished reading an amazing book', media_url: 'https://placehold.co/300x300', username: 'bob_smith', real_name: 'Bob Smith', profile_pic: 'default.jpg' }
            ],
            reels: [
                { id: 1, user_id: 2, description: 'Dancing to my favorite song', video_url: 'https://placehold.co/300x600', username: 'jane_doe', real_name: 'Jane Doe', profile_pic: 'default.jpg' },
                { id: 2, user_id: 3, description: 'Cooking my favorite recipe', video_url: 'https://placehold.co/300x600', username: 'bob_smith', real_name: 'Bob Smith', profile_pic: 'default.jpg' }
            ]
        };
        
        // Get active tab
        const activeTab = document.querySelector('.search-tab.active').getAttribute('data-tab');
        
        // Show results for active tab
        const results = mockResults[activeTab === 'all' ? 'users' : activeTab] || [];
        
        results.forEach(item => {
            const resultEl = document.createElement('div');
            resultEl.className = 'search-result';
            
            if (activeTab === 'users' || activeTab === 'all') {
                resultEl.innerHTML = `
                    <img src="${item.profile_pic}" alt="${item.real_name}" class="search-result-avatar">
                    <div class="search-result-info">
                        <div class="search-result-username">${item.real_name}</div>
                        <div class="search-result-realname">@${item.username}</div>
                    </div>
                    <button class="search-result-action follow" data-id="${item.id}">Follow</button>
                `;
                
                resultEl.querySelector('.search-result-action').addEventListener('click', function() {
                    const isFollowing = this.textContent === 'Following';
                    if (isFollowing) {
                        this.textContent = 'Follow';
                        this.classList.remove('following');
                    } else {
                        this.textContent = 'Following';
                        this.classList.add('following');
                    }
                });
            } else if (activeTab === 'groups') {
                resultEl.innerHTML = `
                    <img src="${item.profile_pic}" alt="${item.name}" class="search-result-avatar" style="border-radius: 4px;">
                    <div class="search-result-info">
                        <div class="search-result-username">${item.name}</div>
                        <div class="search-result-realname">${item.members_count} members</div>
                    </div>
                    <button class="search-result-action message" data-id="${item.id}">Join</button>
                `;
            } else if (activeTab === 'posts') {
                resultEl.innerHTML = `
                    <img src="${item.media_url}" alt="Post" class="search-result-avatar" style="border-radius: 4px;">
                    <div class="search-result-info">
                        <div class="search-result-username">${item.real_name}</div>
                        <div class="search-result-realname">${item.description}</div>
                    </div>
                    <button class="search-result-action message" data-id="${item.id}">View</button>
                `;
            } else if (activeTab === 'reels') {
                resultEl.innerHTML = `
                    <img src="${item.video_url}" alt="Reel" class="search-result-avatar" style="border-radius: 4px;">
                    <div class="search-result-info">
                        <div class="search-result-username">${item.real_name}</div>
                        <div class="search-result-realname">${item.description}</div>
                    </div>
                    <button class="search-result-action message" data-id="${item.id}">View</button>
                `;
            }
            
            // Add click event to open profile
            resultEl.addEventListener('click', function(e) {
                if (!e.target.closest('.search-result-action')) {
                    openProfileModal(item);
                }
            });
            
            searchResults.appendChild(resultEl);
        });
    }
    
    // Show a search tab
    function showSearchTab(tabName) {
        // Update active tab
        document.querySelectorAll('.search-tab').forEach(tab => {
            if (tab.getAttribute('data-tab') === tabName) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
        
        // Perform search with current query
        const query = document.getElementById('searchInput').value;
        if (query.length > 0) {
            performSearch(query);
        }
    }
    
    // Open add modal
    function openAddModal() {
        addModal.classList.add('active');
    }
    
    // Close add modal
    function closeAddModal() {
        addModal.classList.remove('active');
    }
    
    // Post add content
    function postAddContent() {
        const file = document.getElementById('addFile').files[0];
        const description = document.getElementById('addDescription').value;
        const visibility = document.getElementById('addVisibility').value;
        const option = document.querySelector('.add-option.active').getAttribute('data-option');
        
        if (file || description) {
            alert(`${option.charAt(0).toUpperCase() + option.slice(1)} shared successfully!`);
            closeAddModal();
            
            // Clear form
            document.getElementById('addFile').value = '';
            document.getElementById('addDescription').value = '';
        } else {
            alert('Please add content to share');
        }
    }
    
    // Load notifications data
    function loadNotificationsData() {
        // Mock data
        const mockNotifications = [
            { id: 1, type: 'follow', content: 'Jane Doe started following you', created_at: '2023-05-15T14:30:00Z', user: { id: 2, username: 'jane_doe', real_name: 'Jane Doe', profile_pic: 'default.jpg' } },
            { id: 2, type: 'like', content: 'Bob Smith liked your post', created_at: '2023-05-15T13:45:00Z', user: { id: 3, username: 'bob_smith', real_name: 'Bob Smith', profile_pic: 'default.jpg' } },
            { id: 3, type: 'comment', content: 'Alice Jones commented on your post: "Great photo!"', created_at: '2023-05-15T12:30:00Z', user: { id: 4, username: 'alice_jones', real_name: 'Alice Jones', profile_pic: 'default.jpg' } },
            { id: 4, type: 'message', content: 'You have a new message from Charlie Brown', created_at: '2023-05-15T11:20:00Z', user: { id: 5, username: 'charlie_brown', real_name: 'Charlie Brown', profile_pic: 'default.jpg' } },
            { id: 5, type: 'system', content: 'Welcome to SociaFam! We\'re excited to have you here.', created_at: '2023-05-15T10:00:00Z', user: { id: 0, username: 'sociafam', real_name: 'SociaFam', profile_pic: 'default.jpg' } }
        ];
        
        const notificationsContainer = document.querySelector('#notificationsModal .notifications-container');
        notificationsContainer.innerHTML = '';
        
        mockNotifications.forEach(notification => {
            const notificationEl = document.createElement('div');
            notificationEl.className = 'notification';
            notificationEl.innerHTML = `
                <img src="${notification.user.profile_pic}" alt="${notification.user.real_name}" class="notification-avatar">
                <div class="notification-content">
                    <div class="notification-text">${notification.content}</div>
                    <div class="notification-time">${formatTimeAgo(notification.created_at)}</div>
                </div>
            `;
            notificationsContainer.appendChild(notificationEl);
        });
        
        // Show modal
        notificationsModal.classList.add('active');
    }
    
    // Close notifications modal
    function closeNotificationsModal() {
        notificationsModal.classList.remove('active');
    }
    
    // Load menu data
    function loadMenuData() {
        // Show modal
        menuModal.classList.add('active');
    }
    
    // Close menu modal
    function closeMenuModal() {
        menuModal.classList.remove('active');
    }
    
    // Show help & support
    function showHelpSupport() {
        alert('Help & Support');
        closeMenuModal();
    }
    
    // Show settings & privacy
    function showSettingsPrivacy() {
        alert('Settings & Privacy');
        closeMenuModal();
    }
    
    // Logout
    function logout() {
        if (confirm('Are you sure you want to log out?')) {
            currentUser = null;
            showLoginPage();
        }
    }
    
    // Load admin data
    function loadAdminData() {
        // Mock data
        const mockUsers = [
            { id: 1, username: 'john_doe', real_name: 'John Doe', status: 'active' },
            { id: 2, username: 'jane_doe', real_name: 'Jane Doe', status: 'active' },
            { id: 3, username: 'bob_smith', real_name: 'Bob Smith', status: 'banned' },
            { id: 4, username: 'alice_jones', real_name: 'Alice Jones', status: 'active' }
        ];
        
        const mockReports = [
            { type: 'post', content: 'Inappropriate content', reporter: 'john_doe', actions: 'warn' },
            { type: 'user', content: 'Harassment', reporter: 'jane_doe', actions: 'ban' },
            { type: 'comment', content: 'Hate speech', reporter: 'bob_smith', actions: 'delete' }
        ];
        
        const adminUsers = document.getElementById('adminUsers');
        adminUsers.innerHTML = '';
        
        mockUsers.forEach(user => {
            const userEl = document.createElement('tr');
            userEl.innerHTML = `
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.real_name}</td>
                <td>${user.status}</td>
                <td class="admin-actions">
                    <button class="admin-action delete" data-id="${user.id}">Delete</button>
                    <button class="admin-action ban" data-id="${user.id}">${user.status === 'banned' ? 'Unban' : 'Ban'}</button>
                    <button class="admin-action warn" data-id="${user.id}">Warn</button>
                    <button class="admin-action message" data-id="${user.id}">Message</button>
                </td>
            `;
            
            // Add event listeners
            userEl.querySelector('.admin-action.delete').addEventListener('click', function() {
                if (confirm('Are you sure you want to delete this user? This will remove all their content.')) {
                    alert('User deleted');
                    loadAdminData();
                }
            });
            
            userEl.querySelector('.admin-action.ban').addEventListener('click', function() {
                const action = user.status === 'banned' ? 'unban' : 'ban';
                if (confirm(`Are you sure you want to ${action} this user?`)) {
                    alert(`User ${action}ed`);
                    loadAdminData();
                }
            });
            
            userEl.querySelector('.admin-action.warn').addEventListener('click', function() {
                const reason = prompt('Enter warning reason:');
                if (reason) {
                    alert('Warning issued');
                    loadAdminData();
                }
            });
            
            userEl.querySelector('.admin-action.message').addEventListener('click', function() {
                alert('Send message to user');
            });
            
            adminUsers.appendChild(userEl);
        });
        
        const adminReports = document.getElementById('adminReports');
        adminReports.innerHTML = '';
        
        mockReports.forEach(report => {
            const reportEl = document.createElement('tr');
            reportEl.innerHTML = `
                <td>${report.type}</td>
                <td>${report.content}</td>
                <td>${report.reporter}</td>
                <td class="admin-actions">
                    <button class="admin-action delete">Delete</button>
                    <button class="admin-action warn">Warn</button>
                    <button class="admin-action message">Message</button>
                </td>
            `;
            
            // Add event listeners
            reportEl.querySelector('.admin-action.delete').addEventListener('click', function() {
                if (confirm('Are you sure you want to delete this content?')) {
                    alert('Content deleted');
                    loadAdminData();
                }
            });
            
            reportEl.querySelector('.admin-action.warn').addEventListener('click', function() {
                const reason = prompt('Enter warning reason:');
                if (reason) {
                    alert('Warning issued');
                    loadAdminData();
                }
            });
            
            reportEl.querySelector('.admin-action.message').addEventListener('click', function() {
                alert('Send message to user');
            });
            
            adminReports.appendChild(reportEl);
        });
        
        // Show modal
        adminModal.classList.add('active');
    }
    
    // Close admin modal
    function closeAdminModal() {
        adminModal.classList.remove('active');
    }
    
    // Format time ago
    function formatTimeAgo(dateString) {
        const now = new Date();
        const date = new Date(dateString);
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) {
            return 'Just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes}m ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours}h ago`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days}d ago`;
        }
    }
    
    // Initialize the app
    init();
});
