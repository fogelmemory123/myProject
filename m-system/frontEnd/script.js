const monthNames = [
    'ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני',
    'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר'
];

document.addEventListener('DOMContentLoaded', () => {
    const calendarContainer = document.querySelector('#calendar tbody');
    const currentMonthElement = document.getElementById('current-month');
    const prevMonthButton = document.getElementById('prev-month');
    const nextMonthButton = document.getElementById('next-month');

    let currentYear = new Date().getFullYear();
    let currentMonth = new Date().getMonth();

    // Add event listeners to the buttons for changing months
    prevMonthButton.addEventListener('click', () => {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        updateCalendar(currentYear, currentMonth);
    });

    nextMonthButton.addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        updateCalendar(currentYear, currentMonth);
    });

    // Initialize the calendar with the current month
    updateCalendar(currentYear, currentMonth);

    // Set an interval to refresh the calendar data every 30 seconds
    setInterval(() => {
        updateCalendar(currentYear, currentMonth);  // Re-fetch birthdays and events
    }, 30000);  // 30,000 milliseconds = 30 seconds
});

async function updateCalendar(year, month) {
    const birthdayData = await birthdays();  // Fetch the birthdays data
    const eventData = await events();  // Fetch the events data
    
    const calendarContainer = document.querySelector('#calendar tbody');
    const currentMonthElement = document.getElementById('current-month');
    calendarContainer.innerHTML = '';
    currentMonthElement.textContent = `${monthNames[month]} ${year}`;

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    let row = document.createElement('tr');

    // Fill the first week with empty cells if the month does not start on Sunday
    for (let i = 0; i < firstDay; i++) {
        const emptyCell = document.createElement('td');
        row.appendChild(emptyCell);
    }

    // Map birthdays by date for the current month
    const birthdayMap = {};
    birthdayData.forEach(birthday => {
        const [monthPart, dayPart] = birthday.date.split('-');
        if (parseInt(monthPart) - 1 === month) {  // Match the month
            const day = parseInt(dayPart);
            if (!birthdayMap[day]) {
                birthdayMap[day] = [];
            }
            birthdayMap[day].push(birthday.name);
        }
    });

    // Map events by date for the current month
    const eventMap = {};
    eventData.forEach(event => {
        const eventDate = new Date(event.date);
        if (eventDate.getFullYear() === year && eventDate.getMonth() === month) {
            const day = eventDate.getDate();
            if (!eventMap[day]) {
                eventMap[day] = [];
            }
            eventMap[day].push(event.event_description);
        }
    });

    // Fetch the holidays for the given month
    fetch(`https://www.hebcal.com/hebcal?v=1&cfg=json&maj=on&year=${year}&month=${month + 1}&lg=h`)
        .then(response => response.json())
        .then(data => {
            const holidays = {};
            if (data.items && data.items.length > 0) {
                data.items.forEach(item => {
                    const holidayDate = new Date(item.date).getDate();
                    holidays[holidayDate] = item.title;
                });
            }

            // Create cells for each day in the month
            for (let day = 1; day <= daysInMonth; day++) {
                if (row.children.length === 7) {
                    calendarContainer.appendChild(row);
                    row = document.createElement('tr');
                }

                const dayCell = document.createElement('td');
                dayCell.className = 'day';

                const dateDiv = document.createElement('div');
                dateDiv.className = 'date';
                dateDiv.textContent = day;

                dayCell.appendChild(dateDiv);

                // Add holidays
                if (holidays[day]) {
                    const holidayDiv = document.createElement('div');
                    holidayDiv.className = 'holiday';
                    holidayDiv.textContent = holidays[day];
                    dayCell.appendChild(holidayDiv);
                    dayCell.classList.add('holiday');
                }

                // Add birthdays
                if (birthdayMap[day]) {
                    birthdayMap[day].forEach(name => {
                        const birthdayDiv = document.createElement('div');
                        birthdayDiv.className = 'birthday';
                        birthdayDiv.textContent = `${name} 🎂`;
                        dayCell.appendChild(birthdayDiv);
                    });
                    dayCell.classList.add('birthday');
                }

                // Add events
                if (eventMap[day]) {
                    eventMap[day].forEach(description => {
                        const eventDiv = document.createElement('div');
                        eventDiv.className = 'event';
                        if(description === "לא עובדים") {
                            dayCell.style.backgroundColor = "red";
                            eventDiv.textContent = description;
                        } else {
                            eventDiv.textContent = `${description} 📅 `;
                        }
                        dayCell.appendChild(eventDiv);
                    });
                    dayCell.classList.add('event');
                }

                row.appendChild(dayCell);
            }

            // Fill the last week with empty cells if necessary
            while (row.children.length < 7) {
                const emptyCell = document.createElement('td');
                row.appendChild(emptyCell);
            }

            calendarContainer.appendChild(row);
        })
        .catch(error => console.error(`Error fetching holidays for ${year}-${month + 1}:`, error));
}

async function birthdays() {
    const token = getToken();
    if (!token) {
        console.error('No token found');
        return [];
    }

    try {
        const response = await fetch('http://127.0.0.1:5000/birthdays', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (response.ok) {
            const data = await response.json();
            return data;
        } else {
            console.error('Error fetching birthdays:', response.statusText);
            return [];
        }
    } catch (error) {
        console.error('Error fetching birthdays:', error);
        return [];
    }
}

async function events() {
    const token = getToken();
    if (!token) {
        console.error('No token found');
        return [];
    }

    try {
        const response = await fetch('http://127.0.0.1:5000/events', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (response.ok) {
            const data = await response.json();
            return data;
        } else {
            console.error('Error fetching events:', response.statusText);
            return [];
        }
    } catch (error) {
        console.error('Error fetching events:', error);
        return [];
    }
}

function getToken() {
    return localStorage.getItem('access_token');
}
