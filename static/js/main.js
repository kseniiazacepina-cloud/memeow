/*основной JavaScript файл, содержит общие функции и обработчики*/

document.addEventListener('DOMContentLoaded', function() {
    //инициализация тултипов
    initTooltips();
    
    //инициализация обработчиков
    initEventHandlers();
    
    //проверка авторизации для определенных действий
    checkAuthForActions();
});

function initTooltips() {
    //инициализация Bootstrap тултипов
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initEventHandlers() {
    //обработка форм с подтверждением
    const confirmForms = document.querySelectorAll('form[data-confirm]');
    confirmForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const message = this.getAttribute('data-confirm') || 'Вы уверены?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
    
    //копирование ссылки
    const copyButtons = document.querySelectorAll('.copy-link');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const url = this.getAttribute('data-url') || window.location.href;
            copyToClipboard(url);
            showToast('Ссылка скопирована в буфер обмена!', 'success');
        });
    });
    
    //предпросмотр изображений
    const imageInputs = document.querySelectorAll('input[type="file"][accept^="image"]');
    imageInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const previewId = this.getAttribute('data-preview');
                if (previewId) {
                    const preview = document.getElementById(previewId);
                    if (preview) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            preview.innerHTML = `
                                <div class="mt-2">
                                    <img src="${e.target.result}" 
                                         class="img-thumbnail" 
                                         style="max-height: 200px;">
                                    <p class="text-muted small mt-1">${file.name}</p>
                                </div>
                            `;
                        };
                        reader.readAsDataURL(file);
                    }
                }
            }
        });
    });
}

function checkAuthForActions() {
    //проверяем, нужно ли показывать предупреждение о необходимости авторизации
    const authRequiredElements = document.querySelectorAll('[data-requires-auth]');
    authRequiredElements.forEach(element => {
        element.addEventListener('click', function(e) {
            if (!isAuthenticated()) {
                e.preventDefault();
                showLoginModal();
            }
        });
    });
}

function isAuthenticated() {
    //проверка авторизации
    return document.body.classList.contains('user-authenticated') || 
           window.userAuthenticated === true;
}

function showLoginModal() {
    //окно для входа
    const modalHTML = `
        <div class="modal fade" id="loginModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Требуется авторизация</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Для выполнения этого действия необходимо войти в систему.</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
                        <a href="/accounts/login/?next=${encodeURIComponent(window.location.pathname)}" 
                           class="btn btn-primary">Войти</a>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    //добавляем модальное окно в DOM и показываем
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHTML;
    document.body.appendChild(modalContainer);
    
    const modal = new bootstrap.Modal(document.getElementById('loginModal'));
    modal.show();
    
    //удаляем модальное окно после закрытия
    document.getElementById('loginModal').addEventListener('hidden.bs.modal', function() {
        modalContainer.remove();
    });
}

function copyToClipboard(text) {
    //копирование текста в буфер обмена
    navigator.clipboard.writeText(text).then(
        function() {
            console.log('Текст скопирован: ', text);
        },
        function(err) {
            console.error('Ошибка копирования: ', err);
            //fallback для старых браузеров
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
        }
    );
}

function showToast(message, type = 'info') {
    //показ всплывающего уведомления
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
    
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    toastContainer.innerHTML += toastHTML;
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 3000
    });
    
    toast.show();
    
    //удаляем toast после скрытия
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

function createToastContainer() {
    //создаем контейнер для toast, если его нет
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1060';
    document.body.appendChild(container);
    return container;
}

//AJAX helper функции
function ajaxRequest(url, method = 'GET', data = null, headers = {}) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open(method, url);
        
        //устанавливаем заголовки
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        xhr.setRequestHeader('Content-Type', 'application/json');
        for (const [key, value] of Object.entries(headers)) {
            xhr.setRequestHeader(key, value);
        }
        
        //добавляем CSRF токен, если он есть
        const csrfToken = getCookie('csrftoken');
        if (csrfToken) {
            xhr.setRequestHeader('X-CSRFToken', csrfToken);
        }
        
        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response);
                } catch (e) {
                    resolve(xhr.responseText);
                }
            } else {
                reject(new Error(xhr.statusText));
            }
        };
        
        xhr.onerror = function() {
            reject(new Error('Network Error'));
        };
        
        xhr.send(data ? JSON.stringify(data) : null);
    });
}

function getCookie(name) {
    //получение cookie по имени
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

//форматирование дат
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    //меньше минуты
    if (diff < 60000) {
        return 'только что';
    }
    
    //меньше часа
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} ${pluralize(minutes, 'минуту', 'минуты', 'минут')} назад`;
    }
    
    //меньше суток
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} ${pluralize(hours, 'час', 'часа', 'часов')} назад`;
    }
    
    //меньше недели
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days} ${pluralize(days, 'день', 'дня', 'дней')} назад`;
    }
    
    //форматируем как обычную дату
    return date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });
}

function pluralize(number, one, few, many) {
    //правила для русского языка
    const n = Math.abs(number) % 100;
    const n1 = n % 10;
    
    if (n > 10 && n < 20) return many;
    if (n1 > 1 && n1 < 5) return few;
    if (n1 === 1) return one;
    return many;
}

//экспортируем функции для использования в других файлах
window.Memyau = {
    ajaxRequest,
    showToast,
    formatDate,
    copyToClipboard,
    isAuthenticated
};  