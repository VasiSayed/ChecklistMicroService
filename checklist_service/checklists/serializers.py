from rest_framework import serializers
from .models import Checklist, ChecklistItem, ChecklistItemSubmission

class ChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checklist
        fields = '__all__'

class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = '__all__'

class ChecklistItemSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItemSubmission
        fields = '__all__'
