from rest_framework import serializers
from .models import Checklist, ChecklistItem, ChecklistItemSubmission, ChecklistItemOption
from django.db.models import Q
from django.db import models


class ChecklistItemOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItemOption
        fields = '__all__'



class ChecklistItemSubmissionPendingSerializer(serializers.ModelSerializer):
    checklist_item_options = serializers.SerializerMethodField()
    maker_name = serializers.SerializerMethodField()

    class Meta:
        model = ChecklistItemSubmission
        fields = [
            "id", "status", "user", "accepted_at",
            "maker_photo", "check_photo", "check_remark",
            "checked_by_id", "checked_at", "selected_option",
            "checklist_item_options", "maker_name"
        ]
    def get_checklist_item_options(self, obj):
        options = obj.checklist_item.options.all()
        return ChecklistItemOptionSerializer(options, many=True).data

    def get_maker_name(self, obj):
        return f"User {obj.user}" if obj.user else "Unknown User"


class ChecklistItemWithPendingSubmissionsSerializer(serializers.ModelSerializer):
    submissions = serializers.SerializerMethodField()

    class Meta:
        model = ChecklistItem
        fields = [
            "id", "description", "status", "sequence",
            "photo_required", "is_done", "submissions"
        ]

    def get_submissions(self, obj):
        # Only submissions waiting for checker review
        subs = obj.submissions.filter(
            selected_option__isnull=True
        ).order_by('-accepted_at')
        return ChecklistItemSubmissionPendingSerializer(subs, many=True).data

class ChecklistWithItemsAndPendingSubmissionsSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Checklist
        fields = [
            "id", "name", "project_id", "building_id", "zone_id", "flat_id",
            "category", "status", "items"
        ]

    def get_items(self, obj):
        # Only items with status 'DONE' or 'IN_PROGRESS'
        items = obj.items.filter(status="DONE")
        return ChecklistItemWithPendingSubmissionsSerializer(items, many=True).data






class ChecklistItemSubmissionWithOptionsSerializer(serializers.ModelSerializer):
    checklist_item_options = serializers.SerializerMethodField()
    maker_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ChecklistItemSubmission
        fields = [
            "id", "status", "user", "accepted_at",
            "maker_photo", "checked_by_id", "checked_at",
            "check_photo", "check_remark", "selected_option",
            "checklist_item_options", "maker_name"
        ]
    
    def get_checklist_item_options(self, obj):
        """Get all available options for this checklist item"""
        if obj.checklist_item and hasattr(obj.checklist_item, 'options'):
            options = obj.checklist_item.options.all()
            return ChecklistItemOptionSerializer(options, many=True).data
        return []
    
    def get_maker_name(self, obj):
        """Get the name of the user who made this submission"""
        return f"User {obj.user}" if obj.user else "Unknown User"

class ChecklistItemWithSubmissionsSerializer(serializers.ModelSerializer):
    submissions = serializers.SerializerMethodField()
    
    class Meta:
        model = ChecklistItem
        fields = [
            "id", "description", "status", "sequence", 
            "photo_required", "is_done", "submissions"
        ]
    
    def get_submissions(self, obj):
        """Get submissions that need verification by the current user"""
        request = self.context.get('request')
        user_id = request.user.id if request else None
        
        if not user_id:
            return []
        
        # Get submissions assigned to this checker that haven't been verified yet
        subs = obj.submissions.filter(
            checked_by_id=user_id,
            selected_option__isnull=True
        ).order_by('-accepted_at')
        
        print(f"📝 Item {obj.id} has {subs.count()} pending submissions for checker {user_id}")
        
        return ChecklistItemSubmissionWithOptionsSerializer(subs, many=True).data

class ChecklistWithNestedItemsSerializer(serializers.ModelSerializer):
    items = ChecklistItemWithSubmissionsSerializer(many=True, read_only=True)
    total_pending_verifications = serializers.SerializerMethodField()
    
    class Meta:
        model = Checklist
        fields = [
            "id", "name", "project_id", "building_id", "zone_id", "flat_id",
            "category", "status", "items", "total_pending_verifications"
        ]
    
    def get_total_pending_verifications(self, obj):
        """Count total pending verifications in this checklist"""
        request = self.context.get('request')
        user_id = request.user.id if request else None
        
        if not user_id:
            return 0
        
        count = ChecklistItemSubmission.objects.filter(
            checklist_item__checklist=obj,
            checked_by_id=user_id,
            selected_option__isnull=True
        ).count()
        
        return count




