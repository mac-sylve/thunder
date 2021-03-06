from django.db import models
from django.contrib.auth.models import User


class Hobby(models.Model):

    hobby = models.CharField(max_length=20)

    def __str__(self):
        return 'Hobby: ' + self.hobby


class Member(User):

    MALE = 'Male'
    FEMALE = 'Female'
    OTHER = 'Gender' #Assign tuple keys here because it's best practice

    GENDER = ((MALE,'Male'),
              (FEMALE,'Female'),
              (OTHER,'Other'))


    #General Attributes
    firstName = models.CharField(max_length=30) #all choices null=False by default - user MUST input data
    lastName = models.CharField(max_length=30)
    dateOfBirth = models.DateField(max_length=8, default='YYYY-MM-DD')
    gender = models.CharField(max_length=7, null=True, choices=GENDER)
    profileImage = models.ImageField(upload_to='profile_images', default=None)

    #Fields with many to many relations
    hobbies = models.ManyToManyField(Hobby)
    following = models.ManyToManyField(
        to='self',
        blank=True,
        symmetrical=False,
    )

    messages = models.ManyToManyField(
        to='self',
        blank=True,
        symmetrical=False,
        through='Message',
        related_name='related_to'
    )


    def __str__(self):
        return 'Username: ' + self.username + ' Email:' + self.email + ' Password:' + self.password


class Message(models.Model):
    sender = models.ForeignKey(to=Member,
        related_name='sent',
        on_delete=models.CASCADE
    )
    recip = models.ForeignKey(
        to=Member,
        related_name='received',
        on_delete=models.CASCADE
    )
    text = models.CharField(max_length=4096)
    public = models.BooleanField(default=True)
    time = models.DateTimeField()

    def __str__(self):
        return 'Sent from: ' + self.sender.username + ' Sent to: ' + self.recip.username
