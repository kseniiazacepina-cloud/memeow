// Функции для работы с подпиской на мемы

function connectTelegram() {
    const telegramNotConnected = document.getElementById('telegramNotConnected');
    const telegramCodeBlock = document.getElementById('telegramCodeBlock');
    
    // Запрашиваем код у сервера
    fetch('/users/generate-telegram-code/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('verificationCode').textContent = data.code;
            telegramCodeBlock.style.display = 'block';
            
            // Показываем инструкцию
            alert(`Код для привязки: ${data.code}\n\n1. Перейдите в Telegram бота: @MemeowNewsBot\n2. Отправьте ему этот код\n3. После привязки обновите страницу`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при генерации кода');
    });
}

function checkTelegramConnection() {
    // Проверяем статус привязки Telegram
    fetch('/users/check-telegram-connection/')
    .then(response => response.json())
    .then(data => {
        if (data.connected) {
            document.getElementById('telegramConnected').style.display = 'block';
            document.getElementById('telegramNotConnected').style.display = 'none';
        } else {
            document.getElementById('telegramConnected').style.display = 'none';
            document.getElementById('telegramNotConnected').style.display = 'block';
        }
    });
}

function saveSubscription() {
    const formData = new FormData();
    const channel = document.querySelector('input[name="channel"]:checked').value;
    const frequency = document.querySelector('input[name="frequency"]:checked').value;
    
    formData.append('channel', channel);
    formData.append('frequency', frequency);
    
    fetch('/users/subscription/save/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Настройки подписки сохранены!');
            if (typeof bootstrap !== 'undefined') {
                const modal = bootstrap.Modal.getInstance(document.getElementById('subscriptionModal'));
                modal.hide();
            }
        } else {
            alert('Ошибка: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при сохранении настроек');
    });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем статус Telegram при загрузке
    if (document.getElementById('telegramConnectBlock')) {
        checkTelegramConnection();
    }
});

// Вспомогательная функция для получения CSRF токена
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