// script.js
document.addEventListener('DOMContentLoaded', () => {
    const user_id = 1; // Simulate logged-in user
    const pages = ['home', 'reels', 'friends', 'inbox', 'profile', 'search', 'add', 'notifications', 'menu', 'admin'];
    let activePage = 'home';

    function showPage(page) {
        document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
        document.getElementById(page).style.display = 'block';
        activePage = page;
    }

    // Nav handlers
    pages.forEach(page => {
        const btn = document.getElementById(`${page}-btn`);
        if (btn) btn.onclick = () => showPage(page);
    });

    // Modals
    function openModal(id) { document.getElementById(id).style.display = 'block'; }
    function closeModal(id) { document.getElementById(id).style.display = 'none'; }
    document.querySelectorAll('.close').forEach(el => {
        el.onclick = () => closeModal(el.closest('.modal').id);
    });
    window.onclick = (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    };

    // Example API calls
    fetch('/api/posts').then(r => r.json()).then(posts => {
        const container = document.getElementById('posts-container');
        posts.forEach(p => {
            const div = document.createElement('div');
            div.className = 'post';
            div.innerHTML = `
                <div class="post-header">
                    <img src="${p.profile_pic}" alt="">
                    <div><strong>${p.real_name}</strong><br><small>${new Date(p.timestamp).toLocaleString()}</small></div>
                </div>
                ${p.content_url ? `<img src="${p.content_url}" style="max-width:100%;">` : ''}
                <p>${p.description}</p>
                <div class="post-actions">
                    <button onclick="likePost(${p.id})">❤️ Like (${p.like_count})</button>
                    <button onclick="commentOn(${p.id})">💬 Comment (${p.comment_count})</button>
                </div>
            `;
            container.appendChild(div);
        });
    });

    window.likePost = (id) => {
        fetch(`/api/post/${id}/like`, { method: 'POST' }).then(() => location.reload());
    };
});
