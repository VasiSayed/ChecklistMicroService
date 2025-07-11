from django.db import models

class Checklist(models.Model):
    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("work_in_progress", "Work in Progress"),
        ("completed", "Completed"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_started")

    project_id = models.IntegerField()
    building_id = models.IntegerField(null=True, blank=True)
    zone_id = models.IntegerField(null=True, blank=True)
    flat_id = models.IntegerField(null=True, blank=True)
    purpose_id = models.IntegerField()  # Required field
    phase_id = models.IntegerField(null=True, blank=True)
    stage_id = models.IntegerField(null=True, blank=True)

    category = models.IntegerField()  # Required field
    category_level1 = models.IntegerField(null=True, blank=True)
    category_level2 = models.IntegerField(null=True, blank=True)
    category_level3 = models.IntegerField(null=True, blank=True)
    category_level4 = models.IntegerField(null=True, blank=True)
    category_level5 = models.IntegerField(null=True, blank=True)
    category_level6 = models.IntegerField(null=True, blank=True)

    remarks = models.TextField(blank=True)

    created_by_id = models.IntegerField(null=True, blank=True)  # Replaced ForeignKey with integer field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name



class ChecklistItem(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name="items")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),

        ("pending_for_maker", "Pending for Maker"),
        ("pending_for_supervisor", "Pending for Supervisor"),

        ("pending_for_inspector", "Pending for Inspector"),
        ("completed", "Completed"),
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="not_started")
    ignore_now = models.BooleanField(default=False)
    photo_required = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.checklist.name})"



class ChecklistItemOption(models.Model):
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name="options")
    name = models.CharField(max_length=255)
    choice = models.CharField(max_length=20, choices=[("P", "Positive"), ("N", "Negative")])

    def __str__(self):
        return f"{self.name} ({self.choice})"



class ChecklistItemSubmission(models.Model):
    STATUS_CHOICES = [
        ("created", "Created"),
        ("completed", "Completed"),
        
        ("pending_supervisor", "Pending Supervisor"),
        ("pending_checker", "Pending Checker"),

        ("rejected_by_supervisor", "Rejected by Supervisor"),
        ("rejected_by_checker", "Rejected by Checker"),
    ]

    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name="submissions")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="created")

    maker_id = models.IntegerField(null=True, blank=True)
    maker_at = models.DateTimeField(null=True, blank=True)

    supervisor_id = models.IntegerField(null=True, blank=True)
    reviewer_photo = models.ImageField(upload_to='reviewer_photos/', null=True, blank=True)
    supervised_at = models.DateTimeField(null=True, blank=True)

    inspector_photo = models.ImageField(upload_to='inspector_photos/', null=True, blank=True)
    checker_id = models.IntegerField(null=True, blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)

    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission for {self.checklist_item.title} - {self.status}"






# # Not started unil intializer start

# CHECKLIST_STATUS_CHOICES = (
#     ('NOT_STARTED', 'Not Started'),
#     ('IN_PROGRESS', 'In Progress'),
#     ('COMPLETED', 'Completed'),
# )  

# # Inspector wil se in_progress until he approves



# CHECKLISTITEM_STATUS_CHOICES = (
#     ('NOT_STARTED', 'Not Started'),  ## remove his if started he chechklist this will start beacuse al of it
#     ('IN_PROGRESS', 'In Progress'),  ## if main chechklist in_progress then chechker will see in_porogresss 
#     ('DONE', 'Done by Maker'),
#     ('VERIFIED', 'Verified by Checker'),
#     ('REVIEW_REJECTED', 'Rejected by Reviewer'),
#     ('COMPLETED', 'Completed'),
#     ('REOPENED', 'Reopened'),
# )

# CHECKLIST__submission_STATUS_CHOICES = (
#     ('NOT_STARTED', 'Not Started'),
#     ('IN_PROGRESS', 'In Progress'),
#     ('COMPLETED', 'Completed'),
#     ('REJECTED', 'Rejected'),
# )


# choice_ofoption = (
#     ('P', 'Positive'),
#     ('N', 'Negative'),
# )






# class Checklist(models.Model):
#     name = models.CharField(max_length=100, blank=False, default='checklist')
#     project_id = models.IntegerField()
#     building_id = models.IntegerField(null=True, blank=True)
#     zone_id = models.IntegerField(null=True, blank=True)
#     flat_id = models.IntegerField(null=True, blank=True)
#     purpose_id = models.IntegerField()  # Required field
#     phase_id = models.IntegerField(null=True, blank=True)
#     stage_id = models.IntegerField(null=True, blank=True)

#     # Category levels as integer fields
#     category = models.IntegerField()  # Required field
#     category_level1 = models.IntegerField(null=True, blank=True)
#     category_level2 = models.IntegerField(null=True, blank=True)
#     category_level3 = models.IntegerField(null=True, blank=True)
#     category_level4 = models.IntegerField(null=True, blank=True)
#     category_level5 = models.IntegerField(null=True, blank=True)
#     category_level6 = models.IntegerField(null=True, blank=True)

#     status = models.CharField(max_length=20, choices=CHECKLIST_STATUS_CHOICES, default='NOT_STARTED')
#     remarks = models.TextField(blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def _str_(self):
#         loc = self.flat_id or self.zone_id or self.building_id
#         return f" {self.id}  Project {self.project_id} - {loc} - Stage {self.stage_id}"


# class ChecklistItem(models.Model):
#     checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='items')
#     description = models.CharField(max_length=255)
#     photo_required = models.BooleanField(default=False)
#     sequence = models.PositiveIntegerField(default=1)
#     # bypass=models.BooleanField(default=False)  ##new
#     status = models.CharField(
#         max_length=20,
#         choices=CHECKLISTITEM_STATUS_CHOICES,
#         default='NOT_STARTED'
#     )
#     is_done = models.BooleanField(default=False)

#     def _str_(self):
#         return f"Checklist {self.checklist_id} - {self.description} [{self.status}]"



# class ChecklistItemOption(models.Model):
#     checklist_item = models.ForeignKey(
#         ChecklistItem, on_delete=models.CASCADE, related_name='options'
#     )
#     label = models.CharField(max_length=50)   
#     value = models.CharField(max_length=50,choices=choice_ofoption,default="P")   

#     def _str_(self):
#         return f"{self.label} ({self.value}) for Item {self.checklist_item_id}"


# class ChecklistItemSubmission(models.Model):
#     checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name='submissions')
#     status = models.CharField(max_length=25, choices=CHECKLIST__submission_STATUS_CHOICES, default='IN_PROGRESS')
#     user = models.IntegerField(null=True, blank=True)
#     accepted_at = models.DateTimeField(auto_now_add=True)
#     maker_photo = models.ImageField(upload_to='checklist_item_photos/', null=True, blank=True)
#     selected_option = models.ForeignKey( ChecklistItemOption, on_delete=models.SET_NULL, null=True, blank=True, related_name='submissions')
#     check_photo = models.ImageField(upload_to='checklist_check_photos/', null=True, blank=True)
#     check_remark = models.TextField(blank=True)
#     checked_by_id = models.IntegerField(null=True, blank=True)
#     checked_at = models.DateTimeField(null=True, blank=True)


#     inspected_by_id = models.IntegerField(null=True, blank=True)
#     inspected_at = models.DateTimeField(null=True, blank=True)
#     review_remark = models.TextField(blank=True)
#     review_photo = models.ImageField(upload_to='review_photos/', null=True, blank=True) # optional

#     def _str_(self):
#         return f"Item {self.checklist_item_id} - By {self.user} (Checked: {self.checked_by_id}, Inspected: {self.inspected_by_id})"