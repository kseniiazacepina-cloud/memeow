document.addEventListener('DOMContentLoaded', function() {
    // Обработка лайков
    document.querySelectorAll('.like-btn').forEach(button => {
        button.addEventListener('click', function() {
            const memeId = this.getAttribute('data-meme-id');
            toggleLike(memeId, this);
        });
    });

    // Обработка избранного
    document.querySelectorAll('.favorite-btn').forEach(button => {
        button.addEventListener('click', function() {
            const memeId = this.getAttribute('data-meme-id');
            toggleFavorite(memeId, this);
        });
    });
});

function toggleLike(memeId, buttonElement) {
    const token = getCookie('csrftoken');
    
    fetch(`/meme/${memeId}/like/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': token,
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showToast(data.error, 'danger');
            return;
        }

        const icon = buttonElement.querySelector('i');
        const countSpan = buttonElement.querySelector('.like-count');
        
        if (data.liked) {
            icon.classList.remove('bi-heart');
            icon.classList.add('bi-heart-fill', 'text-danger');
            showToast('Лайк поставлен!', 'success');
        } else {
            icon.classList.remove('bi-heart-fill', 'text-danger');
            icon.classList.add('bi-heart');
            showToast('Лайк убран', 'info');
        }
        
        if (countSpan) {
            countSpan.textContent = data.likes_count;
        }
    })
    .catch(error => {
        console.error('Ошибка при лайке:', error);
        showToast('Ошибка при обработке лайка', 'danger');
    });
}

function toggleFavorite(memeId, buttonElement) {
    const token = getCookie('csrftoken');
    
    fetch(`/meme/${memeId}/favorite/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': token,
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showToast(data.error, 'danger');
            return;
        }

        const icon = buttonElement.querySelector('i');
        
        if (data.favorited) {
            icon.classList.remove('bi-star');
            icon.classList.add('bi-star-fill', 'text-warning');
            showToast('Добавлено в избранное!', 'success');
        } else {
            icon.classList.remove('bi-star-fill', 'text-warning');
            icon.classList.add('bi-star');
            showToast('Убрано из избранного', 'info');
        }
        
        // Если мы на странице избранного, удаляем карточку
        if (window.location.pathname.includes('/favorites/') && !data.favorited) {
            const card = buttonElement.closest('.col');
            if (card) {
                card.remove();
                updateFavoritesCount(-1);
            }
        }
    })
    .catch(error => {
        console.error('Ошибка при работе с избранным:', error);
        showToast('Ошибка при работе с избранным', 'danger');
    });
}

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
    // Создаем контейнер для тостов, если его нет
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }
    
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.innerHTML += toastHTML;
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

function updateFavoritesCount(change) {
    const countElement = document.querySelector('.text-muted strong');
    if (countElement) {
        let currentCount = parseInt(countElement.textContent) || 0;
        currentCount += change;
        countElement.textContent = currentCount;
    }
}