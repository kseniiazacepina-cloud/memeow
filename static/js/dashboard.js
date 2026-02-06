/*JavaScript для панели управления
 */

document.addEventListener('DOMContentLoaded', function() {
    initActivityChart();
    initQuickStats();
    initRecentActivity();
});

function initActivityChart() {
    const canvas = document.getElementById('activityChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    //пример данных за неделю
    const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
    const activityData = [5, 8, 12, 7, 15, 20, 10]; // Примерные данные
    
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: days,
            datasets: [{
                label: 'Активность',
                data: activityData,
                borderColor: '#4e73df',
                backgroundColor: 'rgba(78, 115, 223, 0.1)',
                borderWidth: 2,
                pointBackgroundColor: '#4e73df',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        drawBorder: false
                    },
                    ticks: {
                        stepSize: 5
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function initQuickStats() {
    //обновляем статистику при необходимости
    const updateButtons = document.querySelectorAll('.update-stats');
    
    updateButtons.forEach(button => {
        button.addEventListener('click', function() {
            updateDashboardStats();
        });
    });
}

function updateDashboardStats() {
    //в реальном проекте здесь был бы AJAX запрос за обновленной статистикой
    fetch('/api/stats/dashboard/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        //обновляем счетчики на странице
        if (data.memes_count !== undefined) {
            updateCounter('memes-count', data.memes_count);
        }
        if (data.likes_received !== undefined) {
            updateCounter('likes-count', data.likes_received);
        }
        if (data.favorites_count !== undefined) {
            updateCounter('favorites-count', data.favorites_count);
        }
    })
    .catch(error => {
        console.error('Ошибка при обновлении статистики:', error);
    });
}

function updateCounter(elementId, newValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const currentValue = parseInt(element.textContent) || 0;
    const diff = newValue - currentValue;
    
    if (diff !== 0) {
        //анимация изменения числа
        animateCounter(element, currentValue, newValue, 1000);
    }
}

function animateCounter(element, start, end, duration) {
    const startTime = performance.now();
    
    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const currentValue = Math.floor(start + (end - start) * progress);
        element.textContent = currentValue;
        
        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        }
    }
    
    requestAnimationFrame(updateCounter);
}

function initRecentActivity() {
    //загружаем последнюю активность
    fetch('/api/activity/recent/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.activities && data.activities.length > 0) {
            updateActivityList(data.activities);
        }
    })
    .catch(error => {
        console.error('Ошибка при загрузке активности:', error);
    });
}

function updateActivityList(activities) {
    const container = document.getElementById('recent-activity-list');
    if (!container) return;
    
    container.innerHTML = '';
    
    activities.forEach(activity => {
        const activityItem = createActivityItem(activity);
        container.appendChild(activityItem);
    });
}

function createActivityItem(activity) {
    const item = document.createElement('div');
    item.className = 'list-group-item list-group-item-action';
    
    let icon = '';
    let text = '';
    let time = activity.time || 'только что';
    
    switch(activity.type) {
        case 'meme_added':
            icon = '<i class="bi bi-plus-circle text-success"></i>';
            text = `Вы добавили мем "${activity.meme_title}"`;
            break;
        case 'meme_liked':
            icon = '<i class="bi bi-heart text-danger"></i>';
            text = `Вы лайкнули мем "${activity.meme_title}"`;
            break;
        case 'favorite_added':
            icon = '<i class="bi bi-star text-warning"></i>';
            text = `Вы добавили в избранное мем "${activity.meme_title}"`;
            break;
        case 'comment_added':
            icon = '<i class="bi bi-chat text-info"></i>';
            text = `Вы прокомментировали мем "${activity.meme_title}"`;
            break;
        default:
            icon = '<i class="bi bi-activity text-primary"></i>';
            text = activity.description || 'Новая активность';
    }
    
    item.innerHTML = `
        <div class="d-flex w-100 justify-content-between">
            <div>
                ${icon}
                <span class="ms-2">${text}</span>
            </div>
            <small class="text-muted">${time}</small>
        </div>
    `;
    
    return item;
}

//периодическое обновление статистики (каждые 5 минут)
setInterval(updateDashboardStats, 5 * 60 * 1000);