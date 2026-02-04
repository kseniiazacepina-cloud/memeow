from django import forms
from .models import Meme, Tag

class MemeForm(forms.ModelForm):
    """Форма для добавления/редактирования мема"""
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите теги через запятую',
            'id': 'tags-input'
        }),
        label='Теги'
    )
    
    class Meta:
        model = Meme
        fields = ['title', 'image', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название мема'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Добавьте описание (необязательно)'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'image': 'Изображение (JPG, PNG, GIF)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Для редактирования - показываем текущие теги
            self.fields['tags_input'].initial = ', '.join(
                tag.name for tag in self.instance.tags.all()
            )
    
    def clean_image(self):
        """Валидация изображения"""
        image = self.cleaned_data.get('image')
        
        if image:
            # Проверка размера (5MB)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Изображение слишком большое. Максимальный размер: 5MB')
            
            # Проверка расширения
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
            extension = image.name.split('.')[-1].lower()
            if extension not in allowed_extensions:
                raise forms.ValidationError(
                    f'Недопустимый формат файла. Допустимые форматы: {", ".join(allowed_extensions)}'
                )
        
        return image
    
    def save(self, commit=True):
        """Сохранение мема с обработкой тегов"""
        meme = super().save(commit=False)
        
        if commit:
            meme.save()
        
        # Обработка тегов
        tags_input = self.cleaned_data.get('tags_input', '')
        if tags_input:
            tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            
            # Очищаем текущие теги
            meme.tags.clear()
            
            # Добавляем новые теги
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                meme.tags.add(tag)
        
        if commit:
            self.save_m2m()
        
        return meme

class TagForm(forms.ModelForm):
    """Форма для добавления тега"""
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название тега'
            }),
        }