from django.db import models
from worx.models import Account, Profile

import json

class Session(models.Model):
    key = models.CharField(max_length=64, unique=True) # SHA256
    account = models.ForeignKey(Account, related_name='+')

    def to_json(self):
        parts = { 'session_key': self.key, 'id': self.account.id }
        try:
            parts['name'] = self.account.profile.name
            parts['location'] = self.account.profile.location
            parts['bio'] = self.account.profile.bio
            parts['img_data'] = self.account.profile.img_data
        except Profile.DoesNotExist:
        	pass # don't worry about that
        return json.dumps(parts)

