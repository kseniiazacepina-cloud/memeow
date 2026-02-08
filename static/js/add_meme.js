/*JavaScript для формы добавления мема*/

document.addEventListener('DOMContentLoaded', function() {
    initMemeForm();
    initTagSystem();
    initImagePreview();
});

function initMemeForm() {
    const form = document.getElementById('meme-form');
    if (!form) return;
    
    // Добавляем обработчик для скрытого поля тегов
    const hiddenTagsInput = document.getElementById('tags-hidden-input');
    if (hiddenTagsInput) {
        // Восстанавливаем теги при загрузке страницы
        restoreTagsFromHiddenInput();
    }
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Обновляем скрытое поле перед отправкой
        updateHiddenTagsInput();
        
        // Показываем индикатор загрузки
        const submitBtn = document.getElementById('submit-btn');
        const submitText = document.getElementById('submit-text');
        const submitSpinner = document.getElementById('submit-spinner');
        
        submitBtn.disabled = true;
        submitText.classList.add('d-none');
        submitSpinner.classList.remove('d-none');
        
        // Собираем данные формы
        const formData = new FormData(form);
        
        // Отправляем форму
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
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
            alert('Произошла ошибка при добавлении мема. Попробуйте еще раз.');
        })
        .finally(() => {
            // Восстанавливаем кнопку
            submitBtn.disabled = false;
            submitText.classList.remove('d-none');
            submitSpinner.classList.add('d-none');
        });
    });
}

function initTagSystem() {
    const tagInput = document.getElementById('tag-input');
    const selectedTagsContainer = document.getElementById('selected-tags');
    const hiddenTagsInput = document.getElementById('tags-hidden-input');
    
    if (!tagInput || !selectedTagsContainer) return;
    
    let selectedTags = [];
    
    function addTag(tagName) {
        if (!tagName) return;
        
        // Очищаем тег от лишних пробелов
        tagName = tagName.trim();
        
        // Проверяем, нет ли уже такого тега
        if (!selectedTags.includes(tagName)) {
            selectedTags.push(tagName);
            updateSelectedTags();
        }
        
        // Очищаем поле ввода
        tagInput.value = '';
    }
    
    function removeTag(tagName) {
        selectedTags = selectedTags.filter(tag => tag !== tagName);
        updateSelectedTags();
    }
    
    function updateSelectedTags() {
        // Обновляем отображение выбранных тегов
        selectedTagsContainer.innerHTML = '';
        
        selectedTags.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.className = 'badge bg-primary me-1 mb-1';
            tagElement.innerHTML = `
                ${tag}
                <button type="button" class="btn-close btn-close-white ms-1" 
                        style="font-size: 0.6rem;" 
                        onclick="removeSelectedTag('${tag}')"></button>
            `;
            selectedTagsContainer.appendChild(tagElement);
        });
        
        // Обновляем hidden поле
        updateHiddenTagsInput();
    }
    
    function updateHiddenTagsInput() {
        if (hiddenTagsInput) {
            hiddenTagsInput.value = selectedTags.join(', ');
        }
    }
    
    function restoreTagsFromHiddenInput() {
        if (hiddenTagsInput && hiddenTagsInput.value) {
            selectedTags = hiddenTagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag);
            updateSelectedTags();
        }
    }
    
    // Обработка ввода тегов
    tagInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            addTag(this.value);
            this.value = '';
        }
    });
    
    // Клик по предложенным тегам
    document.querySelectorAll('.tag-suggestion').forEach(tag => {
        tag.addEventListener('click', function() {
            const tagName = this.getAttribute('data-tag-name') || this.textContent.trim();
            addTag(tagName);
        });
    });
    
    // Автодополнение тегов
    tagInput.addEventListener('input', function() {
        const query = this.value.trim().toLowerCase();
        if (query.length > 1) {
            // Здесь можно добавить AJAX запрос для поиска тегов
            highlightTagSuggestions(query);
        }
    });
    
    // Экспортируем функции для использования в inline обработчиках
    window.removeSelectedTag = removeTag;
    window.addSelectedTag = addTag;
}

function highlightTagSuggestions(query) {
    const suggestions = document.querySelectorAll('.tag-suggestion');
    suggestions.forEach(tag => {
        const tagName = tag.getAttribute('data-tag-name') || tag.textContent.toLowerCase();
        if (tagName.includes(query.toLowerCase())) {
            tag.classList.add('bg-info');
        } else {
            tag.classList.remove('bg-info');
        }
    });
}

function initImagePreview() {
    const imageInput = document.getElementById('id_image');
    const previewContainer = document.getElementById('image-preview');
    
    if (!imageInput || !previewContainer) return;
    
    imageInput.addEventListener('change', function() {
        const file = this.files[0];
        if (!file) return;
        
        // Проверка типа файла
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            alert('Пожалуйста, выберите изображение в формате JPG, PNG или GIF');
            this.value = '';
            previewContainer.innerHTML = '';
            return;
        }
        
        // Проверка размера (5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('Изображение слишком большое. Максимальный размер: 5MB');
            this.value = '';
            previewContainer.innerHTML = '';
            return;
        }
        
        // Создаем превью
        const reader = new FileReader();
        reader.onload = function(e) {
            previewContainer.innerHTML = `
                <div class="mt-2">
                    <img src="${e.target.result}" 
                         class="img-thumbnail" 
                         style="max-height: 200px; max-width: 200px;">
                    <p class="text-muted small mt-1">
                        ${file.name} (${(file.size / 1024).toFixed(1)} KB)
                    </p>
                </div>
            `;
        };
        reader.readAsDataURL(file);
    });
}