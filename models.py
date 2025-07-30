from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.
class Player(models.Model):

    GOALKEEPER='GK'
    STRIKER='ST'
    MIDFIELDER='MF'
    DEFENDER='DF'

    POSITION_CHOICES=[
        (STRIKER,'Striker'),
        (MIDFIELDER,'Midfielder'),
        (DEFENDER,'Defender'),
        (GOALKEEPER,'Goalkeeper'),

    ]

    name=models.CharField(max_length=20,null=False,blank=False)
    birth_day=models.DateField(null=False,blank=False)
    country=models.CharField(max_length=20)
    picture=models.ImageField(upload_to='player_pictures/',blank=True,null=True)
    market_value=models.PositiveIntegerField()
    salary=models.PositiveIntegerField()
    jersey_no = models.PositiveIntegerField(
    validators=[
        MinValueValidator(1),
        MaxValueValidator(99)
    ]
)
    club = models.ForeignKey('Club', related_name='players', on_delete=models.CASCADE, null=True,blank=True)
    position=models.CharField(
        max_length=2,
        choices=POSITION_CHOICES,
        blank=False,
        null=False,
    )

    age=models.PositiveIntegerField(null=False)


    def save(self, *args, **kwargs):
    # If birth_day is a string, convert to date
        if isinstance(self.birth_day, str):
            self.birth_day = datetime.strptime(self.birth_day, "%Y-%m-%d").date()

        today = datetime.today()
        self.age = today.year - self.birth_day.year
        if (today.month, today.day) < (self.birth_day.month, self.birth_day.day):
            self.age -= 1
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.name} plays as a {self.position} and is from {self.country} of age {self.age}  with market value- £{self.market_value:,}."


class Club(models.Model):
    name=models.CharField(max_length=50,null=False,blank=False)
    stadium_name=models.CharField(max_length=20)
    logo=models.ImageField(upload_to='team_logo/',blank=False,null=False)
    sponsor=models.CharField(max_length=10)
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    transfer_budget=models.PositiveIntegerField()
    salary_budget=models.PositiveIntegerField()
    kit=models.ImageField(upload_to='team_kit/',blank=True,null=True)
    
    class Meta:
        unique_together=['name','stadium_name']

    def __str__(self):
        return self.name



class Trophy(models.Model):
    name = models.CharField(max_length=20, null=False, blank=False)
    club = models.ForeignKey(Club, related_name='trophies', on_delete=models.CASCADE)
    picture = models.ImageField(upload_to='team_trophy', blank=True, null=True)


    def times_won(self):
        return self.years.count()  # Related name from TrophyYear


    def get_years_won(self):
        return [str(year.year) for year in self.years.order_by('year')]
    

    def __str__(self):
        return f"{self.name} ({self.club.name})"


class TrophyYear(models.Model):
    trophy = models.ForeignKey(Trophy, related_name='years', on_delete=models.CASCADE)
    year = models.PositiveIntegerField()

    class Meta:
        unique_together = ('trophy', 'year')  # Prevent duplicates

    def __str__(self):
        return f"{self.trophy.name} - {self.year}"
    
 


class Message(models.Model):
    sender_club = models.ForeignKey(Club, related_name='sent_messages', on_delete=models.CASCADE)
    recipient_club = models.ForeignKey(Club, related_name='received_messages', on_delete=models.CASCADE)
    player = models.ForeignKey(Player, related_name='messages', on_delete=models.CASCADE)
    market_value=models.PositiveIntegerField()
    sent_at = models.DateTimeField(auto_now_add=True)
    accepted=models.BooleanField(default=False)
    rejected=models.BooleanField(default=False)
    sender_deleted = models.BooleanField(default=False)
    recipient_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender_club.name} to {self.recipient_club.name} about {self.player.name}"


    def delete_for_club(self, club):
        if club == self.sender_club:
            self.sender_deleted = True
        elif club == self.recipient_club:
            self.recipient_deleted = True
        self.save()

        # Optional: fully delete if both have deleted
        if self.sender_deleted and self.recipient_deleted:
            self.delete()



class Schedule(models.Model):
    MATCH = 'Match'
    TRAINING = 'Training'

    SCHEDULE_CHOICES = [
        (MATCH, 'Match'),
        (TRAINING, 'Training'),
    ]
    
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=10, choices=SCHEDULE_CHOICES)
    opponent = models.ForeignKey(Club, null=True, blank=True, related_name='opponent', on_delete=models.CASCADE)
    event_date = models.DateTimeField()
    location = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.event_type} against {self.opponent.name if self.opponent else 'Training'} on {self.event_date}"


class Coach(models.Model):

    name=models.CharField(max_length=20,null=False,blank=False)
    birth_day=models.DateField(null=False,blank=False)
    country=models.CharField(max_length=20)
    type=models.CharField(max_length=30)
    picture=models.ImageField(upload_to='player_pictures/',blank=True,null=True)
    club = models.ForeignKey('Club', related_name='coach', on_delete=models.CASCADE, null=True,blank=True)
    age=models.PositiveIntegerField(null=False)
    salary=models.PositiveIntegerField()

    def save(self, *args, **kwargs):
    # If birth_day is a string, convert to date
        if isinstance(self.birth_day, str):
            self.birth_day = datetime.strptime(self.birth_day, "%Y-%m-%d").date()

        today = datetime.today()
        self.age = today.year - self.birth_day.year
        if (today.month, today.day) < (self.birth_day.month, self.birth_day.day):
            self.age -= 1
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.name} is from {self.country} of age {self.age}."