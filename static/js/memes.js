/*основной JavaScript для работы с мемами, взаимодействие с API через Fetch*/

document.addEventListener('DOMContentLoaded', function() {
    //загружаем мем дня
    loadMemeOfTheDay();
    
    //загружаем ленту мемов
    loadMemes(1);
    
    //инициализируем поиск по тегам
    initTagSearch();
    
    //кнопка для персонального мема дня
    const personalMemeBtn = document.getElementById('personal-meme-btn');
    if (personalMemeBtn) {
        personalMemeBtn.addEventListener('click', loadPersonalMemeOfTheDay);
    }
});

function loadMemeOfTheDay() {
    fetch('/api/memes/meme_of_the_day/')
        .then(response => response.json())
        .then(meme => {
            const container = document.getElementById('meme-of-the-day');
            container.innerHTML = renderMemeCard(meme, true);
        })
        .catch(error => {
            console.error('Ошибка загрузки мема дня:', error);
            document.getElementById('meme-of-the-day').innerHTML = 
                '<p class="text-danger">Не удалось загрузить мем дня</p>';
        });
}

function loadPersonalMemeOfTheDay() {
    const token = getCookie('access_token') || localStorage.getItem('access_token');
    
    if (!token) {
        alert('Необходимо авторизоваться');
        return;
    }
    
    fetch('/api/memes/personal_meme_of_the_day/', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(meme => {
        const container = document.getElementById('personal-meme');
        container.innerHTML = `
            <div class="alert alert-info">
                <h5>Ваш персональный мем дня!</h5>
                ${renderMemeCard(meme, false)}
            </div>
        `;
    })
    .catch(error => {
        console.error('Ошибка загрузки персонального мема:', error);
        document.getElementById('personal-meme').innerHTML = 
            '<p class="text-danger">Не удалось загрузить персональный мем</p>';
    });
}

function loadMemes(page = 1, tag = null) {
    let url = `/api/memes/?page=${page}`;
    if (tag) {
        url += `&tag=${tag}`;
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            renderMemes(data.results);
            renderPagination(data);
        })
        .catch(error => {
            console.error('Ошибка загрузки мемов:', error);
            document.getElementById('memes-container').innerHTML = 
                '<p class="text-danger">Не удалось загрузить мемы</p>';
        });
}

function renderMemes(memes) {
    const container = document.getElementById('memes-container');
    
    if (memes.length === 0) {
        container.innerHTML = '<p class="text-center">Мемы не найдены</p>';
        return;
    }
    
    container.innerHTML = '';
    
    memes.forEach(meme => {
        const memeElement = document.createElement('div');
        memeElement.className = 'col-md-6 col-lg-4 mb-4';
        memeElement.innerHTML = renderMemeCard(meme);
        container.appendChild(memeElement);
    });
}

function renderMemeCard(meme, isLarge = false) {
    const colClass = isLarge ? 'col-12' : 'col';
    
    return `
        <div class="card h-100 ${isLarge ? '' : 'shadow-sm'}">
            <img src="${meme.image}" class="card-img-top" alt="${meme.title}" 
                 style="max-height: ${isLarge ? '500px' : '300px'}; object-fit: cover;">
            <div class="card-body">
                <h5 class="card-title">${meme.title}</h5>
                <p class="card-text">${meme.description || ''}</p>
                <div class="mb-2">
                    ${meme.tags.map(tag => 
                        `<span class="badge bg-secondary me-1">${tag.name}</span>`
                    ).join('')}
                </div>
                <p class="text-muted small">
                    Автор: ${meme.author.username}<br>
                    ${new Date(meme.created_at).toLocaleDateString()}
                </p>
            </div>
            <div class="card-footer bg-transparent">
                <button class="btn btn-sm btn-outline-danger like-btn" data-meme-id="${meme.id}">
                    <i class="bi ${meme.is_liked ? 'bi-heart-fill text-danger' : 'bi-heart'}"></i>
                    <span class="like-count">${meme.likes_count}</span>
                </button>
                <button class="btn btn-sm btn-outline-warning favorite-btn ms-2" data-meme-id="${meme.id}">
                    <i class="bi ${meme.is_favorite ? 'bi-star-fill text-warning' : 'bi-star'}"></i>
                </button>
                <a href="/meme/${meme.id}/" class="btn btn-sm btn-outline-primary ms-2">Подробнее</a>
                <button class="btn btn-sm btn-outline-success ms-2 download-btn" data-image-url="${meme.image}">
                    <i class="bi bi-download"></i>
                </button>
            </div>
        </div>
    `;
}

//функции для работы с лайками, избранным и другие вспомогательные
function handleLike(memeId) {
    const token = getCookie('access_token') || localStorage.getItem('access_token');
    
    if (!token) {
        alert('Чтобы ставить лайки, необходимо авторизоваться');
        return;
    }
    
    fetch(`/api/memes/${memeId}/like/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        //обновляем кнопку и счетчик
        const likeBtn = document.querySelector(`.like-btn[data-meme-id="${memeId}"]`);
        const likeIcon = likeBtn.querySelector('i');
        const likeCount = likeBtn.querySelector('.like-count');
        
        likeIcon.className = data.liked ? 'bi bi-heart-fill text-danger' : 'bi bi-heart';
        likeCount.textContent = data.likes_count;
    })
    .catch(error => console.error('Ошибка при лайке:', error));
}

//вспомогательная функция для получения cookies
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

//инициализация обработчиков событий для динамически созданных элементов
document.addEventListener('click', function(e) {
    //обработка лайков
    if (e.target.closest('.like-btn')) {
        const memeId = e.target.closest('.like-btn').dataset.memeId;
        handleLike(memeId);
    }
    
    //обработка избранного
    if (e.target.closest('.favorite-btn')) {
        const memeId = e.target.closest('.favorite-btn').dataset.memeId;
        handleFavorite(memeId);
    }
    
    //скачивание изображения
    if (e.target.closest('.download-btn')) {
        const imageUrl = e.target.closest('.download-btn').dataset.imageUrl;
        downloadImage(imageUrl);
    }
});