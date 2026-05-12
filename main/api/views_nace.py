"""API views for cascading NACE code selection (Activity → Type → Code)."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from main.models import NaceSpecifique


class NaceActivitiesAPIView(APIView):
    """GET /api/nace/activities/ — list of distinct activities."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        activities = (
            NaceSpecifique.objects
            .filter(active=True)
            .values_list("activity", flat=True)
            .distinct()
            .order_by("activity")
        )
        return Response({"activities": list(activities)})


class NaceTypesAPIView(APIView):
    """GET /api/nace/types/?activity=... — types for a given activity."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        activity = request.query_params.get("activity", "").strip()
        if not activity:
            return Response({"types": []})

        types = (
            NaceSpecifique.objects
            .filter(active=True, activity=activity)
            .values_list("type", flat=True)
            .distinct()
            .order_by("type")
        )
        return Response({"types": list(types)})


class NaceCodesAPIView(APIView):
    """GET /api/nace/codes/?activity=...&type=... — codes for activity+type."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        activity = request.query_params.get("activity", "").strip()
        nace_type = request.query_params.get("type", "").strip()

        if not activity or not nace_type:
            return Response({"codes": []})

        qs = NaceSpecifique.objects.filter(
            active=True,
            activity=activity,
            type=nace_type,
        ).order_by("code")

        codes = [
            {
                "id": obj.id,
                "code": obj.code,
                "denomination": obj.denomination,
                "label": f"{obj.code} — {obj.denomination}",
            }
            for obj in qs
        ]
        return Response({"codes": codes})
