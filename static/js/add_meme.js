/*JavaScript для формы добавления мема*/

document.addEventListener('DOMContentLoaded', function() {
    initMemeForm();
    initTagSystem();
    initImagePreview();
});

function initMemeForm() {
    const form = document.getElementById('meme-form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        //показываем индикатор загрузки
        const submitBtn = document.getElementById('submit-btn');
        const submitText = document.getElementById('submit-text');
        const submitSpinner = document.getElementById('submit-spinner');
        
        submitBtn.disabled = true;
        submitText.classList.add('d-none');
        submitSpinner.classList.remove('d-none');
        
        //собираем данные формы
        const formData = new FormData(form);
        
        //добавляем теги из hidden поля
        const tagsInput = document.getElementById('tags-input');
        if (tagsInput) {
            formData.append('tags', tagsInput.value);
        }
        
        //отправляем форму
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
            //восстанавливаем кнопку
            submitBtn.disabled = false;
            submitText.classList.remove('d-none');
            submitSpinner.classList.add('d-none');
        });
    });
}

function initTagSystem() {
    const tagInput = document.getElementById('tag-input');
    const selectedTagsContainer = document.getElementById('selected-tags');
    const hiddenTagsInput = document.getElementById('tags-input');
    
    if (!tagInput || !selectedTagsContainer) return;
    
    let selectedTags = [];
    
    //загружаем существующие теги при редактировании
    if (hiddenTagsInput && hiddenTagsInput.value) {
        selectedTags = hiddenTagsInput.value.split(',');
        updateSelectedTags();
    }
    
    //обработка ввода тегов
    tagInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            addTag(this.value.trim());
            this.value = '';
        }
    });
    
    //клик по предложенным тегам
    document.querySelectorAll('.tag-suggestion').forEach(tag => {
        tag.addEventListener('click', function() {
            addTag(this.textContent.trim());
        });
    });
    
    function addTag(tagName) {
        if (!tagName) return;
        
        //проверяем, нет ли уже такого тега
        if (!selectedTags.includes(tagName)) {
            selectedTags.push(tagName);
            updateSelectedTags();
        }
        
        //очищаем поле ввода
        tagInput.value = '';
    }
    
    function removeTag(tagName) {
        selectedTags = selectedTags.filter(tag => tag !== tagName);
        updateSelectedTags();
    }
    
    function updateSelectedTags() {
        //обновляем отображение выбранных тегов
        selectedTagsContainer.innerHTML = '';
        
        selectedTags.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.className = 'badge bg-primary me-1 mb-1';
            tagElement.innerHTML = `
                ${tag}
                <button type="button" class="btn-close btn-close-white ms-1" 
                        style="font-size: 0.6rem;" 
                        onclick="removeTag('${tag}')"></button>
            `;
            selectedTagsContainer.appendChild(tagElement);
        });
        
        //обновляем hidden поле
        if (hiddenTagsInput) {
            hiddenTagsInput.value = selectedTags.join(',');
        }
    }
    
    //экспортируем функции для использования в inline обработчиках
    window.removeTag = removeTag;
}

function initImagePreview() {
    const imageInput = document.getElementById('image');
    const previewContainer = document.getElementById('image-preview');
    
    if (!imageInput || !previewContainer) return;
    
    imageInput.addEventListener('change', function() {
        const file = this.files[0];
        if (!file) return;
        
        //проверка типа файла
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            alert('Пожалуйста, выберите изображение в формате JPG, PNG или GIF');
            this.value = '';
            previewContainer.innerHTML = '';
            return;
        }
        
        //проверка размера
        if (file.size > 5 * 1024 * 1024) {
            alert('Изображение слишком большое. Максимальный размер: 5MB');
            this.value = '';
            previewContainer.innerHTML = '';
            return;
        }
        
        //создаем превью
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