class ChecklistItemSerializer(serializers.ModelSerializer):
    options = ChecklistItemOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ChecklistItem
        fields = '__all__'

    def validate(self, data):
        """Validate required fields"""
        if not data.get('checklist'):
            raise serializers.ValidationError("Checklist is required")
        if not data.get('title'):
            raise serializers.ValidationError("Title is required")
        return data




class ChecklistSerializer(serializers.ModelSerializer):
    items = ChecklistItemSerializer(many=True, read_only=True)  # 'items' comes from related_name on FK

    class Meta:
        model = Checklist
        fields = '__all__'   # Includes 'items'

    def validate(self, data):
        """Validate required fields"""
        if not data.get('project_id'):
            raise serializers.ValidationError("project_id is required")
        if not data.get('purpose_id'):
            raise serializers.ValidationError("purpose_id is required")
        if not data.get('category'):
            raise serializers.ValidationError("category is required")
        if not data.get('name'):
            raise serializers.ValidationError("name is required")
        return data




class ChecklistItemSubmissionFilteredSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItemSubmission
        fields = [
            "id", "user", "accepted_at", "maker_photo", "status"
        ]

class ChecklistItemWithFilteredSubmissionsSerializer(serializers.ModelSerializer):
    submissions = serializers.SerializerMethodField()

    class Meta:
        model = ChecklistItem
        fields = ["id", "description", "status", "submissions"]

    def get_submissions(self, obj):
        subs = obj.submissions.filter(
            status="COMPLETED",
            selected_option__isnull=True,
            check_photo__isnull=True,
            checked_by_id__isnull=True,
            checked_at__isnull=True
        ).filter(
            models.Q(check_remark__isnull=True) | models.Q(check_remark__exact="")
        )
        return ChecklistItemSubmissionFilteredSerializer(subs, many=True).data


class ChecklistItemSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItemSubmission
        fields = '__all__'

class ChecklistItemWithSubmissionsSerializer(serializers.ModelSerializer):
    options = ChecklistItemOptionSerializer(many=True, read_only=True)
    submissions = ChecklistItemSubmissionSerializer(many=True, read_only=True)
    class Meta:
        model = ChecklistItem
        fields = ['id', 'title', 'description', 'status', 'ignore_now', 'photo_required', 'options', 'submissions']


class ChecklistWithItemsAndSubmissionsSerializer(serializers.ModelSerializer):
    items = ChecklistItemWithSubmissionsSerializer(many=True, read_only=True)
    class Meta:
        model = Checklist
        fields = ['id', 'name', 'description', 'status', 'project_id', 'items']


class ChecklistWithItemsAndFilteredSubmissionsSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Checklist
        fields = ["id", "name", "items"]

    def get_items(self, obj):
        # Only items that are 'DONE'
        items = obj.items.filter(status="DONE")
        return ChecklistItemWithFilteredSubmissionsSerializer(items, many=True).data




    class ChecklistItemSerializer(serializers.ModelSerializer):
        options = ChecklistItemOptionSerializer(many=True, read_only=True)
        
        class Meta:
            model = ChecklistItem
            fields = '__all__'

        def validate(self, data):
            """Validate required fields"""
            if not data.get('checklist'):
                raise serializers.ValidationError("checklist is required")
            if not data.get('title'):
                raise serializers.ValidationError("description is required")
            return data


class ChecklistItemSubmissionSerializer(serializers.ModelSerializer):
    checklist_item_description = serializers.CharField(
        source="checklist_item.description", read_only=True
    )
    photo_required = serializers.BooleanField(
        source="checklist_item.photo_required", read_only=True
    )

    class Meta:
        model = ChecklistItemSubmission
        fields = '__all__'

    def validate(self, data):
        """
        Enforce: If the parent ChecklistItem has photo_required==True,
        user MUST upload a photo to complete.
        """
        instance = self.instance  # Will be non-None for updates
        checklist_item = data.get("checklist_item") or (instance and instance.checklist_item)
        if checklist_item and checklist_item.photo_required:
            # "maker_photo" in request.FILES for new uploads, or keep old one if present
            maker_photo = data.get("maker_photo") or (instance and instance.maker_photo)
            # Only enforce if status is being set to COMPLETED or DONE or IN_PROGRESS etc.
            new_status = data.get("status") or (instance and instance.status)
            if new_status in ("COMPLETED", "DONE", "IN_PROGRESS"):
                if not maker_photo:
                    raise serializers.ValidationError(
                        {"maker_photo": "Photo is required for this item (ChecklistItem.photo_required = True)."}
                    )
        return data
        
class ChecklistItemSubmissionSerializer(serializers.ModelSerializer):
    checklist_item = ChecklistItemSerializer(read_only=True)
    class Meta:
        model = ChecklistItemSubmission
        fields = '__all__'
