from django.db import models

class Account(models.Model):
    account_key = models.CharField(max_length=255)
    passphrase = models.CharField(max_length=64) # SHA256

class Profile(models.Model):
    account = models.OneToOneField(Account, related_name='profile')
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    img_data = models.TextField(blank=True) # base64 encoded

class Report(models.Model):
    reported_by = models.ForeignKey(Account, related_name='reports')
    reported_on = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=128)
    longitude = models.FloatField() # x
    latitude = models.FloatField()  # y

    # overwrite save to force a subscription for the author
    # which they can remove later if they want
    def save(self, *args, **kwargs):
        new_rep = self.pk is None
        super(Report, self).save(*args, **kwargs) # save
        if new_rep:
            new_sub = ReportSubscription(account=self.reported_by, report=self)
            new_sub.save() # save the subscription


class Message(models.Model):
    about_report = models.ForeignKey(Report, related_name='messages')
    written_by = models.ForeignKey(Account, related_name='messages')
    written_on = models.DateTimeField(auto_now_add=True)
    reply_to = models.ForeignKey('Message', blank=True, null=True, related_name='replies')
    message_text = models.TextField()
    class Meta:
        ordering = ['-written_on']

class MessageImage(models.Model):
    on_message = models.ForeignKey(Message, related_name='images')
    img_data = models.TextField() # base64 encoded

class ReportSubscription(models.Model):
    account = models.ForeignKey(Account, related_name='watching')
    report = models.ForeignKey(Report, related_name='observers')

