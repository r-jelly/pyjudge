// Global auth helpers

function apiHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function requireAuth() {
  if (!localStorage.getItem("token")) {
    window.location.href = "/login";
    return false;
  }
  return true;
}

function escHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function nl2p(text) {
  if (!text) return "";
  return text
    .split(/\n\n+/)
    .map(p => `<p>${escHtml(p).replace(/\n/g, "<br>")}</p>`)
    .join("");
}

function difficultyBadge(d) {
  const map = {
    easy:   '<span class="badge bg-success">쉬움</span>',
    medium: '<span class="badge bg-warning text-dark">보통</span>',
    hard:   '<span class="badge bg-danger">어려움</span>',
  };
  return map[d] || `<span class="badge bg-secondary">${escHtml(d)}</span>`;
}
