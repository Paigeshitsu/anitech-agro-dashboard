/**
 * Premium Calendar Component Logic
 * Centralized logic for Admin, Farmer, and Secretary roles.
 */

(function () {
    // State
    let currentDate = new Date();
    let currentMonth = currentDate.getMonth();
    let currentYear = currentDate.getFullYear();
    let cropsData = []; // Will be populated from the global variable `availableCropsData`

    // Seasonal Data (Shared)
    const seasonalDates = {
        planting: [
            "03-01", "03-02", "03-03", "03-04", "03-05", "03-06", "03-07", "03-08", "03-09", "03-10",
            "03-11", "03-12", "03-13", "03-14", "03-15", "03-16", "03-17", "03-18", "03-19", "03-20",
            "03-21", "03-22", "03-23", "03-24", "03-25", "03-26", "03-27", "03-28", "03-29", "03-30", "03-31",
            "04-01", "04-02", "04-03", "04-04", "04-05", "04-06", "04-07", "04-08", "04-09", "04-10",
            "04-11", "04-12", "04-13", "04-14", "04-15"
        ],
        harvest: [
            "08-15", "08-16", "08-17", "08-18", "08-19", "08-20", "08-21", "08-22", "08-23", "08-24",
            "08-25", "08-26", "08-27", "08-28", "08-29", "08-30", "08-31",
            "09-01", "09-02", "09-03", "09-04", "09-05", "09-06", "09-07", "09-08", "09-09", "09-10",
            "09-11", "09-12", "09-13", "09-14", "09-15"
        ],
        highDemand: [
            "12-15", "12-16", "12-17", "12-18", "12-19", "12-20", "12-21", "12-22", "12-23", "12-24",
            "12-25", "12-26", "12-27", "12-28", "12-29", "12-30", "12-31",
            "01-01", "01-02", "01-03", "01-04", "01-05"
        ]
    };

    // Helper: Format Date
    function formatDate(dateStr) {
        if (!dateStr) return window.calendarTranslations?.notSet || "Not Set";
        const d = new Date(dateStr);
        return isNaN(d.getTime()) ? (window.calendarTranslations?.invalidDate || "Invalid Date") : d.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' });
    }

    // Helper: Initialize Data
    function initData() {
        if (typeof window.availableCropsData !== 'undefined') {
            cropsData = window.availableCropsData.map(c => ({
                id: c.id,
                name: c.crop_name || c.name, // handle diverse naming if exists
                grade: c.grade,
                status: c.status,
                wholesalePrice: parseFloat(c.wholesale_price || c.wholesalePrice || 0),
                retailPrice: parseFloat(c.retail_price || c.retailPrice || 0),
                quantity: parseFloat(c.quantity || 0),
                harvestDate: c.harvest_date || c.harvestDate,
                availableUntil: c.available_until || c.availableUntil,
                description: c.description
            }));
        } else {
            console.warn("No crop data found for calendar.");
        }
    }

    // Render Calendar
    function renderCalendar(month, year) {
        const monthNames = window.calendarTranslations?.months || ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

        const titleEl = document.getElementById('calendarMonthYear');
        if (titleEl) titleEl.textContent = `${monthNames[month]} ${year}`;

        const grid = document.getElementById('calendarGrid');
        if (!grid) return;
        grid.innerHTML = '';

        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        // Empty slots for previous month
        for (let i = 0; i < firstDay; i++) {
            const empty = document.createElement('div');
            empty.className = 'calendar-day empty';
            grid.appendChild(empty);
        }

        // Days
        for (let day = 1; day <= daysInMonth; day++) {
            const dayEl = document.createElement('div');
            dayEl.className = 'calendar-day';

            const dateNum = document.createElement('div');
            dateNum.className = 'calendar-date-number';
            dateNum.textContent = day;
            dayEl.appendChild(dateNum);

            // Seasonality
            const monthStr = String(month + 1).padStart(2, '0');
            const dayStr = String(day).padStart(2, '0');
            const seasonalKey = `${monthStr}-${dayStr}`;
            const fullDateKey = `${year}-${monthStr}-${dayStr}`;

            if (seasonalDates.planting.includes(seasonalKey)) dayEl.classList.add('planting');
            else if (seasonalDates.harvest.includes(seasonalKey)) dayEl.classList.add('harvest');
            else if (seasonalDates.highDemand.includes(seasonalKey)) dayEl.classList.add('high-demand');

            // Crops Events
            const matchingCrops = cropsData.filter(c => c.harvestDate === fullDateKey);
            matchingCrops.forEach(c => {
                const eventEl = document.createElement('div');
                eventEl.className = 'crop-event';
                eventEl.textContent = c.name;
                eventEl.title = `${c.name} (${c.grade}) - ${window.calendarTranslations?.clickDetails || 'Click for details'}`;

                // Click Event
                eventEl.addEventListener('click', (e) => {
                    e.stopPropagation();
                    openCompDetailsModal(c); // Use our component's modal logic
                });

                dayEl.appendChild(eventEl);
            });

            grid.appendChild(dayEl);
        }
    }

    // Modal Controls
    window.openCalendarModal = function () {
        initData(); // Refresh data on open
        const modal = document.getElementById('calendarModal');
        if (modal) {
            modal.classList.add('show');
            modal.style.display = 'flex'; // Ensure flex is set for layout
            renderCalendar(currentMonth, currentYear);
        }
    };

    window.closeCalendarModal = function (e) {
        const modal = document.getElementById('calendarModal');
        // Close if clicked on overlay (self) or if forced
        if (modal && (!e || e.target === modal)) {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.style.display = 'none';
            }, 300); // 300ms matches css transition
        }
    };

    // Navigation Events
    function setupNav() {
        const prevBtn = document.getElementById('calPrevMonth');
        const nextBtn = document.getElementById('calNextMonth');

        if (prevBtn) {
            prevBtn.onclick = () => {
                currentMonth--;
                if (currentMonth < 0) { currentMonth = 11; currentYear--; }
                renderCalendar(currentMonth, currentYear);
            };
        }

        if (nextBtn) {
            nextBtn.onclick = () => {
                currentMonth++;
                if (currentMonth > 11) { currentMonth = 0; currentYear++; }
                renderCalendar(currentMonth, currentYear);
            };
        }
    }

    // Details Modal Logic (Reuses existing overlay if available, or we can inject one)
    // We will assume there is a generic overlay since we are standardizing.
    // However, to be safe, we will look for 'cropDetailsOverlay' (generic) or 'adminCalendarCropDetailsOverlay'.

    function openCompDetailsModal(crop) {
        // Try simple function first if defined by page
        if (typeof window.showCropDetailsModal === 'function') {
            window.showCropDetailsModal(crop.id);
            return;
        }

        // Fallback: Populate generic fields if they exist
        // This handles cases where showCropDetailsModal might not be exposed globally as expected
        // OR we can define a standard showCropDetailsModal in the php component script block if missing.
        console.log("Opening details for:", crop);
    }

    // Init
    document.addEventListener('DOMContentLoaded', () => {
        setupNav();

        // Bind Open Button if exists
        const openBtn = document.getElementById('openCalendarBtn');
        if (openBtn) {
            openBtn.addEventListener('click', window.openCalendarModal);
        }
    });

})();
