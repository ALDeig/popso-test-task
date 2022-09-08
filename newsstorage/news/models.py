from django.db import models


class Channel(models.Model):
    """Модель с каналами новостей"""
    name = models.TextField("Канал")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Канал"
        verbose_name_plural = "Каналы"


class Tag(models.Model):
    """Модель с тегами"""
    tag_text = models.TextField("Тег")

    def __str__(self):
        return self.tag_text

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"


class News(models.Model):
    """Модель с новостями"""
    title = models.CharField("Заголовок новости", max_length=255)
    body = models.TextField("Текст новости")
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    date = models.DateField("Дата новости")
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
