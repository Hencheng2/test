// script.js - SociaFam frontend logic

// --- Helpers ---
async function api(url, method = "GET", data = null, files = null) {
  let opts = { method, credentials: "include" };
  if (files) {
    const formData = new FormData();
    for (let key in files) formData.append(key, files[key]);
    if (data) for (let key in data) formData.append(key, data[key]);
    opts.body = formData;
  } else if (data) {
    opts.headers = { "Content-Type": "application/json" };
    opts.body = JSON.stringify(data);
  }
  const res = await fetch(url, opts);
  return res.json();
}
function showModal(id) {
  document.querySelectorAll(".modal").forEach(m => m.classList.remove("show"));
  document.getElementById(id).classList.add("show");
}
function hideModals() {
  document.querySelectorAll(".modal").forEach(m => m.classList.remove("show"));
}

// --- Auth ---
async function doLogin() {
  const u = document.getElementById("login-username").value;
  const p = document.getElementById("login-password").value;
  let res = await api("/api/login", "POST", { username: u, password: p });
  if (res.success) {
    hideModals();
    loadFeed();
  } else alert(res.error);
}
async function doRegister() {
  const u = document.getElementById("reg-username").value;
  const p = document.getElementById("reg-password").value;
  let res = await api("/api/register", "POST", { username: u, password: p });
  if (res.success) {
    alert("Registered. Unique key: " + res.unique_key);
    hideModals();
  } else alert(res.error);
}

// --- Feed ---
async function loadFeed() {
  const posts = await api("/api/posts/feed");
  const cont = document.getElementById("feed");
  cont.innerHTML = "";
  posts.forEach(p => {
    let div = document.createElement("div");
    div.className = "post";
    div.innerHTML = `
      <div class="post-header">
        <img src="${p.owner.profile_photo || 'static/default.png'}">
        <b>${p.owner.username}</b>
      </div>
      <div class="post-media">
        ${p.media_url ? `<img src="${p.media_url}">` : ""}
      </div>
      <div class="post-actions">
        <span onclick="likePost(${p.id})">❤️ ${p.likes_count}</span>
        <span>${p.comments_count} 💬</span>
      </div>
      <div class="post-description">${p.description || ""}</div>
    `;
    cont.appendChild(div);
  });
}
async function likePost(id) {
  await api(`/api/post/${id}/like`, "POST");
  loadFeed();
}

// --- Stories ---
async function loadStories() {
  const stories = await api("/api/stories/feed");
  const cont = document.getElementById("stories");
  cont.innerHTML = "";
  stories.forEach(s => {
    let d = document.createElement("div");
    d.className = "story";
    d.innerHTML = `<img src="${s.owner.profile_photo || 'static/default.png'}"><br>${s.owner.username}`;
    cont.appendChild(d);
  });
}

// --- Reels ---
async function loadReels() {
  const reels = await api("/api/reels/feed");
  const cont = document.getElementById("reels");
  cont.innerHTML = "";
  reels.forEach(r => {
    let div = document.createElement("div");
    div.className = "reel";
    div.innerHTML = `
      <video src="${r.media_url}" controls></video>
      <p>${r.description || ""}</p>
    `;
    cont.appendChild(div);
  });
}

// --- Notifications ---
async function loadNotifications() {
  const n = await api("/api/notifications");
  const cont = document.getElementById("notifications");
  cont.innerHTML = "";
  n.forEach(x => {
    let d = document.createElement("div");
    d.className = "notification";
    d.innerText = `[${x.type}] ${x.content}`;
    cont.appendChild(d);
  });
}

// --- Init ---
document.addEventListener("DOMContentLoaded", () => {
  showModal("login-modal");
});
