import requests
from .models import Checklist
from django.db.models import Q
from rest_framework import viewsets,permissions
from .models import Checklist, ChecklistItem, ChecklistItemSubmission, ChecklistItemOption
from .serializers import ChecklistSerializer, ChecklistItemSerializer, ChecklistItemSubmissionSerializer,ChecklistSerializer,ChecklistItemOptionSerializer,ChecklistWithItemsAndFilteredSubmissionsSerializer,ChecklistWithItemsAndFilteredSubmissionsSerializer,ChecklistWithNestedItemsSerializer,ChecklistWithItemsAndPendingSubmissionsSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


class CHecklist_View_FOr_INtializer(APIView):
    permission_classes = [permissions.IsAuthenticated]
    USER_SERVICE_URL = "http://192.168.16.214:8000/api/user-access/"

    def get(self, request):
        user_id = request.user.id
        project_id = request.query_params.get("project_id")

        if not user_id or not project_id:
            return Response({"detail": "user_id and project_id required."}, status=400)

        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = requests.get(
                self.USER_SERVICE_URL,
                params={"user_id": user_id, "project_id": project_id},
                timeout=5,
                headers=headers
            )
            if resp.status_code != 200:
                return Response({"detail": "Could not fetch user access"}, status=400)
            accesses = resp.json()
        except Exception as e:
            return Response({"detail": "User service error", "error": str(e)}, status=400)

        q = Q()
        for access in accesses:
            cat_q = Q()
            if access.get('category'):
                cat_q &= Q(category=access['category'])
                for i in range(1, 7):
                    key = f'CategoryLevel{i}'
                    if access.get(key) is not None:
                        cat_q &= Q(**{f'category_level{i}': access[key]})
                    else:
                        break

            loc_q = Q()
            if access.get('flat_id'):
                loc_q &= Q(flat_id=access['flat_id'])
            elif access.get('zone_id'):
                loc_q &= Q(zone_id=access['zone_id'])
            elif access.get('building_id'):
                loc_q &= Q(building_id=access['building_id'])

            q |= (cat_q & loc_q)

        checklists = Checklist.objects.filter(project_id=project_id, status='not_started')
        if q:  
            checklists = checklists.filter(q).distinct()
        else:
            checklists = Checklist.objects.none()

        serializer = ChecklistSerializer(checklists, many=True)
        print(serializer.data)
        return Response(serializer.data, status=200)






