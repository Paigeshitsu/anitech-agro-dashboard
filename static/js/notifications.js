/**
 * AniTech Notifications JavaScript
 * Updated for Django system
 */

function updateNotifications() {
    // Use Django API endpoint - correct path is /notifications/api/
    fetch('/notifications/api/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Handle both list response and success response format
            const notifications = data.results || data.notifications || [];
            const unreadCount = notifications.filter(n => !n.is_read).length;
            
            const badge = document.querySelector('#notificationBtn .notification-badge');
            if (badge) {
                badge.textContent = unreadCount;
                badge.style.display = unreadCount > 0 ? 'flex' : 'none';
            }

            const panel = document.getElementById('notificationPanel');
            if (panel) {
                if (notifications.length === 0) {
                    panel.innerHTML = `<div class="notification-item-unread">${window.notificationTranslations?.noNotifications || 'No notifications'}</div>`;
                } else {
                    panel.innerHTML = notifications.map(n => {
                        let icon = 'fa-bell';
                        let colorClass = '';

                        if (n.type === 'warning') { icon = 'fa-triangle-exclamation'; colorClass = 'text-warning'; }
                        else if (n.type === 'market') { icon = 'fa-arrow-trend-up'; colorClass = 'text-info'; }
                        else if (n.type === 'offer') { icon = 'fa-hand-holding-dollar'; colorClass = 'text-success'; }
                        else if (n.type === 'urgent') { icon = 'fa-circle-exclamation'; colorClass = 'text-danger'; }
                        else if (n.type === 'info') { icon = 'fa-circle-info'; colorClass = 'text-primary'; }

                        // Format time
                        const timeAgo = getTimeAgo(n.created_at);

                        return `
                            <div class="notification-item-unread ${n.is_read ? 'read' : ''}" onclick="markAsRead(${n.id})">
                                <div style="display:flex; gap:10px;">
                                    <div style="margin-top:2px;"><i class="fa-solid ${icon} ${colorClass}"></i></div>
                                    <div>
                                        <strong>${n.title}</strong>
                                        <div>${n.message}</div>
                                        <span class="time">${timeAgo}</span>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('');

                    // Add a "Mark all as read" button if there are unread notifications
                    if (unreadCount > 0) {
                        panel.innerHTML += `
                            <div style="padding: 10px; text-align: center; border-top: 1px solid #eee;">
                                <a href="#" onclick="markAsRead(0); return false;" style="font-size: 12px; color: #4CAF50; text-decoration: none;">${window.notificationTranslations?.markAllAsRead || 'Mark all as read'}</a>
                            </div>
                        `;
                    }
                }
            }
        })
        .catch(error => {
            console.log('[Notifications] Using mock data - API not available');
            // Show placeholder when API is not available
            const panel = document.getElementById('notificationPanel');
            if (panel) {
                panel.innerHTML = `<div class="notification-item-unread">${window.notificationTranslations?.noNotifications || 'No notifications'}</div>`;
            }
        });
}

function getTimeAgo(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' minutes ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours ago';
    if (seconds < 604800) return Math.floor(seconds / 86400) + ' days ago';
    return date.toLocaleDateString();
}

function markAsRead(id) {
    if (id === 0) {
        // Mark all as read
        fetch('/notifications/api/mark-read/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ id: 0 })
        })
            .then(response => response.json())
            .then(data => {
                updateNotifications();
            })
            .catch(error => console.error('Error marking all as read:', error));
        return;
    }
    
    if (typeof id === 'string' && id.startsWith('sys_')) {
        return; // specific system notifications cannot be marked as read yet
    }
    
    fetch('/notifications/api/mark-read/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ id: id })
    })
        .then(response => response.json())
        .then(data => {
            updateNotifications();
        })
        .catch(error => console.error('Error marking notification as read:', error));
}

function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize notifications
document.addEventListener('DOMContentLoaded', () => {
    updateNotifications();
    // Refresh every 30 seconds
    setInterval(updateNotifications, 30000);

    // Toggle panel visibility
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationPanel = document.getElementById('notificationPanel');
    const notificationContainer = document.getElementById('notificationContainer');

    if (notificationBtn && notificationPanel) {
        notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isVisible = notificationPanel.style.display === 'block';
            notificationPanel.style.display = isVisible ? 'none' : 'block';
        });

        // Prevent panel from closing when clicking inside it
        if (notificationContainer) {
            notificationContainer.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }

        // Close panel when clicking anywhere else
        document.addEventListener('click', () => {
            notificationPanel.style.display = 'none';
        });
    }
});

// Toast notification function
function showToast(message = "Action completed!") {
    const toast = document.getElementById('toast');
    if (toast) {
        toast.textContent = message;
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 2500);
    }
}
