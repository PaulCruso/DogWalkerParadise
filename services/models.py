from django.db import models
from django.contrib.auth.models import User

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Inprogress', 'Inprogress'),
        ('Started', 'Started'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    DOG_TYPE_CHOICES = [
        ('French Bulldog', 'French Bulldog'),
        ('Labrador Retriever', 'Labrador Retriever'),
        ('Golden Retriever', 'Golden Retriever'),
        ('German Shepherd Dog', 'German Shepherd Dog'),
        ('Poodle', 'Poodle'),
        ('Other', 'Other'),
    ]

    DOG_SIZE_CHOICES = [
        ('0-15', '0-15 lbs'),
        ('16-40', '16-40 lbs'),
        ('41-100', '41-100 lbs'),
        ('101+', '101+ lbs'),
    ]

    DOG_AGE_CHOICES = [
        ('0-1', '0-1 years'),
        ('2-5', '2-5 years'),
        ('6-10', '6-10 years'),
        ('10+', '10+ years'),
    ]

    DURATION_CHOICES = [
        ('15', '15 mins'),
        ('30', '30 mins'),
        ('45', '45 mins'),
        ('60', '1 hour'),
        ('90', '1.5 hours'),
    ]

    dog_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointments_as_owner", null=True, blank=True)
    dog_walker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointments_as_walker", null=True, blank=True)    
    dog_type = models.CharField(max_length=50, choices=DOG_TYPE_CHOICES)
    other_dog_type = models.CharField(max_length=100, blank=True, null=True)
    dog_size = models.CharField(max_length=10, choices=DOG_SIZE_CHOICES)
    dog_age = models.CharField(max_length=10, choices=DOG_AGE_CHOICES)
    dog_number = models.IntegerField(default=1)
    special_requirement = models.TextField(blank=True, null=True)
    appointment_date = models.DateTimeField()
    duration = models.CharField(max_length=5, choices=DURATION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    location = models.CharField(max_length=255, blank=False, default="Unknown Location")
    rating = models.IntegerField(null=True, blank=True)  # Ratings out of 5

    def __str__(self):
        return f"Appointment on {self.appointment_date} for {self.dog_type} ({self.dog_size}) - User: {self.user.username}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    average_rating = models.FloatField(default=0)  # Average rating of the user
    rating_count = models.IntegerField(default=0)  # Count of ratings received

    def __str__(self):
        return self.user.username

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)  
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}"
    
class ChatMessage(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'{self.sender.username}: {self.content[:50]}'
    

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    appointment = models.ForeignKey('Appointment', on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message[:50]}"
