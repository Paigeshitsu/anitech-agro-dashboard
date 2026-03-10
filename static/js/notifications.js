function updateNotifications() {
    fetch('/agro/api/notifications.php?action=fetch')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const badge = document.querySelector('#notificationBtn .badge');
                if (badge) {
                    badge.textContent = data.unread_count;
                    badge.style.display = data.unread_count > 0 ? 'flex' : 'none';
                }

                const panel = document.getElementById('notificationPanel');
                if (panel) {
                    if (data.notifications.length === 0) {
                        panel.innerHTML = `<div class="notification-item-unread">${window.notificationTranslations?.noNotifications || 'No notifications'}</div>`;
                    } else {
                        panel.innerHTML = data.notifications.map(n => {
                            let icon = 'fa-bell';
                            let colorClass = '';

                            if (n.type === 'warning') { icon = 'fa-triangle-exclamation'; colorClass = 'text-warning'; }
                            else if (n.type === 'market') { icon = 'fa-arrow-trend-up'; colorClass = 'text-info'; }
                            else if (n.type === 'offer') { icon = 'fa-hand-holding-dollar'; colorClass = 'text-success'; }
                            else if (n.type === 'urgent') { icon = 'fa-circle-exclamation'; colorClass = 'text-danger'; }
                            else if (n.type === 'info') { icon = 'fa-circle-info'; colorClass = 'text-primary'; }

                            return `
                                <div class="notification-item-unread ${n.is_read ? 'read' : ''}" onclick="markAsRead('${n.id}')">
                                    <div style="display:flex; gap:10px;">
                                        <div style="margin-top:2px;"><i class="fa-solid ${icon} ${colorClass}"></i></div>
                                        <div>
                                            <strong>${n.title}</strong>
                                            <div>${n.message}</div>
                                            <span class="time">${n.time_ago}</span>
                                        </div>
                                    </div>
                                </div>
                            `}).join('');

                        // Add a "Mark all as read" button if there are unread notifications
                        if (data.unread_count > 0) {
                            panel.innerHTML += `
                                <div style="padding: 10px; text-align: center; border-top: 1px solid #eee;">
                                    <a href="#" onclick="markAsRead(0); return false;" style="font-size: 12px; color: #4CAF50; text-decoration: none;">${window.notificationTranslations?.markAllAsRead || 'Mark all as read'}</a>
                                </div>
                            `;
                        }
                    }
                }
            }
        })
        .catch(error => console.error('Error fetching notifications:', error));
}

function markAsRead(id) {
    if (String(id).startsWith('sys_')) {
        return; // specific system notifications cannot be marked as read yet
    }
    fetch('/agro/api/notifications.php?action=mark_as_read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: id })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateNotifications();
            }
        })
        .catch(error => console.error('Error marking notification as read:', error));
}

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
