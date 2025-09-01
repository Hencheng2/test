// static/js/home.js

document.addEventListener('DOMContentLoaded', function() {
    const storyModal = document.getElementById('storyModal');
    const storyImage = document.getElementById('storyImage');
    const storyVideo = document.getElementById('storyVideo');
    const exitStoryBtn = document.querySelector('.exit-story-btn');
    const storyUsernameModal = document.querySelector('.story-username-modal');
    const storyCircles = document.querySelectorAll('.story-circle-wrapper');
    const navArrows = document.querySelectorAll('.nav-arrow');

    let currentStoryIndex = 0;
    const storiesData = Array.from(storyCircles).map(circle => ({
        id: circle.dataset.storyId,
        username: circle.querySelector('.story-username').textContent,
        // In a real app, you would fetch the full story content dynamically
    }));

    // Open story modal
    storyCircles.forEach((circle, index) => {
        circle.addEventListener('click', () => {
            currentStoryIndex = index;
            showStory(currentStoryIndex);
        });
    });

    // Show a specific story in the modal
    function showStory(index) {
        if (index < 0 || index >= storiesData.length) return;
        
        const story = storiesData[index];
        storyUsernameModal.textContent = story.username;
        // In a real app, you'd make an AJAX request to get the story content (image/video)
        // For this placeholder, we'll just simulate with dummy content
        storyImage.style.display = 'block';
        storyVideo.style.display = 'none';
        storyImage.src = `/static/uploads/stories/story_${story.id}.jpg`;
        storyModal.style.display = 'block';
    }

    // Story navigation
    navArrows.forEach(arrow => {
        arrow.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent modal from closing
            if (e.target.classList.contains('right-arrow')) {
                currentStoryIndex = (currentStoryIndex + 1) % storiesData.length;
            } else {
                currentStoryIndex = (currentStoryIndex - 1 + storiesData.length) % storiesData.length;
            }
            showStory(currentStoryIndex);
        });
    });

    // Close story modal by swiping down (simplified)
    let startY;
    storyModal.addEventListener('touchstart', (e) => {
        startY = e.touches[0].clientY;
    });

    storyModal.addEventListener('touchmove', (e) => {
        const endY = e.touches[0].clientY;
        if (endY > startY + 50) { // Swiped down
            storyModal.style.display = 'none';
        }
    });

    // Close story modal with the exit button
    exitStoryBtn.addEventListener('click', () => {
        storyModal.style.display = 'none';
    });

    // Post interaction buttons (like, comment, share, etc.)
    document.querySelectorAll('.like-button').forEach(button => {
        button.addEventListener('click', function() {
            const postId = this.dataset.postId;
            console.log(`User liked post ${postId}`);
            // AJAX call to backend to handle the like
        });
    });

    document.querySelectorAll('.comment-button').forEach(button => {
        button.addEventListener('click', function() {
            const postId = this.dataset.postId;
            console.log(`User wants to comment on post ${postId}`);
            // Open a modal for comments
        });
    });

    // ... (add event listeners for other buttons: share, save, follow, repost, analytics, report, hide, notifications, block)
    document.querySelectorAll('.follow-button').forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.dataset.userId;
            console.log(`User wants to follow user ${userId}`);
            // AJAX call to backend
        });
    });
});
