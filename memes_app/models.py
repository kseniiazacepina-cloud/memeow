from django.db import models

class Meme(models.Model):
    title =
    image =
    description =
    author =
    created_at = 
    views_count =
    likes_count =
    is_published =
    tags =


class Tag(models.Model):
    name =
    slug =

class Favorite(models.Model):
    pass

class MemeOfTheDay(models.Model):
    pass

