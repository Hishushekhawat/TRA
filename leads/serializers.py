from rest_framework import serializers
from .models import *


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leads
        fields = "__all__"