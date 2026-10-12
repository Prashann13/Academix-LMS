from django.db import models
from django.urls import reverse


class NewsAndEvents(models.Model):
    class PostType(models.TextChoices):
        NEWS = "News", "News"
        EVENT = "Event", "Event"

    title = models.CharField(max_length=200)
    summary = models.TextField()
    posted_as = models.CharField(max_length=10, choices=PostType.choices, default=PostType.NEWS)
    event_date = models.DateField(null=True, blank=True, help_text="Only used for events")
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_date"]
        verbose_name = "News / Event"
        verbose_name_plural = "News & Events"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("news_detail", kwargs={"pk": self.pk})
