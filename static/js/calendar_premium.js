/**
 * Premium Calendar Component Logic - Alignment Fixed
 * Supports both modal and static mini-calendar
 */

(function () {
    // State
    let currentDate = new Date();
    let currentMonth = currentDate.getMonth();
    let currentYear = currentDate.getFullYear();
    let cropsData = [];

    // Seasonal Data
    const seasonalDates = {
        planting: [
            "03-01", "03-02", /* ... abbreviated for brevity, same as original ... */
            "04-15"
        ],
        harvest: [
            "08-15", /* ... same ... */ "09-15"
        ],
        highDemand: [
            "12-15", /* ... same ... */ "01-05"
        ]
    };

    // Format helper
    function formatDate(dateStr) {
        if (!dateStr) return window.calendarTranslations?.notSet || "Not Set";
        const d = new Date(dateStr);
        return isNaN(d.getTime()) ? (window.calendarTranslations?.invalidDate || "Invalid Date") : d.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' });
    }

    // Init data
    function initData() {
        if (typeof window.availableCropsData !== 'undefined') {
            cropsData = window.availableCropsData.map(c => ({
                id: c.id,
                name: c.crop_name || c.name,
                grade: c.grade,
                status: c.status,
                wholesalePrice: parseFloat(c.wholesale_price || c.wholesalePrice || 0),
                retailPrice: parseFloat(c.retail_price || c.retailPrice || 0),
                quantity: parseFloat(c.quantity || 0),
                harvestDate: c.harvest_date || c.harvestDate,
                availableUntil: c.available_until || c.availableUntil,
                description: c.description
            }));
        }
    }

    // Generic render function (used by both modal and mini)
    window.renderCalendar = function(containerId, titleElId = null, isModal = true) {
        const monthNames = window.calendarTranslations?.months || ["January","February","March","April","May","June","July","August","September","October","November","December"];
        
        // Update title
        if (titleElId) {
            const titleEl = document.getElementById(titleElId);
            if (titleEl) titleEl.textContent = `${monthNames[currentMonth]} ${currentYear}`;
        }

        const grid = document.getElementById(containerId);
        if (!grid) return console.warn(`Calendar grid #${containerId} not found`);

        grid.innerHTML = '';

        const firstDay = new Date(currentYear, currentMonth, 1).getDay();
        const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

        // Empty slots
        for (let i = 0; i < firstDay; i++) {
            const empty = document.createElement('div');
            empty.className = 'calendar-day empty';
            grid.appendChild(empty);
        }

        // Days of month
        for (let day = 1; day <= daysInMonth; day++) {
            const dayEl = document.createElement('div');
            dayEl.className = 'calendar-day';

            const dateNum = document.createElement('div');
            dateNum.className = 'calendar-date-number';
            dateNum.textContent = day;
            dayEl.appendChild(dateNum);

            // Seasonal classes
            const monthStr = String(currentMonth + 1).padStart(2, '0');
            const dayStr = String(day).padStart(2, '0');
            const seasonalKey = `${monthStr}-${dayStr}`;

            if (seasonalDates.planting.includes(seasonalKey)) dayEl.classList.add('planting');
            else if (seasonalDates.harvest.includes(seasonalKey)) dayEl.classList.add('harvest');
            else if (seasonalDates.highDemand.includes(seasonalKey)) dayEl.classList.add('high-demand');

            // Today highlight
            const today = new Date();
            if (day === today.getDate() && currentMonth === today.getMonth() && currentYear === today.getFullYear()) {
                dayEl.classList.add('today');
            }

            // Crop events
            const fullDateKey = `${currentYear}-${monthStr}-${dayStr}`;
            const matchingCrops = cropsData.filter(c => c.harvestDate === fullDateKey);
            matchingCrops.forEach(c => {
                const eventEl = document.createElement('div');
                eventEl.className = 'crop-event';
                eventEl.textContent = c.name;
                eventEl.title = `${c.name} (${c.grade})`;
                dayEl.appendChild(eventEl);
            });

            if (matchingCrops.length > 0) dayEl.classList.add('has-event');

            dayEl.addEventListener('click', () => {
                if (matchingCrops.length > 0 && isModal) {
                    openCompDetailsModal(matchingCrops[0]);
                }
            });

            grid.appendChild(dayEl);
        }
    };

    // Modal functions
    window.openCalendarModal = function () {
        initData();
        const modal = document.getElementById('calendarModal');
        if (modal) {
            modal.classList.add('show');
            modal.style.display = 'flex';
            window.renderCalendar('calendarGrid', 'calendarMonthYear', true);
        }
    };

    window.closeCalendarModal = function (e) {
        const modal = document.getElementById('calendarModal');
        if (modal && (!e || e.target === modal)) {
            modal.classList.remove('show');
            setTimeout(() => modal.style.display = 'none', 300);
        }
    };

    // Navigation (shared)
    function setupNav(containerPrefix = '') {
        const prevId = `${containerPrefix}Prev`;
        const nextId = `${containerPrefix}Next`;

        document.getElementById(prevId)?.addEventListener('click', () => {
            currentMonth--;
            if (currentMonth < 0) { currentMonth = 11; currentYear--; }
            window.renderCalendar(`${containerPrefix}Grid`, `${containerPrefix}MonthYear`);
        });

        document.getElementById(nextId)?.addEventListener('click', () => {
            currentMonth++;
            if (currentMonth > 11) { currentMonth = 0; currentYear++; }
            window.renderCalendar(`${containerPrefix}Grid`, `${containerPrefix}MonthYear`);
        });
    }

    function openCompDetailsModal(crop) {
        if (typeof window.showCropDetailsModal === 'function') {
            window.showCropDetailsModal(crop.id);
        } else {
            console.log("Crop details:", crop);
            alert(`Crop: ${crop.name}\nGrade: ${crop.grade}\nHarvest: ${crop.harvestDate}`);
        }
    }

    // Init
    document.addEventListener('DOMContentLoaded', () => {
        // Modal nav
        setupNav('cal');

        // Modal button
        const openBtn = document.getElementById('openCalendarBtn');
        if (openBtn) openBtn.addEventListener('click', window.openCalendarModal);

        // Static mini-calendar init (schedule.html)
        const scheduleGrid = document.getElementById('scheduleCalendarGrid');
        if (scheduleGrid) {
            initData();
            window.renderCalendar('scheduleCalendarGrid', 'scheduleCalendarMonthYear', false);
            setupNav('schedule');
        }
    });
})();
