from django.conf import settings
from django.db import models
from django.urls import reverse


class Lecturer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lecturer_profile"
    )
    staff_id = models.CharField(max_length=20, unique=True, blank=True)
    department = models.CharField(max_length=150, blank=True)
    office = models.CharField(max_length=100, blank=True)
    date_joined = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.staff_id:
            self.staff_id = f"LEC-{self.pk:04d}"
            super().save(update_fields=["staff_id"])

    def get_absolute_url(self):
        return reverse("lecturer_list")
