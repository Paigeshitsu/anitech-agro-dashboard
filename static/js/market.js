// Market page JavaScript
// Handles tabs, AJAX status updates, search, and charts

document.addEventListener('DOMContentLoaded', function() {
  initMarketPage();
});

function initMarketPage() {
  // Tab switching with URL hash persistence
  const tabs = document.querySelectorAll('.market-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', function() {
      switchTab(this.dataset.tab || this.getAttribute('onclick').match(/'([^']+)'/)[1]);
    });
  });

  // Load tab from URL hash
  const hash = window.location.hash.replace('#', '');
  if (hash && document.getElementById(hash + 'Tab')) {
    switchTab(hash);
  }

  // Live search
  initLiveSearch();

  // AJAX status updates for farmers/admins
  initStatusUpdates();

  // Initialize chart if Chart.js loaded
  initPriceChart();
}

function switchTab(tabName) {
  // Hide all tab contents
  document.querySelectorAll('.tab-content').forEach(content => {
    content.style.display = 'none';
  });

  // Remove active class from tabs
  document.querySelectorAll('.market-tab').forEach(tab => {
    tab.classList.remove('active');
  });

  // Show selected tab
  const selectedTab = document.getElementById(tabName + 'Tab');
  if (selectedTab) {
    selectedTab.classList.add('active');
    selectedTab.style.display = 'block';
    const clickedTab = document.querySelector(`[data-tab="${tabName}"]`) || event?.target;
    if (clickedTab) clickedTab.classList.add('active');
  }

  // Update URL without reload
  history.replaceState(null, null, '#' + tabName);

  // Re-init search/charts for new tab
  initLiveSearch();
}

function initLiveSearch() {
  const searchInputs = document.querySelectorAll('.market-search');
  searchInputs.forEach(input => {
    input.addEventListener('input', function() {
      const table = this.closest('.market-table-container').querySelector('.market-table');
      const rows = table.querySelectorAll('tbody tr');
      const term = this.value.toLowerCase();

      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
      });
    });
  });
}

function initStatusUpdates() {
  const statusForms = document.querySelectorAll('.status-update-form');
  statusForms.forEach(form => {
    const select = form.querySelector('select');
    select.addEventListener('change', function() {
      updateOfferStatus(form, this.value);
    });
  });
}

async function updateOfferStatus(form, status) {
  const formData = new FormData(form);
  formData.append('status', status);

  try {
    const response = await fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
      }
    });

    if (response.ok) {
      // Update badge
      const badge = form.parentElement.querySelector('.status-badge');
      badge.textContent = status;
      badge.className = `status-badge status-${status.toLowerCase()}`;
      
      // Show success toast
      showToast(`Offer status updated to ${status}!`);
    }
  } catch (error) {
    showToast('Error updating status', 'error');
  }
}

function initPriceChart() {
  // Check if Chart.js is available (CDN loaded in base.html or extra)
  if (typeof Chart === 'undefined') {
    console.log('Chart.js not loaded');
    return;
  }

  const ctx = document.getElementById('priceChart');
  if (!ctx) return;

  // Mock data - in production, fetch via AJAX
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
      datasets: [{
        label: 'Avg Price/kg',
        data: [25.5, 26.2, 24.8, 27.1, 28.0, 26.5, {{ avg_price_7d|default:26 }}],
        borderColor: '#28a745',
        backgroundColor: 'rgba(40, 167, 69, 0.1)',
        tension: 0.4,
        fill: true
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: false }
      }
    }
  });

  document.getElementById('priceChartContainer').style.display = 'block';
}

function showToast(message, type = 'success') {
  // Simple toast notification
  const toast = document.createElement('div');
  toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'success'} border-0`;
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  
  document.body.appendChild(toast);
  
  const bsToast = new bootstrap.Toast(toast);
  bsToast.show();
  
  toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

// Export functions for global access
window.switchTab = switchTab;
window.updateOfferStatus = updateOfferStatus;
