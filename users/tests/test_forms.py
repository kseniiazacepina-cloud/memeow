from django.test import TestCase
from django.contrib.auth.models import User
from users.forms import (
    UserRegisterForm, UserUpdateForm, 
    ProfileUpdateForm, MemeSubscriptionForm
)
from users.models import Profile
from memes.tests.factories import UserFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image


class UserRegisterFormTest(TestCase):
    """Тесты для формы регистрации"""
    
    def setUp(self):
        self.existing_user = UserFactory(
            username='existinguser',
            email='existing@example.com'
        )
    
    def test_valid_form(self):
        """Тест валидной формы"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        
        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_email_format(self):
        """Тест невалидного формата email"""
        form_data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_duplicate_username(self):
        """Тест существующего имени пользователя"""
        form_data = {
            'username': 'existinguser',
            'email': 'new@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('уже существует', form.errors['username'][0])
    
    def test_duplicate_email(self):
        """Тест существующего email"""
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(
            form.errors['email'][0],
            'Этот email уже зарегистрирован'
        )
    
    def test_password_mismatch(self):
        """Тест несовпадающих паролей"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass123!',
        }
        
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_password_too_short(self):
        """Тест слишком короткого пароля"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': '123',
            'password2': '123',
        }
        
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_form_widgets(self):
        """Тест виджетов формы"""
        form = UserRegisterForm()
        
        self.assertEqual(form.fields['username'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['email'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['password1'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['password2'].widget.attrs['class'], 'form-control')


class UserUpdateFormTest(TestCase):
    """Тесты для формы обновления пользователя"""
    
    def setUp(self):
        self.user = UserFactory(
            username='testuser',
            email='test@example.com',
            first_name='Иван',
            last_name='Иванов'
        )
    
    def test_valid_form(self):
        """Тест валидной формы"""
        form_data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'first_name': 'Петр',
            'last_name': 'Петров',
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
    
    def test_duplicate_username(self):
        """Тест обновления на существующее имя пользователя"""
        UserFactory(username='otheruser')
        
        form_data = {
            'username': 'otheruser',
            'email': 'test@example.com',
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
    
    def test_duplicate_email(self):
        """Тест обновления на существующий email"""
        UserFactory(email='other@example.com')
        
        form_data = {
            'username': 'testuser',
            'email': 'other@example.com',
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_keep_own_username(self):
        """Тест сохранения своего имени пользователя"""
        form_data = {
            'username': 'testuser',
            'email': 'updated@example.com',
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())


class ProfileUpdateFormTest(TestCase):
    """Тесты для формы обновления профиля"""
    
    def setUp(self):
        self.user = UserFactory()
        self.profile = Profile.objects.get(user=self.user)
    
    def create_test_image(self):
        """Создает тестовое изображение"""
        file = BytesIO()
        image = Image.new('RGB', (100, 100), 'blue')
        image.save(file, 'jpeg')
        file.seek(0)
        return SimpleUploadedFile('avatar.jpg', file.read(), content_type='image/jpeg')
    
    def test_valid_form(self):
        """Тест валидной формы"""
        form_data = {
            'bio': 'Тестовая биография',
            'email_subscription': True,
        }
        
        form = ProfileUpdateForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())
    
    def test_form_with_image(self):
        """Тест формы с изображением"""
        image = self.create_test_image()
        
        form_data = {
            'bio': 'С новой аватаркой',
            'email_subscription': False,
        }
        form_files = {
            'avatar': image
        }
        
        form = ProfileUpdateForm(
            data=form_data,
            files=form_files,
            instance=self.profile
        )
        self.assertTrue(form.is_valid())
    
    def test_bio_max_length(self):
        """Тест максимальной длины биографии"""
        long_bio = 'a' * 501
        
        form_data = {
            'bio': long_bio,
            'email_subscription': True,
        }
        
        form = ProfileUpdateForm(data=form_data, instance=self.profile)
        self.assertFalse(form.is_valid())
        self.assertIn('bio', form.errors)
    
    def test_form_widgets(self):
        """Тест виджетов формы"""
        form = ProfileUpdateForm(instance=self.profile)
        
        self.assertEqual(form.fields['bio'].widget.attrs['rows'], 4)
        self.assertEqual(form.fields['email_subscription'].widget.attrs['class'], 'form-check-input')


class MemeSubscriptionFormTest(TestCase):
    """Тесты для формы подписки"""
    
    def test_valid_form(self):
        """Тест валидной формы"""
        form_data = {
            'frequency': 'daily',
            'channel': 'email',
        }
        
        form = MemeSubscriptionForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_frequency(self):
        """Тест невалидной частоты"""
        form_data = {
            'frequency': 'invalid',
            'channel': 'email',
        }
        
        form = MemeSubscriptionForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_all_choices_valid(self):
        """Тест всех валидных комбинаций"""
        for frequency in ['daily', 'weekly', 'none']:
            for channel in ['email', 'telegram', 'both']:
                form_data = {
                    'frequency': frequency,
                    'channel': channel,
                }
                form = MemeSubscriptionForm(data=form_data)
                self.assertTrue(form.is_valid(), f"Failed for {frequency}/{channel}")
    
    def test_form_widgets(self):
        """Тест виджетов формы"""
        form = MemeSubscriptionForm()
        
        self.assertEqual(form.fields['frequency'].widget.__class__.__name__, 'RadioSelect')
        self.assertEqual(form.fields['channel'].widget.__class__.__name__, 'RadioSelect')