class IntializeChechklistView(APIView):
    def post(self, request, checklist_id):
        try:
            checklist = Checklist.objects.get(id=checklist_id, status="not_started")
        except Checklist.DoesNotExist:
            return Response(
                {"error": "Checklist not found or not in 'not_started' status."},
                status=status.HTTP_404_NOT_FOUND,
            )

        checklist.status = "in_progress"
        checklist.save()

        items_qs = checklist.items.filter(status="not_started")
        updated_count = items_qs.update(status="in_progress")

        return Response(
            {
                "checklist": ChecklistSerializer(checklist).data,
                "items_updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )



class CheckerInprogressAccessibleChecklists(APIView):
    permission_classes = [permissions.IsAuthenticated]
    USER_SERVICE_URL = "http://192.168.16.214:8000/api/user-access/"

    def get(self, request):
        user_id = request.user.id
        project_id = request.query_params.get("project_id")

        if not user_id or not project_id:
            return Response({"detail": "user_id and project_id required."}, status=400)

        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = requests.get(
                self.USER_SERVICE_URL,
                params={"user_id": user_id, "project_id": project_id},
                timeout=5,
                headers=headers
            )
            if resp.status_code != 200:
                return Response({"detail": "Could not fetch user access"}, status=400)
            accesses = resp.json()
        except Exception as e:
            return Response({"detail": "User service error", "error": str(e)}, status=400)

        q = Q()
        for access in accesses:
            cat_q = Q()
            if access.get('category'):
                cat_q &= Q(category=access['category'])
                for i in range(1, 7):
                    key = f'CategoryLevel{i}'
                    if access.get(key) is not None:
                        cat_q &= Q(**{f'category_level{i}': access[key]})
                    else:
                        break

            loc_q = Q()
            if access.get('flat_id'):
                loc_q &= Q(flat_id=access['flat_id'])
            elif access.get('zone_id'):
                loc_q &= Q(zone_id=access['zone_id'])
            elif access.get('building_id'):
                loc_q &= Q(building_id=access['building_id'])

            q |= (cat_q & loc_q)

        checklists = Checklist.objects.filter(project_id=project_id, status='in_progress')
        if q:  
            checklists = checklists.filter(q).distinct()
        else:
            checklists = Checklist.objects.none()

        serializer = ChecklistSerializer(checklists, many=True)
        return Response(serializer.data, status=200)
    





from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

class VerifyChecklistItemForCheckerNSupervisorAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        checklist_item_id = request.data.get('checklist_item_id')
        role = request.data.get('role')
        option_id = request.data.get('option_id')
        check_remark = request.data.get('check_remark', '')
        check_photo = request.FILES.get('check_photo', None)

        if not checklist_item_id or not role or not option_id:
            return Response({"detail": "checklist_item_id, role, and option_id are required."}, status=400)

        try:
            item = ChecklistItem.objects.get(id=checklist_item_id)
        except ChecklistItem.DoesNotExist:
            return Response({"detail": "ChecklistItem not found."}, status=404)

        try:
            option = ChecklistItemOption.objects.get(id=option_id)
        except ChecklistItemOption.DoesNotExist:
            return Response({"detail": "ChecklistItemOption not found."}, status=404)

        checklist = item.checklist

        # ========== CHECKER LOGIC ==========
        if role.lower() == "checker":
            # 1. Find old pending submission for this checker, or create new if first time
            submission = item.submissions.filter(
                checker_id=request.user.id,
                status="pending_checker"
            ).order_by('-created_at').first()

            if not submission:
                # First time: create submission and assign checker
                submission = ChecklistItemSubmission.objects.create(
                    checklist_item=item,
                    checker_id=request.user.id,
                    status="pending_checker"
                )
            # Update details
            submission.remarks = check_remark
            submission.checked_at = timezone.now()
            # submission.selected_option = option
            if check_photo:
                submission.inspector_photo = check_photo

            if option.choice == "P":  # YES
                submission.status = "completed"
                item.status = "completed"
                submission.save(update_fields=["remarks", "checked_at", "inspector_photo", "status"])
                item.save(update_fields=["status"])
                if not checklist.items.exclude(status="completed").exists():
                    checklist.status = "completed"
                    checklist.save(update_fields=["status"])
                return Response({
                    "detail": "Item completed.",
                    "item_id": item.id,
                    "item_status": item.status,
                    "submission_id": submission.id,
                    "submission_status": submission.status,
                    "checklist_status": checklist.status
                }, status=200)

            elif option.choice == "N":  # NO
                submission.status = "rejected_by_checker"
                submission.save(update_fields=["remarks", "checked_at", "inspector_photo", "status"])
                item.status = "pending_for_maker"
                item.save(update_fields=["status"])
                # Create new submission for the same maker (if exists) else None
                new_maker_id = submission.maker_id if submission.maker_id else None
                new_supervisor_id = submission.supervisor_id if submission.supervisor_id else None
                new_submission = ChecklistItemSubmission.objects.create(
                    checklist_item=item,
                    maker_id=new_maker_id,
                    checker_id=submission.checker_id,  # always assign to same checker for rework
                    status="created",
                    supervisor_id=new_supervisor_id
                )
                checklist.status = "work_in_progress"
                checklist.save(update_fields=["status"])
                return Response({
                    "detail": "Rejected by checker, sent back to maker.",
                    "item_id": item.id,
                    "item_status": item.status,
                    "old_submission_id": submission.id,
                    "old_submission_status": submission.status,
                    "new_submission_id": new_submission.id,
                    "checklist_status": checklist.status
                }, status=200)
            else:
                return Response({"detail": "Invalid option value for checker."}, status=400)

        # ========== SUPERVISOR LOGIC ==========
        elif role.lower() == "supervisor":
            # 1. Find old pending submission for this supervisor, or create new if first time
            submission = item.submissions.filter(
                supervisor_id=request.user.id,
                status="pending_supervisor"
            ).order_by('-created_at').first()

            if not submission:
                # Try to find a submission ready for supervisor but not yet assigned to a supervisor
                submission = item.submissions.filter(
                    checker_id__isnull=False,
                    maker_id__isnull=False,
                    status="pending_supervisor",
                    supervisor_id__isnull=True
                ).order_by('-created_at').first()

            if not submission:
                # If STILL not found, raise error
                return Response({
                    "detail": (
                        "No submission found for supervisor action. "
                        "This usually means the item hasn't been checked by checker or submitted by maker. "
                        "Please check workflow: Maker must submit, Checker must verify before Supervisor can act."
                    ),
                    "item_id": item.id,
                    "item_status": item.status
                }, status=400)

            # Update details
            submission.remarks = check_remark
            submission.supervised_at = timezone.now()
            # submission.selected_option = option
            if check_photo:
                submission.reviewer_photo = check_photo

            if option.choice == "P":  # YES
                item.status = "pending_for_inspector"
                submission.status = "pending_checker"
                item.save(update_fields=["status"])
                submission.save(update_fields=["remarks", "supervised_at", "reviewer_photo", "status"])
                return Response({
                    "detail": "Sent to inspector.",
                    "item_id": item.id,
                    "item_status": item.status,
                    "submission_id": submission.id,
                    "submission_status": submission.status
                }, status=200)

            elif option.choice == "N":  # NO
                submission.status = "rejected_by_supervisor"
                submission.save(update_fields=["remarks", "supervised_at", "reviewer_photo", "status"])
                item.status = "pending_for_maker"
                item.save(update_fields=["status"])
                new_submission = ChecklistItemSubmission.objects.create(
                    checklist_item=item,
                    maker_id=submission.maker_id,  # keep same maker for rework
                    checker_id=submission.checker_id,  # keep same checker
                    supervisor_id=submission.supervisor_id,  # keep same supervisor
                    status="created"
                )
                checklist.status = "work_in_progress"
                checklist.save(update_fields=["status"])
                return Response({
                    "detail": "Rejected by supervisor, sent back to maker.",
                    "item_id": item.id,
                    "item_status": item.status,
                    "old_submission_id": submission.id,
                    "old_submission_status": submission.status,
                    "new_submission_id": new_submission.id,
                    "checklist_status": checklist.status
                }, status=200)
            else:
                return Response({"detail": "Invalid option value for supervisor."}, status=400)
        else:
            return Response({"detail": "Invalid role. Must be 'checker' or 'supervisor'."}, status=400)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Q, Exists, OuterRef
from .models import Checklist, ChecklistItem, ChecklistItemSubmission
from .serializers import ChecklistItemSerializer  # Assume you have this!

class PendingForMakerItemsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    USER_SERVICE_URL = "http://192.168.16.214:8000/api/user-access/"

    def get(self, request):
        user_id = request.user.id
        project_id = request.query_params.get("project_id")

        if not user_id or not project_id:
            return Response({"detail": "user_id and project_id required."}, status=400)

        # ---- Fetch access as in your code ----
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            import requests
            resp = requests.get(
                self.USER_SERVICE_URL,
                params={"user_id": user_id, "project_id": project_id},
                timeout=5,
                headers=headers
            )
            if resp.status_code != 200:
                return Response({"detail": "Could not fetch user access"}, status=400)
            accesses = resp.json()
        except Exception as e:
            return Response({"detail": "User service error", "error": str(e)}, status=400)

        q = Q()
        for access in accesses:
            cat_q = Q()
            if access.get('category'):
                cat_q &= Q(category=access['category'])
                for i in range(1, 7):
                    key = f'CategoryLevel{i}'
                    if access.get(key) is not None:
                        cat_q &= Q(**{f'category_level{i}': access[key]})
                    else:
                        break
            loc_q = Q()
            if access.get('flat_id'):
                loc_q &= Q(flat_id=access['flat_id'])
            elif access.get('zone_id'):
                loc_q &= Q(zone_id=access['zone_id'])
            elif access.get('building_id'):
                loc_q &= Q(building_id=access['building_id'])
            q |= (cat_q & loc_q)

        # --- The actual filter for pending for maker ---
        items = ChecklistItem.objects.filter(
            checklist__project_id=project_id,
            checklist__in=Checklist.objects.filter(q),
            status="pending_for_maker"
        ).filter(
            Exists(
                ChecklistItemSubmission.objects.filter(
                    checklist_item=OuterRef('pk'),
                    status="created",
                    checker_id__isnull=False,
                    maker_id__isnull=True
                )
            )
        ).select_related('checklist').prefetch_related('submissions', 'options')

        serializer = ChecklistItemSerializer(items, many=True)
        # print(serializer.data)
        return Response(serializer.data, status=200)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from .models import ChecklistItem, ChecklistItemSubmission
from .serializers import ChecklistItemSerializer  # You must have a serializer for this

class MAker_DOne_view(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        checklist_item_id = request.data.get("checklist_item_id")
        print("Received checklist_item_id:", checklist_item_id)

        print('status change')
        if not checklist_item_id:
            print("Validation failed: checklist_item_id missing")
            return Response({"detail": "checklist_item_id required."}, status=400)

        # 1. Get item with status pending_for_maker
        try:
            item = ChecklistItem.objects.get(id=checklist_item_id, status="pending_for_maker")
            print(f"Found ChecklistItem: {item.id} with status {item.status}")
        except ChecklistItem.DoesNotExist:
            print("ChecklistItem not found or not pending for maker.")
            return Response({"detail": "ChecklistItem not found or not pending for maker."}, status=404)
        item.status="pending_for_supervisor"
      
        print('saved')
        # 2. Try to get submission (rework, first try)
        submission = ChecklistItemSubmission.objects.filter(
            checklist_item=item.id,
            status="created",
            checker_id__isnull=False,
            maker_id__isnull=True
        ).order_by("-created_at").first()

        if submission:
            print(f"Found submission in first query: {submission.id}")
        else:
            print("First submission query returned nothing, trying second logic...")
            # 3. If not found, try the second logic
            submission = ChecklistItemSubmission.objects.filter(
                checklist_item=item.id,
                status="created",
                maker_id=request.user.id,
                checker_id__isnull=False,
                supervisor_id__isnull=False
            ).order_by("-created_at").first()
            if submission:
                print(f"Found submission in second query: {submission.id}")
            else:
                print("Second submission query also returned nothing.")

        # 4. If any submission found, update status to pending_supervisor and save
        if submission:
            print(f"Updating submission {submission.id} status to 'pending_supervisor'")
            submission.status = "pending_supervisor"
            submission.save(update_fields=["status"])
            item.status="pending_for_supervisor"
            item.save()
            item_data = ChecklistItemSerializer(item).data
            submission_data = {
                "id": submission.id,
                "status": submission.status,
                "checker_id": submission.checker_id,
                "maker_id": submission.maker_id,
                "supervisor_id": submission.supervisor_id,
            }
            print("Returning success response with item and submission data.")
            return Response({
                "item": item_data,
                "submission": submission_data
            }, status=200)
        else:
            print("No matching submission found for rework.")
            return Response({"detail": "No matching submission found for rework."}, status=404)




class Rework_MakerChecklistItemsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    USER_SERVICE_URL = "http://192.168.16.214:8000/api/user-access/"

    def get(self, request):
        user_id = request.user.id
        project_id = request.query_params.get("project_id")

        if not user_id or not project_id:
            return Response({"detail": "user_id and project_id required."}, status=400)

        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            import requests
            resp = requests.get(
                self.USER_SERVICE_URL,
                params={"user_id": user_id, "project_id": project_id},
                timeout=5,
                headers=headers
            )
            if resp.status_code != 200:
                return Response({"detail": "Could not fetch user access"}, status=400)
            accesses = resp.json()
        except Exception as e:
            return Response({"detail": "User service error", "error": str(e)}, status=400)

        q = Q()
        for access in accesses:
            cat_q = Q()
            if access.get('category'):
                cat_q &= Q(category=access['category'])
                for i in range(1, 7):
                    key = f'CategoryLevel{i}'
                    if access.get(key) is not None:
                        cat_q &= Q(**{f'category_level{i}': access[key]})
                    else:
                        break
            loc_q = Q()
            if access.get('flat_id'):
                loc_q &= Q(flat_id=access['flat_id'])
            elif access.get('zone_id'):
                loc_q &= Q(zone_id=access['zone_id'])
            elif access.get('building_id'):
                loc_q &= Q(building_id=access['building_id'])
            q |= (cat_q & loc_q)

        items = ChecklistItem.objects.filter(
            checklist__project_id=project_id,
            checklist__in=Checklist.objects.filter(q),
            status="pending_for_maker"
        ).filter(
            Exists(
                ChecklistItemSubmission.objects.filter(
                    checklist_item=OuterRef('pk'),
                    status="created",
                    checker_id__isnull=False,
                    maker_id=user_id  
                )
            )
        ).distinct()

        from .serializers import ChecklistItemSerializer
        serializer = ChecklistItemSerializer(items, many=True)
        return Response(serializer.data, status=200)






# end here





class StartChecklistItemAPIView(APIView):
    def post(self, request, user_id, item_id):
        try:
            item = ChecklistItem.objects.get(id=item_id, status='NOT_STARTED')
        except ChecklistItem.DoesNotExist:
            return Response({'error': 'ChecklistItem not found or not in NOT_STARTED status.'}, status=404)

        item.status = 'IN_PROGRESS'
        item.save()

        submission = ChecklistItemSubmission.objects.create(
            checklist_item=item,
            status='IN_PROGRESS',
            user=user_id
        )

        return Response({
            'item': ChecklistItemSerializer(item).data,
            'submission': ChecklistItemSubmissionSerializer(submission).data
        }, status=201)




class ChecklistItemOptionViewSet(viewsets.ModelViewSet):
    queryset = ChecklistItemOption.objects.all()
    serializer_class = ChecklistItemOptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        print("Creating ChecklistItemOption with data:", request.data)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("ChecklistItemOption Validation Errors:", serializer.errors)
            return Response(serializer.errors, status=400)
        self.perform_create(serializer)
        print("ChecklistItemOption created successfully:", serializer.data)
        return Response(serializer.data, status=201)


class ChecklistViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Checklist.objects.all()
    serializer_class = ChecklistSerializer

    def create(self, request, *args, **kwargs):
        # print("Creating Checklist with data:", request.data)
        
        # Validate required fields before serializer
        if not request.data.get('project_id'):
            return Response({"project_id": ["This field is required."]}, status=400)
        if not request.data.get('purpose_id'):
            return Response({"purpose_id": ["This field is required."]}, status=400)
        if not request.data.get('category'):
            return Response({"category": ["This field is required."]}, status=400)
        if not request.data.get('name'):
            return Response({"name": ["This field is required."]}, status=400)
            
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Checklist Validation Errors:", serializer.errors)
            return Response(serializer.errors, status=400)
        
        self.perform_create(serializer)
        # print("Checklist created successfully:", serializer.data)
        return Response(serializer.data, status=201)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get("project")
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset


class ChecklistItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ChecklistItem.objects.all()
    serializer_class = ChecklistItemSerializer

    def create(self, request, *args, **kwargs):
        print("Creating ChecklistItem with data:", request.data)
        
        # Validate required fields
        if not request.data.get('checklist'):
            return Response({"checklist": ["This field is required."]}, status=400)

            
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("ChecklistItem Validation Errors:", serializer.errors)
            return Response(serializer.errors, status=400)
        
        self.perform_create(serializer)
        print("ChecklistItem created successfully:", serializer.data)
        return Response(serializer.data, status=201)
    
    @action(detail=False, methods=['get'])
    def by_checklist(self, request):
        checklist_id = request.query_params.get('checklist_id')
        if not checklist_id:
            return Response({"error": "checklist_id is required"}, status=400)
        items = self.get_queryset().filter(checklist_id=checklist_id)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


class ChecklistItemSubmissionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ChecklistItemSubmission.objects.all()
    serializer_class = ChecklistItemSubmissionSerializer

    def create(self, request, *args, **kwargs):
        # print("Creating ChecklistItemSubmission with data:", request.data)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("ChecklistItemSubmission Validation Errors:", serializer.errors)
            return Response(serializer.errors, status=400)
        self.perform_create(serializer)
        # print("ChecklistItemSubmission created successfully:", serializer.data)
        return Response(serializer.data, status=201)

    @action(detail=False, methods=['get'])
    def All_Checklist_Record(self, request):
        check_listItem_id = request.query_params.get('check_listItem_id')
        if not check_listItem_id:
            return Response({"error": "checklistItem_id is required"}, status=400)
        items = self.get_queryset().filter(checklist_item_id=check_listItem_id)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


class StartChecklistItemAPIView(APIView):
    def post(self, request, user_id, item_id):
        try:
            item = ChecklistItem.objects.get(id=item_id, status='NOT_STARTED')
        except ChecklistItem.DoesNotExist:
            return Response({'error': 'ChecklistItem not found or not in NOT_STARTED status.'}, status=404)

        item.status = 'IN_PROGRESS'
        item.save()

        submission = ChecklistItemSubmission.objects.create(
            checklist_item=item,
            status='IN_PROGRESS',
            user=user_id
        )

        return Response({
            'item': ChecklistItemSerializer(item).data,
            'submission': ChecklistItemSubmissionSerializer(submission).data
        }, status=201)




class ChecklistItemInProgressByUserView(APIView):
    def get(self, request, user_id):
        submissions = ChecklistItemSubmission.objects.filter(status='IN_PROGRESS', user=user_id)
        serializer = ChecklistItemSubmissionSerializer(submissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class ChecklistItemCompletedByUserView(APIView):
    def get(self, request, user_id):
        submissions = ChecklistItemSubmission.objects.filter(status='COMPLETED', user=user_id)
        serializer = ChecklistItemSubmissionSerializer(submissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChecklistItemByCategoryStatusView(APIView):
    def get(self, request, cat_or_subcat_id):
        checklist_ids = Checklist.objects.filter(
            status='NOT_STARTED'
        ).filter(
            Q(category=cat_or_subcat_id) | Q(category_level1=cat_or_subcat_id)
        ).values_list('id', flat=True)
        items = ChecklistItem.objects.filter(checklist_id__in=checklist_ids, status='NOT_STARTED')
        serializer = ChecklistItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)





class AccessibleChecklistsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    USER_SERVICE_URL = "http://192.168.23.214:8000/api/user-access/"

    def get(self, request):
        user_id = request.user.id
        project_id = request.query_params.get("project_id")

        if not user_id or not project_id:
            return Response({"detail": "user_id and project_id required."}, status=400)

        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = requests.get(
                self.USER_SERVICE_URL,
                params={"user_id": user_id, "project_id": project_id},
                timeout=5,
                headers=headers
            )
            if resp.status_code != 200:
                return Response({"detail": "Could not fetch user access"}, status=400)
            accesses = resp.json()
        except Exception as e:
            return Response({"detail": "User service error", "error": str(e)}, status=400)

        q = Q()
        for access in accesses:
            # Category containment logic
            cat_q = Q()
            if access.get('category'):
                cat_q &= Q(category=access['category'])
                for i in range(1, 7):
                    key = f'CategoryLevel{i}'
                    if access.get(key) is not None:
                        cat_q &= Q(**{f'category_level{i}': access[key]})
                    else:
                        break

            # Location containment logic
            loc_q = Q()
            if access.get('flat_id'):
                loc_q &= Q(flat_id=access['flat_id'])
            elif access.get('zone_id'):
                loc_q &= Q(zone_id=access['zone_id'])
            elif access.get('building_id'):
                loc_q &= Q(building_id=access['building_id'])
            # If only project-level access, don't filter further (loc_q empty = all)

            q |= (cat_q & loc_q)

        checklists = Checklist.objects.filter(project_id=project_id, status='NOT_STARTED')
        if q:  # Only apply if any access was provided
            checklists = checklists.filter(q).distinct()
        else:
            checklists = Checklist.objects.none()

        serializer = ChecklistSerializer(checklists, many=True)
        print(serializer.data)
        return Response(serializer.data, status=200)




class MyInProgressChecklistItemSubmissions(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        queryset = ChecklistItemSubmission.objects.filter(
            status="IN_PROGRESS",
            user=user_id,
           selected_option__isnull=True
        )
        serializer = ChecklistItemSubmissionSerializer(queryset, many=True)
        return Response(serializer.data)
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Q
import requests

from .models import Checklist
from .serializers import ChecklistWithItemsAndPendingSubmissionsSerializer

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
import requests

# from .models import Checklist, ChecklistItem, ChecklistItemSubmission
# from .serializers import ChecklistItemSubmissionSerializer

# class AccessibleChecklistsWithPendingCheckerSubmissionsAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     USER_SERVICE_URL = "http://192.168.1.28:8000/api/user-access/"

#     def get(self, request):
#         user_id = request.user.id
#         project_id = request.query_params.get("project_id")
        
#         # A. By roles_json.checker assignment
#         assigned_checklists = Checklist.objects.filter(roles_json__checker__contains=[user_id])
#         assigned_submissions = ChecklistItemSubmission.objects.filter(
#             checklist_item__checklist__in=assigned_checklists,
#             checked_by_id__isnull=True,
#             status="DONE"
#         )

#         # B. By access (location/category)
#         location_submissions = ChecklistItemSubmission.objects.none()
#         if project_id:
#             token = None
#             auth_header = request.headers.get("Authorization")
#             if auth_header:
#                 token = auth_header.split(" ")[1] if " " in auth_header else auth_header
#             headers = {}
#             if token:
#                 headers["Authorization"] = f"Bearer {token}"
#             try:
#                 resp = requests.get(
#                     self.USER_SERVICE_URL,
#                     params={"user_id": user_id, "project_id": project_id},
#                     timeout=5,
#                     headers=headers
#                 )
#                 if resp.status_code == 200:
#                     accesses = resp.json()
#                     q = Q()
#                     for access in accesses:
#                         cat_q = Q()
#                         if access.get('category'):
#                             cat_q &= Q(checklist__category=access['category'])
#                             for i in range(1, 7):
#                                 key = f'CategoryLevel{i}'
#                                 if access.get(key) is not None:
#                                     cat_q &= Q(**{f'checklist__category_level{i}': access[key]})
#                                 else:
#                                     break
#                         loc_q = Q()
#                         if access.get('flat_id'):
#                             loc_q &= Q(checklist__flat_id=access['flat_id'])
#                         elif access.get('zone_id'):
#                             loc_q &= Q(checklist__zone_id=access['zone_id'])
#                         elif access.get('building_id'):
#                             loc_q &= Q(checklist__building_id=access['building_id'])
#                         q |= (cat_q & loc_q)
#                     checklist_items = ChecklistItem.objects.filter(status="DONE")
#                     if q:
#                         location_submissions = ChecklistItemSubmission.objects.filter(
#                             checklist_item__in=checklist_items.filter(q),
#                             checked_by_id__isnull=True,
#                             status="DONE"
#                         )
#             except Exception as e:
#                 # Log or handle the error as needed
#                 pass

#         # Merge both querysets, deduplicate, and order
#         all_submissions = assigned_submissions | location_submissions
#         all_submissions = all_submissions.distinct().order_by("-accepted_at")

#         serializer = ChecklistItemSubmissionSerializer(all_submissions, many=True)
#         return Response(serializer.data)



class AccessibleChecklistsWithPendingCheckerSubmissionsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    USER_SERVICE_URL = "http://192.168.23.214:8000/api/user-access/"

    def get(self, request):
        user_id = request.user.id
        project_id = request.query_params.get("project_id")

        if not user_id or not project_id:
            return Response({"detail": "user_id and project_id required."}, status=400)

        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = requests.get(
                self.USER_SERVICE_URL,
                params={"user_id": user_id, "project_id": project_id},
                timeout=5,
                headers=headers
            )
            if resp.status_code != 200:
                return Response({"detail": "Could not fetch user access"}, status=400)
            accesses = resp.json()
        except Exception as e:
            return Response({"detail": "User service error", "error": str(e)}, status=400)

        q = Q()
        for access in accesses:
            cat_q = Q()
            if access.get('category'):
                cat_q &= Q(category=access['category'])
                for i in range(1, 7):
                    key = f'CategoryLevel{i}'
                    if access.get(key) is not None:
                        cat_q &= Q(**{f'category_level{i}': access[key]})
                    else:
                        break
            loc_q = Q()
            if access.get('flat_id'):
                loc_q &= Q(flat_id=access['flat_id'])
            elif access.get('zone_id'):
                loc_q &= Q(zone_id=access['zone_id'])
            elif access.get('building_id'):
                loc_q &= Q(building_id=access['building_id'])
            q |= (cat_q & loc_q)

        checklists = Checklist.objects.filter(project_id=project_id, status='IN_PROGRESS')
        if q:
            checklists = checklists.filter(q).distinct()
        else:
            checklists = Checklist.objects.none()

        serializer = ChecklistWithItemsAndPendingSubmissionsSerializer(checklists, many=True)
        data = serializer.data

        # Filter out checklists with no items or where all items have no pending submissions
        filtered_data = []
        for cl in data:
            items_with_pending = [item for item in cl.get("items", []) if item.get("submissions")]
            if items_with_pending:
                cl["items"] = items_with_pending
                filtered_data.append(cl)
        print(filtered_data)
        return Response(filtered_data, status=200)



   
class CreateSubmissionsForChecklistItemsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        checklist_id = request.data.get('checklist_id')
        user_id = request.user.id

        if not checklist_id:
            return Response({"detail": "checklist_id is required."}, status=400)
        checklist=Checklist.objects.get(id=checklist_id)
        checklist.status='IN_PROGRESS'
        checklist.save()
    
        items = ChecklistItem.objects.filter(checklist_id=checklist_id)
        created = []
        for item in items:
            obj, created_flag = ChecklistItemSubmission.objects.get_or_create(
                checklist_item=item,
                user=user_id,
            )
            item.status="IN_PROGRESS"
            item.save()
            created.append(obj.id)
        
        return Response({
            "message": f"Submissions created for checklist {checklist_id}",
            "submission_ids": created
        }, status=status.HTTP_201_CREATED)
    



class PatchChecklistItemSubmissionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        submission_id = request.data.get("submission_id")
        maker_photo = request.FILES.get("maker_photo")

        if not submission_id:
            return Response({"detail": "submission_id is required."}, status=400)
        
        try:
            submission = ChecklistItemSubmission.objects.get(id=submission_id)
        except ChecklistItemSubmission.DoesNotExist:
            return Response({"detail": "ChecklistItemSubmission not found."}, status=404)
        
        submission.status="COMPLETED"
        submission.save()
        if maker_photo:
            submission.maker_photo = maker_photo
            
            submission.save(update_fields=["maker_photo"])
            item = submission.checklist_item
            item.status = "DONE"
            item.save(update_fields=["status"])
            return Response({
                "message": "Photo uploaded to ChecklistItemSubmission.",
                "submission_id": submission.id,
                "maker_photo": submission.maker_photo.url if submission.maker_photo else None,
            }, status=200)
        else:
            item = submission.checklist_item
            item.status = "DONE"
            item.save(update_fields=["status"])
            return Response({
                "message": "ChecklistItem marked as DONE.",
                "checklist_item_id": item.id,
                "status": item.status,
            }, status=200)


# Replace your MyHierarchicalVerificationsAPIView with this:

# Replace your MyHierarchicalVerificationsAPIView with this FINAL corrected version:

class MyHierarchicalVerificationsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user_id = request.user.id
        print(f"🔍 Fetching verifications for checker user_id: {user_id}")
        
        try:
            # Method 1: Try direct ORM query first
            print("🔄 Attempting direct ORM query...")
            
            try:
                checklists = Checklist.objects.filter(
                    items_submissions_checked_by_id=user_id,
                    items_submissionsselected_option_isnull=True
                ).distinct()
                print(f"📊 Direct query found {checklists.count()} checklists")
            except Exception as orm_error:
                print(f"⚠ Direct ORM query failed: {orm_error}")
                checklists = Checklist.objects.none()
            
            # Method 2: Fallback to submission-based lookup
            if checklists.count() == 0:
                print("🔄 Using fallback method: submission-based lookup...")
                
                # Get all pending submissions for this checker
                pending_submissions = ChecklistItemSubmission.objects.filter(
                    checked_by_id=user_id,
                    selected_option__isnull=True
                )
                
                print(f"📝 Found {pending_submissions.count()} pending submissions for checker {user_id}")
                
                if pending_submissions.exists():
                    # Get checklist IDs from those submissions
                    checklist_ids = set()
                    for submission in pending_submissions:
                        if submission.checklist_item and submission.checklist_item.checklist:
                            checklist_ids.add(submission.checklist_item.checklist.id)
                    
                    print(f"📋 Found checklist IDs: {list(checklist_ids)}")
                    
                    # Get the checklists
                    checklists = Checklist.objects.filter(id__in=checklist_ids)
                    print(f"📊 Fallback method found {checklists.count()} checklists")
            
            if checklists.count() == 0:
                print("ℹ No checklists found needing verification")
                return Response([], status=200)
            
            # Serialize the checklists
            serializer = ChecklistWithNestedItemsSerializer(
                checklists, 
                many=True, 
                context={"request": request}
            )
            
            print(f"📦 Serialized {len(serializer.data)} checklists")
            
            # Filter to only include items with pending submissions
            data = []
            for checklist in serializer.data:
                items_with_pending_subs = []
                
                for item in checklist["items"]:
                    # Only include items that have submissions needing verification
                    pending_subs = [
                        sub for sub in item["submissions"] 
                        if (sub["selected_option"] is None and 
                            sub["checked_by_id"] == user_id)
                    ]
                    
                    if pending_subs:
                        # Create a copy of the item with only pending submissions
                        item_copy = item.copy()
                        item_copy["submissions"] = pending_subs
                        items_with_pending_subs.append(item_copy)
                        print(f"  📝 Item {item['id']}: {len(pending_subs)} pending submissions")
                
                if items_with_pending_subs:
                    checklist_copy = checklist.copy()
                    checklist_copy["items"] = items_with_pending_subs
                    checklist_copy["total_pending_verifications"] = sum(
                        len(item["submissions"]) for item in items_with_pending_subs
                    )
                    data.append(checklist_copy)
                    print(f"✅ Checklist {checklist['id']}: {checklist['name']} has {len(items_with_pending_subs)} items to verify")
            
            print(f"🎯 Returning {len(data)} checklists for verification")
            
            # Debug: Print sample data structure
            if data:
                sample_checklist = data[0]
                print(f"📋 Sample checklist structure:")
                print(f"  - ID: {sample_checklist.get('id')}")
                print(f"  - Name: {sample_checklist.get('name')}")
                print(f"  - Items count: {len(sample_checklist.get('items', []))}")
                if sample_checklist.get('items'):
                    sample_item = sample_checklist['items'][0]
                    print(f"  - Sample item submissions: {len(sample_item.get('submissions', []))}")
            
            return Response(data, status=200)
            
        except Exception as e:
            print(f"❌ Error in MyHierarchicalVerificationsAPIView: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Failed to fetch verifications: {str(e)}"}, 
                status=500
            )
        



from django.utils import timezone

class BulkVerifyChecklistItemSubmissionsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        ids = request.data.get("submission_ids")
        user_id = request.user.id

        if not ids or not isinstance(ids, list):
            return Response({"detail": "submission_ids (list) required."}, status=400)

        updated = []
        for submission_id in ids:
            try:
                submission = ChecklistItemSubmission.objects.get(id=submission_id)
            except ChecklistItemSubmission.DoesNotExist:
                continue  # skip if not found

            # Update submission
            submission.checked_by_id = user_id
            submission.checked_at = timezone.now()
            submission.save(update_fields=["checked_by_id", "checked_at"])

            # Update related item
            item = submission.checklist_item
            # item.status = "VERIFYING"
            item.save(update_fields=["status"])

            updated.append(submission_id)

        return Response({
            "message": "Submissions verified and checklist items set to VERIFYING.",
            "verified_submission_ids": updated
        }, status=200)
    


from django.utils import timezone


class VerifyChecklistItemSubmissionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        # Print the whole request.data and request.FILES for debugging
        # print("PATCH DATA:", request.data)
        # print("PATCH FILES:", request.FILES)

        submission_id = request.data.get('submission_id')
        role = request.data.get('role')  # "checker" or "inspector"
        option_id = request.data.get('option_id')
        check_remark = request.data.get('check_remark', '')
        check_photo = request.FILES.get('check_photo', None)

        # Print parsed values
        print("submission_id:", submission_id)
        print("role:", role)
        print("option_id:", option_id)
        print("check_remark:", check_remark)
        print("check_photo:", check_photo)

        if not submission_id or not role or not option_id:
            print("❌ Required field missing in request")
            return Response({"detail": "submission_id, role, and option_id are required."}, status=400)

        # Get objects
        try:
            submission = ChecklistItemSubmission.objects.select_related('checklist_item').get(id=submission_id)
        except ChecklistItemSubmission.DoesNotExist:
            print("❌ Submission not found")
            return Response({"detail": "ChecklistItemSubmission not found."}, status=404)

        try:
            option = ChecklistItemOption.objects.get(id=option_id)
        except ChecklistItemOption.DoesNotExist:
            print("❌ Option not found")
            return Response({"detail": "ChecklistItemOption not found."}, status=404)

        item = submission.checklist_item
        print('item',item.status)
        print('item',item.id)
        # --- Checker Logic ---
        if role == "checker":
            print("Checker logic triggered. Current item.status:", item.status)
            if item.status not in ["DONE", "IN_PROGRESS"]:
                print("❌ Item status is not DONE (it's %s)" % item.status)
                return Response({"detail": "Item must be DONE before checker can act."}, status=400)
            submission.check_remark = check_remark
            submission.checked_by_id = request.user.id
            submission.checked_at = timezone.now()
            # submission.selected_option = option

            if option.value == "N":
                # Mark the current submission as rejected and item not started
                item.status = "NOT_STARTED"
                submission.status = "REJECTED"
                item.save(update_fields=["status"])
                submission.save(update_fields=["check_remark", "checked_by_id", "checked_at", "status"])
                item.status = "IN_PROGRESS"
                item.save(update_fields=["status"])
                new_submission = ChecklistItemSubmission.objects.create(
                    checklist_item=item,
                    status="IN_PROGRESS",
                    user=submission.user  # reassign to the original maker
                )
                
                print(f"Reopened item {item.id} for Maker {submission.user}, new submission {new_submission.id}")

            elif option.value == "P":
                item.status = "VERIFIED"
            else:
                print("❌ Invalid option value for checker:", option.value)
                return Response({"detail": "Invalid option for checker."}, status=400)

            item.save(update_fields=["status"])
            submission.save(update_fields=["check_remark", "checked_by_id", "checked_at", "status"])

        # --- Inspector Logic ---
        elif role == "SUPERVISOR":
            print("Supervisor logic triggered. Current item.status:", item.status)
            if item.status != "VERIFIED":
                print("❌ Item status is not VERIFIED (it's %s)" % item.status)
                return Response({"detail": "Item must be VERIFIED before supervisor can act."}, status=400)
            if check_photo:
                submission.check_photo = check_photo
            submission.check_remark = check_remark
            submission.inspected_by_id = request.user.id
            submission.inspected_at = timezone.now()
            # submission.selected_option = option

            if option.value == "P":
                item.status = "COMPLETED"
                submission.status = "COMPLETED"
                item.save(update_fields=["status"])
                submission.save(update_fields=[
                    "check_photo", "check_remark", "inspected_by_id", "inspected_at", "status"
                ])
            elif option.value == "N":
                # Supervisor rejected: restart for maker
                item.status = "NOT_STARTED"
                submission.status = "REJECTED"
                item.save(update_fields=["status"])
                submission.save(update_fields=[
                    "check_photo", "check_remark", "inspected_by_id", "inspected_at", "status"
                ])
                # Mark item as IN_PROGRESS for new submission
                item.status = "IN_PROGRESS"
                item.save(update_fields=["status"])
                new_submission = ChecklistItemSubmission.objects.create(
                    checklist_item=item,
                    status="IN_PROGRESS",
                    user=submission.user  # original maker
                )
                print(f"Reopened item {item.id} for Maker {submission.user}, new submission {new_submission.id}")
            else:
                print("❌ Invalid option value for supervisor:", option.value)
                return Response({"detail": "Invalid option for supervisor."}, status=400)


            item.save(update_fields=["status"])
            submission.save(update_fields=["check_photo", "check_remark", "inspected_by_id", "inspected_at", "status"])
        else:
            print("❌ Invalid role:", role)
            return Response({"detail": "Invalid role. Must be 'checker' or 'inspector'."}, status=400)

        print("✅ Success! Item and submission updated.")
        return Response({
            "item_id": item.id,
            "item_status": item.status,
            "submission_id": submission.id,
            "submission_status": submission.status,
        }, status=200)




# from rest_framework.permissions import IsAuthenticated

# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from django.db.models import Q
# import requests

# from .models import Checklist, ChecklistItem, ChecklistItemSubmission
# from .serializers import ChecklistItemSubmissionSerializer

# class VerifiedByCheckerPendingInspectorAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     USER_SERVICE_URL = "http://192.168.1.28:8000/api/user-access/"

#     def get(self, request):
#         user_id = request.user.id
#         project_id = request.query_params.get("project_id")
#         results = []

#         # A. Assigned by roles_json.supervisor
#         assigned_checklists = Checklist.objects.filter(roles_json__supervisor__contains=[user_id])
#         assigned_submissions = ChecklistItemSubmission.objects.filter(
#             checklist_item__checklist__in=assigned_checklists,
#             inspected_by_id__isnull=True,
#             status="VERIFIED"
#         )

#         # B. By access (location/category)
#         location_submissions = ChecklistItemSubmission.objects.none()
#         if project_id:
#             # --- Fetch access from user-access service ---
#             token = None
#             auth_header = request.headers.get("Authorization")
#             if auth_header:
#                 token = auth_header.split(" ")[1] if " " in auth_header else auth_header

#             headers = {}
#             if token:
#                 headers["Authorization"] = f"Bearer {token}"

#             try:
#                 resp = requests.get(
#                     self.USER_SERVICE_URL,
#                     params={"user_id": user_id, "project_id": project_id},
#                     timeout=5,
#                     headers=headers
#                 )
#                 if resp.status_code == 200:
#                     accesses = resp.json()
#                     q = Q()
#                     for access in accesses:
#                         cat_q = Q()
#                         if access.get('category'):
#                             cat_q &= Q(checklist__category=access['category'])
#                             for i in range(1, 7):
#                                 key = f'CategoryLevel{i}'
#                                 if access.get(key) is not None:
#                                     cat_q &= Q(**{f'checklist__category_level{i}': access[key]})
#                                 else:
#                                     break

#                         loc_q = Q()
#                         if access.get('flat_id'):
#                             loc_q &= Q(checklist__flat_id=access['flat_id'])
#                         elif access.get('zone_id'):
#                             loc_q &= Q(checklist__zone_id=access['zone_id'])
#                         elif access.get('building_id'):
#                             loc_q &= Q(checklist__building_id=access['building_id'])

#                         q |= (cat_q & loc_q)

#                     checklist_items = ChecklistItem.objects.filter(status="VERIFIED")
#                     if q:
#                         location_submissions = ChecklistItemSubmission.objects.filter(
#                             checklist_item__in=checklist_items.filter(q),
#                             inspected_by_id__isnull=True,
#                             status="VERIFIED"
#                         )
#             except Exception as e:
#                 # If access fetch fails, ignore location submissions
#                 pass

#         # Merge both querysets and deduplicate
#         all_submissions = assigned_submissions | location_submissions
#         all_submissions = all_submissions.distinct().order_by("-accepted_at")

#         serializer = ChecklistItemSubmissionSerializer(all_submissions, many=True)
#         return Response(serializer.data)


class VerifiedByCheckerPendingInspectorAPIView(APIView):
    permission_classes = [IsAuthenticated]
    USER_SERVICE_URL = "http://192.168.23.214:8000/api/user-access/"

    def get(self, request):
        user_id = request.user.id
        project_id = request.query_params.get("project_id")

        if not user_id or not project_id:
            return Response({"detail": "user_id and project_id required."}, status=400)

        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = requests.get(
                self.USER_SERVICE_URL,
                params={"user_id": user_id, "project_id": project_id},
                timeout=5,
                headers=headers
            )
            if resp.status_code != 200:
                return Response({"detail": "Could not fetch user access"}, status=400)
            accesses = resp.json()

        except Exception as e:
            return Response({"detail": "User service error", "error": str(e)}, status=400)
        print(accesses)
        print(Checklist.objects.filter(project_id=34))
        q = Q()
        for access in accesses:
            cat_q = Q()
            if access.get('category'):
                cat_q &= Q(checklist__category=access['category'])
                for i in range(1, 7):
                    key = f'CategoryLevel{i}'
                    if access.get(key) is not None:
                        cat_q &= Q(**{f'checklist__category_level{i}': access[key]})
                    else:
                        break

            loc_q = Q()
            if access.get('flat_id'):
                loc_q &= Q(checklist__flat_id=access['flat_id'])
            elif access.get('zone_id'):
                loc_q &= Q(checklist__zone_id=access['zone_id'])
            elif access.get('building_id'):
                loc_q &= Q(checklist__building_id=access['building_id'])

            q |= (cat_q & loc_q)

        checklist_items = ChecklistItem.objects.filter( status="VERIFIED")

        submissions = ChecklistItemSubmission.objects.filter(
            checklist_item__in=checklist_items,
            status="COMPLETED",
            checked_by_id__isnull=False,
            checked_at__isnull=False,
            inspected_by_id__isnull=True,
            inspected_at__isnull=True,
            # selected_option__isnull=True,  
        ).order_by("-accepted_at")

        serializer = ChecklistItemSubmissionSerializer(submissions, many=True)
        
        # PRINT THE DATA BEFORE RETURNING IT
        print("🔍 Submissions Data:", serializer.data)
        
        return Response(serializer.data, status=200)




class MyChecklistItemSubmissions(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user_id = request.user.id
        submissions = ChecklistItemSubmission.objects.filter(user=user_id)
        serializer = ChecklistItemSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)




class PendingVerificationsForCheckerAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user_id = request.user.id
        # Find all checklists where this user is a checker
        checklists = Checklist.objects.filter(roles_json__checker__contains=[user_id])
        submissions = ChecklistItemSubmission.objects.filter(
            checklist_item__checklist__in=checklists,
            checked_by_id__isnull=True,  # Not yet checked
            status="DONE"
        )
        serializer = ChecklistItemSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)





class PendingVerificationsForSupervisorAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user_id = request.user.id
        checklists = Checklist.objects.filter(roles_json__supervisor__contains=[user_id])
        submissions = ChecklistItemSubmission.objects.filter(
            checklist_item__checklist__in=checklists,
            inspected_by_id__isnull=True,  
            status="VERIFIED"
        )
        serializer = ChecklistItemSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)




from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Checklist
import json

class PatchChecklistRolesJsonAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, checklist_id):
        # Accept roles_json as a dict or string
        roles_json = request.data.get('roles_json')
        if not roles_json:
            return Response({'roles_json': 'This field is required.'}, status=400)
        # Parse JSON if sent as a string
        if isinstance(roles_json, str):
            try:
                roles_json = json.loads(roles_json)
            except Exception as e:
                return Response({'roles_json': 'Invalid JSON format.'}, status=400)
        # Get the checklist
        try:
            checklist = Checklist.objects.get(id=checklist_id)
        except Checklist.DoesNotExist:
            return Response({'error': 'Checklist not found.'}, status=404)
        # Update and save
        checklist.roles_json = roles_json
        checklist.save(update_fields=['roles_json'])
        return Response({'message': 'roles_json updated.', 'roles_json': checklist.roles_json}, status=200)



























# import requests
# from .models import Checklist
# from django.db.models import Q
# from rest_framework import viewsets,permissions
# from .models import Checklist, ChecklistItem, ChecklistItemSubmission, ChecklistItemOption
# from .serializers import ChecklistSerializer, ChecklistItemSerializer, ChecklistItemSubmissionSerializer,ChecklistSerializer,ChecklistItemOptionSerializer,ChecklistWithItemsAndFilteredSubmissionsSerializer,ChecklistWithItemsAndFilteredSubmissionsSerializer,ChecklistWithNestedItemsSerializer,ChecklistWithItemsAndPendingSubmissionsSerializer
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework import status


# class ChecklistItemOptionViewSet(viewsets.ModelViewSet):
#     queryset = ChecklistItemOption.objects.all()
#     serializer_class = ChecklistItemOptionSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def create(self, request, *args, **kwargs):
#         print("Creating ChecklistItemOption with data:", request.data)
#         serializer = self.get_serializer(data=request.data)
#         if not serializer.is_valid():
#             print("ChecklistItemOption Validation Errors:", serializer.errors)
#             return Response(serializer.errors, status=400)
#         self.perform_create(serializer)
#         print("ChecklistItemOption created successfully:", serializer.data)
#         return Response(serializer.data, status=201)


# class ChecklistViewSet(viewsets.ModelViewSet):
#     permission_classes = [permissions.IsAuthenticated]
#     queryset = Checklist.objects.all()
#     serializer_class = ChecklistSerializer

#     def create(self, request, *args, **kwargs):
#         print("Creating Checklist with data:", request.data)
        
#         # Validate required fields before serializer
#         if not request.data.get('project_id'):
#             return Response({"project_id": ["This field is required."]}, status=400)
#         if not request.data.get('purpose_id'):
#             return Response({"purpose_id": ["This field is required."]}, status=400)
#         if not request.data.get('category'):
#             return Response({"category": ["This field is required."]}, status=400)
#         if not request.data.get('name'):
#             return Response({"name": ["This field is required."]}, status=400)
            
#         serializer = self.get_serializer(data=request.data)
#         if not serializer.is_valid():
#             print("Checklist Validation Errors:", serializer.errors)
#             return Response(serializer.errors, status=400)
        
#         self.perform_create(serializer)
#         print("Checklist created successfully:", serializer.data)
#         return Response(serializer.data, status=201)
    
#     def get_queryset(self):
#         queryset = super().get_queryset()
#         project_id = self.request.query_params.get("project")
#         if project_id:
#             queryset = queryset.filter(project_id=project_id)
#         return queryset


# class ChecklistItemViewSet(viewsets.ModelViewSet):
#     permission_classes = [permissions.IsAuthenticated]
#     queryset = ChecklistItem.objects.all()
#     serializer_class = ChecklistItemSerializer

#     def create(self, request, *args, **kwargs):
#         print("Creating ChecklistItem with data:", request.data)
        
#         # Validate required fields
#         if not request.data.get('checklist'):
#             return Response({"checklist": ["This field is required."]}, status=400)
#         if not request.data.get('description'):
#             return Response({"description": ["This field is required."]}, status=400)
            
#         serializer = self.get_serializer(data=request.data)
#         if not serializer.is_valid():
#             print("ChecklistItem Validation Errors:", serializer.errors)
#             return Response(serializer.errors, status=400)
        
#         self.perform_create(serializer)
#         print("ChecklistItem created successfully:", serializer.data)
#         return Response(serializer.data, status=201)
    
#     @action(detail=False, methods=['get'])
#     def by_checklist(self, request):
#         checklist_id = request.query_params.get('checklist_id')
#         if not checklist_id:
#             return Response({"error": "checklist_id is required"}, status=400)
#         items = self.get_queryset().filter(checklist_id=checklist_id)
#         serializer = self.get_serializer(items, many=True)
#         return Response(serializer.data)


# class ChecklistItemSubmissionViewSet(viewsets.ModelViewSet):
#     permission_classes = [permissions.IsAuthenticated]
#     queryset = ChecklistItemSubmission.objects.all()
#     serializer_class = ChecklistItemSubmissionSerializer

#     def create(self, request, *args, **kwargs):
#         print("Creating ChecklistItemSubmission with data:", request.data)
#         serializer = self.get_serializer(data=request.data)
#         if not serializer.is_valid():
#             print("ChecklistItemSubmission Validation Errors:", serializer.errors)
#             return Response(serializer.errors, status=400)
#         self.perform_create(serializer)
#         print("ChecklistItemSubmission created successfully:", serializer.data)
#         return Response(serializer.data, status=201)

#     @action(detail=False, methods=['get'])
#     def All_Checklist_Record(self, request):
#         check_listItem_id = request.query_params.get('check_listItem_id')
#         if not check_listItem_id:
#             return Response({"error": "checklist_id is required"}, status=400)
#         items = self.get_queryset().filter(checklist_item_id=check_listItem_id)
#         serializer = self.get_serializer(items, many=True)
#         return Response(serializer.data)


# class StartChecklistItemAPIView(APIView):
#     def post(self, request, user_id, item_id):
#         try:
#             item = ChecklistItem.objects.get(id=item_id, status='NOT_STARTED')
#         except ChecklistItem.DoesNotExist:
#             return Response({'error': 'ChecklistItem not found or not in NOT_STARTED status.'}, status=404)

#         item.status = 'IN_PROGRESS'
#         item.save()

#         submission = ChecklistItemSubmission.objects.create(
#             checklist_item=item,
#             status='IN_PROGRESS',
#             user=user_id
#         )

#         return Response({
#             'item': ChecklistItemSerializer(item).data,
#             'submission': ChecklistItemSubmissionSerializer(submission).data
#         }, status=201)


# class ChecklistItemInProgressByUserView(APIView):
#     def get(self, request, user_id):
#         submissions = ChecklistItemSubmission.objects.filter(status='IN_PROGRESS', user=user_id)
#         serializer = ChecklistItemSubmissionSerializer(submissions, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)


# class ChecklistItemCompletedByUserView(APIView):
#     def get(self, request, user_id):
#         submissions = ChecklistItemSubmission.objects.filter(status='COMPLETED', user=user_id)
#         serializer = ChecklistItemSubmissionSerializer(submissions, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)


# class ChecklistItemByCategoryStatusView(APIView):
#     def get(self, request, cat_or_subcat_id):
#         checklist_ids = Checklist.objects.filter(
#             status='NOT_STARTED'
#         ).filter(
#             Q(category=cat_or_subcat_id) | Q(category_level1=cat_or_subcat_id)
#         ).values_list('id', flat=True)
#         items = ChecklistItem.objects.filter(checklist_id__in=checklist_ids, status='NOT_STARTED')
#         serializer = ChecklistItemSerializer(items, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)





# class AccessibleChecklistsAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     USER_SERVICE_URL = "http://192.168.1.28:8000/api/user-access/"

#     def get(self, request):
#         user_id = request.user.id
#         project_id = request.query_params.get("project_id")

#         if not user_id or not project_id:
#             return Response({"detail": "user_id and project_id required."}, status=400)

#         token = None
#         auth_header = request.headers.get("Authorization")
#         if auth_header:
#             token = auth_header.split(" ")[1] if " " in auth_header else auth_header

#         headers = {}
#         if token:
#             headers["Authorization"] = f"Bearer {token}"

#         try:
#             resp = requests.get(
#                 self.USER_SERVICE_URL,
#                 params={"user_id": user_id, "project_id": project_id},
#                 timeout=5,
#                 headers=headers
#             )
#             if resp.status_code != 200:
#                 return Response({"detail": "Could not fetch user access"}, status=400)
#             accesses = resp.json()
#         except Exception as e:
#             return Response({"detail": "User service error", "error": str(e)}, status=400)

#         q = Q()
#         for access in accesses:
#             # Category containment logic
#             cat_q = Q()
#             if access.get('category'):
#                 cat_q &= Q(category=access['category'])
#                 for i in range(1, 7):
#                     key = f'CategoryLevel{i}'
#                     if access.get(key) is not None:
#                         cat_q &= Q(**{f'category_level{i}': access[key]})
#                     else:
#                         break

#             # Location containment logic
#             loc_q = Q()
#             if access.get('flat_id'):
#                 loc_q &= Q(flat_id=access['flat_id'])
#             elif access.get('zone_id'):
#                 loc_q &= Q(zone_id=access['zone_id'])
#             elif access.get('building_id'):
#                 loc_q &= Q(building_id=access['building_id'])
           

#             q |= (cat_q & loc_q)

#         checklists = Checklist.objects.filter(project_id=project_id, status='NOT_STARTED')
#         if q:  
#             checklists = checklists.filter(q).distinct()
#         else:
#             checklists = Checklist.objects.none()

#         serializer = ChecklistSerializer(checklists, many=True)
#         print(serializer.data)
#         return Response(serializer.data, status=200)




# class MyInProgressChecklistItemSubmissions(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request):
#         user_id = request.user.id
#         queryset = ChecklistItemSubmission.objects.filter(
#             status="IN_PROGRESS",
#             user=user_id,
#            selected_option__isnull=True
#         )
#         serializer = ChecklistItemSubmissionSerializer(queryset, many=True)
#         return Response(serializer.data)
    



# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import permissions
# from django.db.models import Q
# import requests

# from .models import Checklist
# from .serializers import ChecklistWithItemsAndPendingSubmissionsSerializer

# class AccessibleChecklistsWithPendingCheckerSubmissionsAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     USER_SERVICE_URL = "http://192.168.1.28:8000/api/user-access/"

#     def get(self, request):
#         user_id = request.user.id
#         project_id = request.query_params.get("project_id")

#         if not user_id or not project_id:
#             return Response({"detail": "user_id and project_id required."}, status=400)

#         token = None
#         auth_header = request.headers.get("Authorization")
#         if auth_header:
#             token = auth_header.split(" ")[1] if " " in auth_header else auth_header

#         headers = {}
#         if token:
#             headers["Authorization"] = f"Bearer {token}"

#         try:
#             resp = requests.get(
#                 self.USER_SERVICE_URL,
#                 params={"user_id": user_id, "project_id": project_id},
#                 timeout=5,
#                 headers=headers
#             )
#             if resp.status_code != 200:
#                 return Response({"detail": "Could not fetch user access"}, status=400)
#             accesses = resp.json()
#         except Exception as e:
#             return Response({"detail": "User service error", "error": str(e)}, status=400)

#         q = Q()
#         for access in accesses:
#             cat_q = Q()
#             if access.get('category'):
#                 cat_q &= Q(category=access['category'])
#                 for i in range(1, 7):
#                     key = f'CategoryLevel{i}'
#                     if access.get(key) is not None:
#                         cat_q &= Q(**{f'category_level{i}': access[key]})
#                     else:
#                         break
#             loc_q = Q()
#             if access.get('flat_id'):
#                 loc_q &= Q(flat_id=access['flat_id'])
#             elif access.get('zone_id'):
#                 loc_q &= Q(zone_id=access['zone_id'])
#             elif access.get('building_id'):
#                 loc_q &= Q(building_id=access['building_id'])
#             q |= (cat_q & loc_q)

#         checklists = Checklist.objects.filter(project_id=project_id, status='IN_PROGRESS')
#         if q:
#             checklists = checklists.filter(q).distinct()
#         else:
#             checklists = Checklist.objects.none()

#         serializer = ChecklistWithItemsAndPendingSubmissionsSerializer(checklists, many=True)
#         data = serializer.data

#         # Filter out checklists with no items or where all items have no pending submissions
#         filtered_data = []
#         for cl in data:
#             items_with_pending = [item for item in cl.get("items", []) if item.get("submissions")]
#             if items_with_pending:
#                 cl["items"] = items_with_pending
#                 filtered_data.append(cl)
#         print(filtered_data)
#         return Response(filtered_data, status=200)



   
# class CreateSubmissionsForChecklistItemsAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request):
#         checklist_id = request.data.get('checklist_id')
#         user_id = request.user.id

#         if not checklist_id:
#             return Response({"detail": "checklist_id is required."}, status=400)
#         checklist=Checklist.objects.get(id=checklist_id)
#         checklist.status='IN_PROGRESS'
#         checklist.save()
    
#         items = ChecklistItem.objects.filter(checklist_id=checklist_id)
#         created = []
#         for item in items:
#             obj, created_flag = ChecklistItemSubmission.objects.get_or_create(
#                 checklist_item=item,
#                 user=user_id,
#             )
#             item.status="IN_PROGRESS"
#             item.save()
#             created.append(obj.id)
        
#         return Response({
#             "message": f"Submissions created for checklist {checklist_id}",
#             "submission_ids": created
#         }, status=status.HTTP_201_CREATED)
    



# class PatchChecklistItemSubmissionAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def patch(self, request):
#         submission_id = request.data.get("submission_id")
#         maker_photo = request.FILES.get("maker_photo")

#         if not submission_id:
#             return Response({"detail": "submission_id is required."}, status=400)
        
#         try:
#             submission = ChecklistItemSubmission.objects.get(id=submission_id)
#         except ChecklistItemSubmission.DoesNotExist:
#             return Response({"detail": "ChecklistItemSubmission not found."}, status=404)
        
#         submission.status="COMPLETED"
#         submission.save()
#         if maker_photo:
#             submission.maker_photo = maker_photo
            
#             submission.save(update_fields=["maker_photo"])
#             item = submission.checklist_item
#             item.status = "DONE"
#             item.save(update_fields=["status"])
#             return Response({
#                 "message": "Photo uploaded to ChecklistItemSubmission.",
#                 "submission_id": submission.id,
#                 "maker_photo": submission.maker_photo.url if submission.maker_photo else None,
#             }, status=200)
#         else:
#             item = submission.checklist_item
#             item.status = "DONE"
#             item.save(update_fields=["status"])
#             return Response({
#                 "message": "ChecklistItem marked as DONE.",
#                 "checklist_item_id": item.id,
#                 "status": item.status,
#             }, status=200)


# # Replace your MyHierarchicalVerificationsAPIView with this:

# # Replace your MyHierarchicalVerificationsAPIView with this FINAL corrected version:

# # class MyHierarchicalVerificationsAPIView(APIView):
# #     permission_classes = [permissions.IsAuthenticated]
    
# #     def get(self, request):
# #         user_id = request.user.id
# #         print(f"🔍 Fetching verifications for checker user_id: {user_id}")
        
# #         try:
# #             # Method 1: Try direct ORM query first
# #             print("🔄 Attempting direct ORM query...")
            
# #             try:
# #                 checklists = Checklist.objects.filter(
# #                     items_submissions_checked_by_id=user_id,
# #                     items_submissionsselected_option_isnull=True
# #                 ).distinct()
# #                 print(f"📊 Direct query found {checklists.count()} checklists")
# #             except Exception as orm_error:
# #                 print(f"⚠ Direct ORM query failed: {orm_error}")
# #                 checklists = Checklist.objects.none()
            
# #             # Method 2: Fallback to submission-based lookup
# #             if checklists.count() == 0:
# #                 print("🔄 Using fallback method: submission-based lookup...")
                
# #                 # Get all pending submissions for this checker
# #                 pending_submissions = ChecklistItemSubmission.objects.filter(
# #                     checked_by_id=user_id,
# #                     selected_option__isnull=True
# #                 )
                
# #                 print(f"📝 Found {pending_submissions.count()} pending submissions for checker {user_id}")
                
# #                 if pending_submissions.exists():
# #                     # Get checklist IDs from those submissions
# #                     checklist_ids = set()
# #                     for submission in pending_submissions:
# #                         if submission.checklist_item and submission.checklist_item.checklist:
# #                             checklist_ids.add(submission.checklist_item.checklist.id)
                    
# #                     print(f"📋 Found checklist IDs: {list(checklist_ids)}")
                    
# #                     # Get the checklists
# #                     checklists = Checklist.objects.filter(id__in=checklist_ids)
# #                     print(f"📊 Fallback method found {checklists.count()} checklists")
            
# #             if checklists.count() == 0:
# #                 print("ℹ No checklists found needing verification")
# #                 return Response([], status=200)
            
# #             # Serialize the checklists
# #             serializer = ChecklistWithNestedItemsSerializer(
# #                 checklists, 
# #                 many=True, 
# #                 context={"request": request}
# #             )
            
# #             print(f"📦 Serialized {len(serializer.data)} checklists")
            
# #             # Filter to only include items with pending submissions
# #             data = []
# #             for checklist in serializer.data:
# #                 items_with_pending_subs = []
                
# #                 for item in checklist["items"]:
# #                     # Only include items that have submissions needing verification
# #                     pending_subs = [
# #                         sub for sub in item["submissions"] 
# #                         if (sub["selected_option"] is None and 
# #                             sub["checked_by_id"] == user_id)
# #                     ]
                    
# #                     if pending_subs:
# #                         # Create a copy of the item with only pending submissions
# #                         item_copy = item.copy()
# #                         item_copy["submissions"] = pending_subs
# #                         items_with_pending_subs.append(item_copy)
# #                         print(f"  📝 Item {item['id']}: {len(pending_subs)} pending submissions")
                
# #                 if items_with_pending_subs:
# #                     checklist_copy = checklist.copy()
# #                     checklist_copy["items"] = items_with_pending_subs
# #                     checklist_copy["total_pending_verifications"] = sum(
# #                         len(item["submissions"]) for item in items_with_pending_subs
# #                     )
# #                     data.append(checklist_copy)
# #                     print(f"✅ Checklist {checklist['id']}: {checklist['name']} has {len(items_with_pending_subs)} items to verify")
            
# #             print(f"🎯 Returning {len(data)} checklists for verification")
            
# #             # Debug: Print sample data structure
# #             if data:
# #                 sample_checklist = data[0]
# #                 print(f"📋 Sample checklist structure:")
# #                 print(f"  - ID: {sample_checklist.get('id')}")
# #                 print(f"  - Name: {sample_checklist.get('name')}")
# #                 print(f"  - Items count: {len(sample_checklist.get('items', []))}")
# #                 if sample_checklist.get('items'):
# #                     sample_item = sample_checklist['items'][0]
# #                     print(f"  - Sample item submissions: {len(sample_item.get('submissions', []))}")
            
# #             return Response(data, status=200)
            
# #         except Exception as e:
# #             print(f"❌ Error in MyHierarchicalVerificationsAPIView: {str(e)}")
# #             import traceback
# #             traceback.print_exc()
# #             return Response(
# #                 {"error": f"Failed to fetch verifications: {str(e)}"}, 
# #                 status=500
# #             )
        
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import permissions 
# from .models import Checklist, ChecklistItemSubmission
# from .serializers import ChecklistWithNestedItemsSerializer



# class MyHierarchicalVerificationsAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request):
#         user_id = request.user.id
#         role = request.query_params.get('role')
#         submissions = ChecklistItemSubmission.objects.none()

#         if role == 'checker':
#             submissions = ChecklistItemSubmission.objects.filter(
#                 checked_by_id=user_id,
#                 status__in=['SUBMITTED', 'IN_PROGRESS'],
#                 selected_option__isnull=True
#             )

#         elif role == 'maker':
#             submissions = ChecklistItemSubmission.objects.filter(
#                 user=user_id,
#                 status__in=['IN_PROGRESS'],
#                 selected_option__isnull=True
#             )

#         elif role == 'supervisor':
#             submissions = ChecklistItemSubmission.objects.filter(
#                 inspected_by_id=user_id,
#                 status__in=['SUBMITTED'],
#                 selected_option__isnull=True
#             )
#         serializer = ChecklistItemSubmissionSerializer(submissions, many=True)
#         return Response(serializer.data, status=200)
    
# #     def get(self, request):
# #         user_id = request.user.id
# #         print(f"🔍 Fetching verifications for checker user_id: {user_id}")

# #         try:
# #             # Always look for submissions where checker needs to act:
# #             # - assigned as checked_by_id
# #             # - status IN_PROGRESS or SUBMITTED
# #             # - not yet selected_option (no decision yet)

# #             pending_submissions = ChecklistItemSubmission.objects.filter(
# #                 checked_by_id=user_id,
# #                 status__in=["IN_PROGRESS", "SUBMITTED"],
# #                 selected_option__isnull=True
# #             ).select_related('checklist_item__checklist')

# #             print(f"📝 Found {pending_submissions.count()} pending submissions for checker {user_id}")

# #             if not pending_submissions.exists():
# #                 print("ℹ No checklists found needing verification")
# #                 return Response([], status=200)

# #             # Gather all related checklist IDs
# #             checklist_ids = set()
# #             for submission in pending_submissions:
# #                 if submission.checklist_item and submission.checklist_item.checklist:
# #                     checklist_ids.add(submission.checklist_item.checklist.id)

# #             # Fetch all those checklists
# #             checklists = Checklist.objects.filter(id__in=checklist_ids).distinct()
# #             print(f"📊 Found {checklists.count()} checklists needing verification")

# #             # Serialize with nested items+submissions
# #             serializer = ChecklistWithNestedItemsSerializer(
# #                 checklists, many=True, context={"request": request}
# #             )

# #             # Only include items in each checklist that have pending submissions for THIS checker
# #             data = []
# #             for checklist in serializer.data:
# #                 items_with_pending_subs = []
# #                 for item in checklist.get("items", []):
# #                     # Only submissions for this checker that are pending
# #                     pending_subs = [
# #                         sub for sub in item.get("submissions", [])
# #                         if sub.get("selected_option") is None and
# #                            sub.get("checked_by_id") == user_id and
# #                            sub.get("status") in ["IN_PROGRESS", "SUBMITTED"]
# #                     ]
# #                     if pending_subs:
# #                         item_copy = item.copy()
# #                         item_copy["submissions"] = pending_subs
# #                         items_with_pending_subs.append(item_copy)
# #                         print(f"  📝 Item {item['id']}: {len(pending_subs)} pending submissions")

# #                 if items_with_pending_subs:
# #                     checklist_copy = checklist.copy()
# #                     checklist_copy["items"] = items_with_pending_subs
# #                     checklist_copy["total_pending_verifications"] = sum(
# #                         len(it["submissions"]) for it in items_with_pending_subs
# #                     )
# #                     data.append(checklist_copy)
# #                     print(f"✅ Checklist {checklist['id']}: {checklist['name']} has {len(items_with_pending_subs)} items to verify")

# #             print(f"🎯 Returning {len(data)} checklists for verification")
# #             return Response(data, status=200)

# #         except Exception as e:
# #             print(f"❌ Error in MyHierarchicalVerificationsAPIView: {str(e)}")
# #             import traceback
# #             traceback.print_exc()
# #             return Response(
# #                 {"error": f"Failed to fetch verifications: {str(e)}"}, 
# #                 status=500
# #             )




# from django.utils import timezone

# class BulkVerifyChecklistItemSubmissionsAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def patch(self, request):
#         ids = request.data.get("submission_ids")
#         user_id = request.user.id

#         if not ids or not isinstance(ids, list):
#             return Response({"detail": "submission_ids (list) required."}, status=400)

#         updated = []
#         for submission_id in ids:
#             try:
#                 submission = ChecklistItemSubmission.objects.get(id=submission_id)
#             except ChecklistItemSubmission.DoesNotExist:
#                 continue  # skip if not found

#             # Update submission
#             submission.checked_by_id = user_id
#             submission.checked_at = timezone.now()
#             submission.save(update_fields=["checked_by_id", "checked_at"])

#             # Update related item
#             item = submission.checklist_item
#             # item.status = "VERIFYING"
#             item.save(update_fields=["status"])

#             updated.append(submission_id)

#         return Response({
#             "message": "Submissions verified and checklist items set to VERIFYING.",
#             "verified_submission_ids": updated
#         }, status=200)
    


# from django.utils import timezone


# class VerifyChecklistItemSubmissionAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def patch(self, request):
#         # Print the whole request.data and request.FILES for debugging
#         # print("PATCH DATA:", request.data)
#         # print("PATCH FILES:", request.FILES)

#         submission_id = request.data.get('submission_id')
#         role = request.data.get('role')  # "checker" or "inspector"
#         option_id = request.data.get('option_id')
#         check_remark = request.data.get('check_remark', '')
#         check_photo = request.FILES.get('check_photo', None)

#         # Print parsed values
#         print("submission_id:", submission_id)
#         print("role:", role)
#         print("option_id:", option_id)
#         print("check_remark:", check_remark)
#         print("check_photo:", check_photo)

#         if not submission_id or not role or not option_id:
#             print("❌ Required field missing in request")
#             return Response({"detail": "submission_id, role, and option_id are required."}, status=400)

#         # Get objects
#         try:
#             submission = ChecklistItemSubmission.objects.select_related('checklist_item').get(id=submission_id)
#         except ChecklistItemSubmission.DoesNotExist:
#             print("❌ Submission not found")
#             return Response({"detail": "ChecklistItemSubmission not found."}, status=404)

#         try:
#             option = ChecklistItemOption.objects.get(id=option_id)
#         except ChecklistItemOption.DoesNotExist:
#             print("❌ Option not found")
#             return Response({"detail": "ChecklistItemOption not found."}, status=404)

#         item = submission.checklist_item
#         print('item',item.status)
#         print('item',item.id)
#         # --- Checker Logic ---
#         if role == "checker":
#             print("Checker logic triggered. Current item.status:", item.status)
#             if item.status not in ["DONE", "IN_PROGRESS"]:
#                 print("❌ Item status is not DONE (it's %s)" % item.status)
#                 return Response({"detail": "Item must be DONE before checker can act."}, status=400)
#             submission.check_remark = check_remark
#             submission.checked_by_id = request.user.id
#             submission.checked_at = timezone.now()
#             submission.selected_option = option

#             if option.value == "N":
#                 # Mark the current submission as rejected and item not started
#                 item.status = "NOT_STARTED"
#                 submission.status = "REJECTED"
#                 item.save(update_fields=["status"])
#                 submission.save(update_fields=["check_remark", "checked_by_id", "checked_at", "selected_option", "status"])
#                 item.status = "IN_PROGRESS"
#                 item.save(update_fields=["status"])
#                 new_submission = ChecklistItemSubmission.objects.create(
#                     checklist_item=item,
#                     status="IN_PROGRESS",
#                     user=submission.user  # reassign to the original maker
#                 )
                
#                 print(f"Reopened item {item.id} for Maker {submission.user}, new submission {new_submission.id}")

#             elif option.value == "P":
#                 item.status = "VERIFIED"
#             else:
#                 print("❌ Invalid option value for checker:", option.value)
#                 return Response({"detail": "Invalid option for checker."}, status=400)

#             item.save(update_fields=["status"])
#             submission.save(update_fields=["check_remark", "checked_by_id", "checked_at", "selected_option", "status"])

#         # --- Inspector Logic ---
#         elif role == "inspector":
#             print("Inspector logic triggered. Current item.status:", item.status)
#             if item.status != "VERIFIED":
#                 print("❌ Item status is not VERIFIED (it's %s)" % item.status)
#                 return Response({"detail": "Item must be VERIFIED before inspector can act."}, status=400)
#             if check_photo:
#                 submission.check_photo = check_photo
#             submission.check_remark = check_remark
#             submission.inspected_by_id = request.user.id
#             submission.inspected_at = timezone.now()
#             submission.selected_option = option

#             if option.value == "P":
#                 item.status = "COMPLETED"
#                 submission.status = "COMPLETED"
#             if option.value == "N":
#                 item.status = "NOT_STARTED"
#                 submission.status = "REJECTED"
#                 item.save(update_fields=["status"])
#                 submission.save(update_fields=[ ... ,"status"])
#                 item.status = "IN_PROGRESS"
#                 item.save(update_fields=["status"])
#                 new_submission = ChecklistItemSubmission.objects.create(
#                     checklist_item=item,
#                     status="IN_PROGRESS",
#                     user=submission.user
#                 )
#             else:
#                 print("❌ Invalid option value for inspector:", option.value)
#                 return Response({"detail": "Invalid option for inspector."}, status=400)

#             item.save(update_fields=["status"])
#             submission.save(update_fields=["check_photo", "check_remark", "inspected_by_id", "inspected_at", "selected_option", "status"])
#         else:
#             print("❌ Invalid role:", role)
#             return Response({"detail": "Invalid role. Must be 'checker' or 'inspector'."}, status=400)

#         print("✅ Success! Item and submission updated.")
#         return Response({
#             "item_id": item.id,
#             "item_status": item.status,
#             "submission_id": submission.id,
#             "submission_status": submission.status,
#         }, status=200)




# from rest_framework.permissions import IsAuthenticated


# class VerifiedByCheckerPendingInspectorAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     USER_SERVICE_URL = "http://192.168.1.28:8000/api/user-access/"

#     def get(self, request):
#         user_id = request.user.id
#         project_id = request.query_params.get("project_id")

#         if not user_id or not project_id:
#             return Response({"detail": "user_id and project_id required."}, status=400)

#         token = None
#         auth_header = request.headers.get("Authorization")
#         if auth_header:
#             token = auth_header.split(" ")[1] if " " in auth_header else auth_header

#         headers = {}
#         if token:
#             headers["Authorization"] = f"Bearer {token}"

#         try:
#             resp = requests.get(
#                 self.USER_SERVICE_URL,
#                 params={"user_id": user_id, "project_id": project_id},
#                 timeout=5,
#                 headers=headers
#             )
#             if resp.status_code != 200:
#                 return Response({"detail": "Could not fetch user access"}, status=400)
#             accesses = resp.json()
#         except Exception as e:
#             return Response({"detail": "User service error", "error": str(e)}, status=400)

#         q = Q()
#         for access in accesses:
#             cat_q = Q()
#             if access.get('category'):
#                 cat_q &= Q(checklist__category=access['category'])
#                 for i in range(1, 7):
#                     key = f'CategoryLevel{i}'
#                     if access.get(key) is not None:
#                         cat_q &= Q(**{f'checklist__category_level{i}': access[key]})
#                     else:
#                         break

#             loc_q = Q()
#             if access.get('flat_id'):
#                 loc_q &= Q(checklist__flat_id=access['flat_id'])
#             elif access.get('zone_id'):
#                 loc_q &= Q(checklist__zone_id=access['zone_id'])
#             elif access.get('building_id'):
#                 loc_q &= Q(checklist__building_id=access['building_id'])

#             q |= (cat_q & loc_q)

#         checklist_items = ChecklistItem.objects.filter(q, status="VERIFIED")

#         submissions = ChecklistItemSubmission.objects.filter(
#             checklist_item__in=checklist_items,
#             status="COMPLETED",
#             checked_by_id__isnull=False,
#             checked_at__isnull=False,
#             inspected_by_id__isnull=True,
#             inspected_at__isnull=True,
#             selected_option__isnull=True,  # Not yet reviewed by inspector
#         ).order_by("-accepted_at")

#         serializer = ChecklistItemSubmissionSerializer(submissions, many=True)
        
#         # PRINT THE DATA BEFORE RETURNING IT
#         print("🔍 Submissions Data:", serializer.data)
        
#         return Response(serializer.data, status=200)
    


# #added now
# class MyChecklistItemSubmissions(APIView):
#     permission_classes = [IsAuthenticated]
#     def get(self, request):
#         user_id = request.user.id
#         from .models import ChecklistItemSubmission
#         from .serializers import ChecklistItemSubmissionSerializer
#         submissions = ChecklistItemSubmission.objects.filter(user=user_id)
#         serializer = ChecklistItemSubmissionSerializer(submissions, many=True)
#         return Response(serializer.data)
    



# class PendingVerificationsForSupervisorAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user_id = request.user.id
#         checklists = Checklist.objects.filter(roles_json__supervisor__contains=[user_id])
#         submissions = ChecklistItemSubmission.objects.filter(
#             checklist_item__checklist__in=checklists,
#             inspected_by_id__isnull=True,  
#             status="VERIFIED"
#         )
#         serializer = ChecklistItemSubmissionSerializer(submissions, many=True)
#         return Response(serializer.data)
    

# from rest_framework import viewsets, permissions, status
# from rest_framework.response import Response
# from .models import ChecklistAccess, Checklist, ChecklistItem, ChecklistItemSubmission
# from .serializers import ChecklistAccessSerializer
# import requests
# class ChecklistAccessViewSet(viewsets.ModelViewSet):
#     queryset = ChecklistAccess.objects.all()
#     serializer_class = ChecklistAccessSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         access = serializer.instance

#         checklist = access.checklist
#         items = checklist.items.all()
#         purpose_id = checklist.purpose_id

#         # Fetch purpose type (e.g., SNAGGING, Q.C.)
#         purpose_type = None
#         try:
#             resp = requests.get(f"http://0.0.0.0:8001/api/purposes/{purpose_id}")
#             resp.raise_for_status()
#             data = resp.json()
#             purpose_type = (data.get("type") or "").upper()
#         except Exception as e:
#             print(f"[ChecklistAccessViewSet] Could not fetch purpose: {e}")

#         roles = access.roles or {}
#         maker_id = roles.get('maker')
#         checker_id = roles.get('checker')
#         supervisor_id = roles.get('supervisor')

#         created_subs = []
#         for item in items:
#             if purpose_type == "SNAGGING" and checker_id:
#                 # Create ONLY for checker
#                 obj, created = ChecklistItemSubmission.objects.get_or_create(
#                     checklist_item=item,
#                     checked_by_id=checker_id,
#                     defaults={"status": "SUBMITTED"}  # So checker sees it immediately
#                 )
#                 created_subs.append(obj.id)
#             elif purpose_type == "Q.C.":
#                 # Only for maker (typical QC)
#                 if maker_id:
#                     obj, created = ChecklistItemSubmission.objects.get_or_create(
#                         checklist_item=item,
#                         user=maker_id,
#                         defaults={"status": "IN_PROGRESS"}
#                     )
#                     created_subs.append(obj.id)
#                 # If you want supervisor to get a submission at this point for Q.C., keep this block.
#                 # If NOT, comment or remove below:
#                 # elif supervisor_id:
#                 #     obj, created = ChecklistItemSubmission.objects.get_or_create(
#                 #         checklist_item=item,
#                 #         inspected_by_id=supervisor_id,
#                 #         defaults={"status": "IN_PROGRESS"}
#                 #     )
#                 #     created_subs.append(obj.id)

#         print(f"[ChecklistAccessViewSet] Auto-created {len(created_subs)} submissions.")
#         headers = self.get_success_headers(serializer.data)
#         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
