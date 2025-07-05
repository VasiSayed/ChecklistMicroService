from django.db import models

CHECKLIST_STATUS_CHOICES = (
    ('NOT_STARTED', 'Not Started'),
    ('IN_PROGRESS', 'In Progress'),
    ('COMPLETED', 'Completed'),
)

CHECKLISTITEM_STATUS_CHOICES = (
    ('NOT_STARTED', 'Not Started'),
    ('IN_PROGRESS','In Progress'),
    ('DONE', 'Done by Maker'),
    ('VERIFYING', 'Verifying by Checker'),
    ('COMPLETED', 'Completed'),
    ('REOPENED', 'Reopened'),
)



CHECKER_DECISION_CHOICES = (
    ('YES', 'Yes'),
    ('NO', 'No'),
    ('NA', 'Not Applicable'),
)

class Checklist(models.Model):
    project_id = models.IntegerField()
    building_id = models.IntegerField(null=True, blank=True)
    zone_id = models.IntegerField(null=True, blank=True)
    flat_id = models.IntegerField(null=True, blank=True)
    phase_id = models.IntegerField(null=True, blank=True)
    stage_id = models.IntegerField(null=True, blank=True)
    category = models.IntegerField()
    subcategory=models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=CHECKLIST_STATUS_CHOICES, default='NOT_STARTED')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        loc = self.flat_id or self.zone_id or self.building_id
        return f"Project {self.project_id} - {loc} - WorkType {self.work_type_id} - Stage {self.stage_id}"


class ChecklistItem(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    photo_required = models.BooleanField(default=False)
    sequence = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=CHECKLISTITEM_STATUS_CHOICES,
        default='NOT_STARTED'
    )
    is_done = models.BooleanField(default=False)


    def __str__(self):
        return f"Checklist {self.checklist_id} - {self.description} [{self.status}]"

class ChecklistItemSubmission(models.Model):
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name='submissions')
    # checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='item_submissions')
    status=models.CharField(max_length=25,choices=CHECKLIST_STATUS_CHOICES,default='IN_PROGRESS')
    user = models.IntegerField(null=True, blank=True) 
    accepted_at=models.DateTimeField(auto_now_add=True)
    # submitted_at = models.DateTimeField(auto_now_add=True)
    maker_photo = models.ImageField(upload_to='checklist_item_photos/', null=True, blank=True)
    checker_decision = models.CharField(
        max_length=10,
        choices=CHECKER_DECISION_CHOICES,
        null=True,
        blank=True
)
    check_photo = models.ImageField(upload_to='checklist_check_photos/', null=True, blank=True)
    check_remark = models.TextField(blank=True)
    checked_by_id = models.IntegerField(null=True, blank=True)    
    checked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Item {self.checklist_item_id} - By {self.submitted_by_id} (Checked: {self.checked_by_id})"