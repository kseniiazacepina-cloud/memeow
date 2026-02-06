/*JavaScript для страницы избранного*/

document.addEventListener('DOMContentLoaded', function() {
    initFavoriteButtons();
    initClearFavorites();
});

function initFavoriteButtons() {
    //обработка кнопок избранного на странице
    document.querySelectorAll('.favorite-btn').forEach(button => {
        button.addEventListener('click', function() {
            const memeId = this.getAttribute('data-meme-id');
            toggleFavorite(memeId, this);
        });
    });
}

function toggleFavorite(memeId, buttonElement) {
    const token = getCookie('csrftoken');
    
    if (!token) {
        alert('Необходимо авторизоваться');
        return;
    }
    
    fetch(`/meme/${memeId}/favorite/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': token,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.favorited === false) {
            //удаляем карточку из DOM
            buttonElement.closest('.col').remove();
            
            //обновляем счетчик
            updateFavoritesCount(-1);
            
            //показываем уведомление
            showToast('Мем удален из избранного', 'warning');
        }
    })
    .catch(error => {
        console.error('Ошибка при работе с избранным:', error);
        showToast('Произошла ошибка', 'danger');
    });
}

function initClearFavorites() {
    const clearBtn = document.getElementById('confirm-clear-favorites');
    if (!clearBtn) return;
    
    clearBtn.addEventListener('click', function() {
        clearAllFavorites();
    });
    
    //валидация ввода для подтверждения
    const confirmInput = document.getElementById('confirmUsername');
    const deleteBtn = document.getElementById('confirmDeleteAccount');
    
    if (confirmInput && deleteBtn) {
        confirmInput.addEventListener('input', function() {
            deleteBtn.disabled = this.value !== this.getAttribute('placeholder');
        });
    }
}

function clearAllFavorites() {
    const token = getCookie('csrftoken');
    
    if (!token) {
        alert('Необходимо авторизоваться');
        return;
    }
    
    if (!confirm('Вы уверены, что хотите очистить все избранное? Это действие нельзя отменить.')) {
        return;
    }
    
    //показываем индикатор загрузки
    const originalText = clearBtn.innerHTML;
    clearBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Очистка...';
    clearBtn.disabled = true;
    
    //в реальном проекте здесь был бы API endpoint для массового удаления
    //пока делаем через удаление каждого по отдельности
    const favoriteButtons = document.querySelectorAll('.favorite-btn');
    let promises = [];
    
    favoriteButtons.forEach(button => {
        const memeId = button.getAttribute('data-meme-id');
        promises.push(
            fetch(`/meme/${memeId}/favorite/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': token,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
        );
    });
    
    Promise.all(promises)
        .then(() => {
            //обновляем страницу
            location.reload();
        })
        .catch(error => {
            console.error('Ошибка при очистке избранного:', error);
            showToast('Произошла ошибка при очистке', 'danger');
        })
        .finally(() => {
            clearBtn.innerHTML = originalText;
            clearBtn.disabled = false;
        });
}

function updateFavoritesCount(change) {
    const countElement = document.querySelector('.text-muted strong');
    if (countElement) {
        let currentCount = parseInt(countElement.textContent) || 0;
        currentCount += change;
        countElement.textContent = currentCount;
        
        //обновляем заголовок
        const title = document.querySelector('.display-6');
        if (title && currentCount === 0) {
            title.innerHTML = '<i class="bi bi-star-fill text-warning"></i> Избранное (пусто)';
        }
    }
}

//вспомогательные функции
function getCookie(name) {
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

function showToast(message, type = 'info') {
    const toastHTML = `
        <div class="toast align-items-center text-bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    const toastId = 'toast-' + Date.now();
    toastContainer.innerHTML += toastHTML.replace('<div class="toast', `<div id="${toastId}" class="toast`);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 3000
    });
    
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1060';
    document.body.appendChild(container);
    return container;
}