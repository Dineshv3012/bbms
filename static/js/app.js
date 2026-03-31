// ===== Dark Mode =====
function toggleDarkMode() {
    const html = document.documentElement;
    html.classList.toggle('dark');
    localStorage.setItem('darkMode', html.classList.contains('dark'));
}

// Init dark mode
if (localStorage.getItem('darkMode') === 'true' ||
    (!localStorage.getItem('darkMode') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
}

// ===== Sidebar Toggle =====
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar) {
        sidebar.classList.toggle('-translate-x-full');
        if (overlay) overlay.classList.toggle('hidden');
    }
}

// ===== Modal System =====
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        document.body.style.overflow = '';
    }
}

// Close modal on backdrop click
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('backdrop-blur-sm') && e.target.id) {
        closeModal(e.target.id);
    }
});

// Close modal on Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.fixed.z-50.flex').forEach(modal => {
            closeModal(modal.id);
        });
    }
});

// ===== User Menu =====
function toggleUserMenu() {
    const menu = document.getElementById('user-menu');
    if (menu) menu.classList.toggle('hidden');
}

// ===== Notifications =====
function toggleNotifications() {
    const dropdown = document.getElementById('notification-dropdown');
    if (dropdown) dropdown.classList.toggle('hidden');
}

// Fetch notifications
function loadNotifications() {
    fetch('/api/notifications')
        .then(r => r.json())
        .then(data => {
            const badge = document.getElementById('notification-badge');
            const list = document.getElementById('notification-list');
            if (!badge || !list) return;

            if (data.count > 0) {
                const critical = data.items.some(i => i.severity === 'critical');
                badge.textContent = data.count;
                badge.classList.remove('hidden', 'bg-blue-600', 'bg-red-600');
                badge.classList.add('flex', critical ? 'bg-red-600' : 'bg-blue-600');
                
                list.innerHTML = data.items.map(item => `
                    <a href="${item.action_url}" class="px-4 py-3 flex items-start gap-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors border-b border-gray-100 dark:border-gray-800 last:border-0">
                        <span class="mt-0.5 text-lg">${item.icon}</span>
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium ${item.severity === 'critical' ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'}">${item.message}</p>
                            <p class="text-[10px] text-gray-400 uppercase tracking-widest font-bold mt-0.5">${item.severity}</p>
                        </div>
                    </a>
                `).join('');
            } else {
                badge.classList.add('hidden');
                badge.classList.remove('flex');
                list.innerHTML = '<p class="px-4 py-8 text-sm text-gray-400 text-center">No new notifications</p>';
            }
        })
        .catch(() => {});
}

// ===== Global Search =====
let searchTimeout;
const searchInput = document.getElementById('global-search');
const searchResults = document.getElementById('search-results');

if (searchInput && searchResults) {
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const q = this.value.trim();
        if (q.length < 2) {
            searchResults.classList.add('hidden');
            return;
        }
        searchTimeout = setTimeout(() => {
            fetch(`/api/search?q=${encodeURIComponent(q)}`)
                .then(r => r.json())
                .then(results => {
                    if (results.length === 0) {
                        searchResults.innerHTML = '<p class="px-4 py-3 text-sm text-gray-400">No results found</p>';
                    } else {
                        searchResults.innerHTML = results.map(r => `
                            <a href="${r.url}" class="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                                <span class="text-xs font-bold uppercase px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">${r.type}</span>
                                <div>
                                    <p class="text-sm font-medium text-gray-900 dark:text-white">${r.name}</p>
                                    <p class="text-xs text-gray-500 dark:text-gray-400">${r.detail}</p>
                                </div>
                            </a>
                        `).join('');
                    }
                    searchResults.classList.remove('hidden');
                });
        }, 300);
    });

    // Close search on click away
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });
}

// ===== Toast Auto-dismiss =====
document.addEventListener('DOMContentLoaded', function() {
    loadNotifications();
    setInterval(loadNotifications, 30000);

    // Auto-dismiss toasts after 5s
    document.querySelectorAll('.toast-item').forEach(toast => {
        setTimeout(() => {
            toast.style.animation = 'toastOut 0.3s ease-in forwards';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    });
});

// Close menus on outside click
document.addEventListener('click', function(e) {
    const userMenu = document.getElementById('user-menu');
    const notifDropdown = document.getElementById('notification-dropdown');
    const notifBtn = document.getElementById('notification-btn');

    if (userMenu && !e.target.closest('[onclick="toggleUserMenu()"]') && !userMenu.contains(e.target)) {
        userMenu.classList.add('hidden');
    }
    if (notifDropdown && notifBtn && !notifBtn.contains(e.target) && !notifDropdown.contains(e.target)) {
        notifDropdown.classList.add('hidden');
    }
});
