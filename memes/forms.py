from django import forms
from .models import Meme, Tag

from django import forms
from .models import Meme, Tag

class MemeForm(forms.ModelForm):
    """Форма для добавления/редактирования мема"""
    # Поле для ввода тегов через запятую
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'котики, юмор, программирование'
        }),
        label='Теги',
        help_text='Введите теги через запятую. Существующие теги добавятся автоматически, новые будут созданы.'
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Если редактируем существующий мем, показываем текущие теги
        if self.instance and self.instance.pk:
            current_tags = self.instance.tags.all()
            self.fields['tags_input'].initial = ', '.join(tag.name for tag in current_tags)
    
    def save(self, commit=True):
        """Переопределяем сохранение для обработки тегов"""
        # Сначала сохраняем мем
        meme = super().save(commit=commit)
        
        if commit:
            # Обрабатываем теги из текстового поля
            tags_text = self.cleaned_data.get('tags_input', '')
            
            if tags_text:
                # Разделяем теги по запятой
                tag_names = [name.strip() for name in tags_text.split(',') if name.strip()]
                
                # Очищаем старые теги
                meme.tags.clear()
                
                # Добавляем новые теги
                for tag_name in tag_names:
                    # Ищем существующий тег или создаем новый
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name,
                        defaults={'slug': tag_name.lower().replace(' ', '-')}
                    )
                    meme.tags.add(tag)
        
        return meme


class TagForm(forms.ModelForm):
    """Форма для добавления/редактирования тега"""
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название тега'
            }),
        }