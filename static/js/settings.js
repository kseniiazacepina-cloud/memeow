/*JavaScript для страницы настроек*/

document.addEventListener('DOMContentLoaded', function() {
    initAvatarPreview();
    initTabNavigation();
    initDeleteAccount();
    initFormValidation();
});

function initAvatarPreview() {
    const avatarInput = document.getElementById('id_avatar');
    const preview = document.getElementById('avatar-preview');
    
    if (!avatarInput || !preview) return;
    
    avatarInput.addEventListener('change', function() {
        const file = this.files[0];
        if (!file) return;
        
        //проверка типа файла
        if (!file.type.startsWith('image/')) {
            alert('Пожалуйста, выберите изображение');
            this.value = '';
            return;
        }
        
        //проверка размера (2MB)
        if (file.size > 2 * 1024 * 1024) {
            alert('Изображение слишком большое. Максимальный размер: 2MB');
            this.value = '';
            return;
        }
        
        //создаем превью
        const reader = new FileReader();
        reader.onload = function(e) {
            if (preview.tagName === 'IMG') {
                preview.src = e.target.result;
            } else {
                //если был div, заменяем на img
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'rounded-circle img-thumbnail';
                img.width = 150;
                img.height = 150;
                img.id = 'avatar-preview';
                preview.parentNode.replaceChild(img, preview);
            }
        };
        reader.readAsDataURL(file);
    });
}

function initTabNavigation() {
    //сохраняем активную вкладку в localStorage
    const tabLinks = document.querySelectorAll('.list-group-item[data-bs-toggle="list"]');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function() {
            localStorage.setItem('settingsActiveTab', this.getAttribute('href'));
        });
    });
    
    //восстанавливаем активную вкладку при загрузке
    const activeTab = localStorage.getItem('settingsActiveTab');
    if (activeTab) {
        const tabLink = document.querySelector(`.list-group-item[href="${activeTab}"]`);
        if (tabLink) {
            const tab = new bootstrap.Tab(tabLink);
            tab.show();
        }
    }
}

function initDeleteAccount() {
    const deleteBtn = document.getElementById('confirmDeleteAccount');
    const confirmInput = document.getElementById('confirmUsername');
    
    if (!deleteBtn || !confirmInput) return;
    
    //валидация ввода
    confirmInput.addEventListener('input', function() {
        deleteBtn.disabled = this.value !== this.getAttribute('placeholder');
    });
    
    //обработка удаления аккаунта
    deleteBtn.addEventListener('click', function() {
        if (!confirm('Вы уверены, что хотите удалить свой аккаунт? Это действие необратимо!')) {
            return;
        }
        
        //показываем индикатор загрузки
        const originalText = this.innerHTML;
        this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Удаление...';
        this.disabled = true;
        
        //отправляем запрос на удаление
        fetch('/users/delete-account/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                confirm: confirmInput.value
            })
        })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            } else if (response.ok) {
                return response.json();
            } else {
                throw new Error('Network response was not ok');
            }
        })
        .then(data => {
            if (data && data.success) {
                window.location.href = data.redirect_url;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Произошла ошибка при удалении аккаунта');
            this.innerHTML = originalText;
            this.disabled = false;
        });
    });
}

function initFormValidation() {
    //валидация формы на стороне клиента
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Сохранение...';
                submitBtn.disabled = true;
            }
        });
    });
    
    //валидация email
    const emailInput = document.getElementById('id_email');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            const email = this.value.trim();
            if (email && !validateEmail(email)) {
                this.classList.add('is-invalid');
                showFieldError(this, 'Введите корректный email адрес');
            } else {
                this.classList.remove('is-invalid');
                removeFieldError(this);
            }
        });
    }
    
    //валидация username
    const usernameInput = document.getElementById('id_username');
    if (usernameInput) {
        usernameInput.addEventListener('blur', function() {
            const username = this.value.trim();
            if (username && !validateUsername(username)) {
                this.classList.add('is-invalid');
                showFieldError(this, 'Имя пользователя может содержать только буквы, цифры и @/./+/-/_');
            } else {
                this.classList.remove('is-invalid');
                removeFieldError(this);
            }
        });
    }
}

//вспомогательные функции
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validateUsername(username) {
    const re = /^[\w.@+-]+$/;
    return re.test(username);
}

function showFieldError(field, message) {
    removeFieldError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

function removeFieldError(field) {
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
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