import bleach
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.functions import TruncMonth
from django.db.models import Count

from main.models import Alerte, Client
from main.serializers import *

# === Vues Warning === #
class AlertesParMois(APIView):
    def get(self, request):
        # Annoter les alertes par mois et compter le nombre total par mois
        alertes_par_mois = Alerte.objects.annotate(
            mois=TruncMonth('created_at')
        ).values('mois').annotate(
            total=Count('id')
        ).order_by('mois')

        # Dictionnaire pour mapper les noms des mois en français
        mois_en_francais = {
            'January': 'Janvier',
            'February': 'Février',
            'March': 'Mars',
            'April': 'Avril',
            'May': 'Mai',
            'June': 'Juin',
            'July': 'Juillet',
            'August': 'Août',
            'September': 'Septembre',
            'October': 'Octobre',
            'November': 'Novembre',
            'December': 'Décembre'
        }

        # Préparer les données pour le graphique
        data = {
            'labels': [mois_en_francais[entry['mois'].strftime('%B')] for entry in alertes_par_mois],
            'data': [entry['total'] for entry in alertes_par_mois]
        }
        return Response(data)



class ListAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get("search", "")
        page_number = request.query_params.get("page", 1)

        alerte_list = Alerte.objects.filter(
            Q(reference__icontains=search_query)
            | Q(objet__icontains=search_query)
            | Q(content__icontains=search_query)
        ).order_by("-created_at")

        paginator = Paginator(alerte_list, 10)
        alerte_page = paginator.get_page(page_number)
        serializer = AlerteSerializer(alerte_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": alerte_page.has_next(),
                "previous": alerte_page.has_previous(),
            }
        )


class SearchAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alerte_list = Alerte.objects.filter(
            Q(reference__icontains=search_term)
            | Q(objet__icontains=search_term)
            | Q(content__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(alerte_list, 10)
        page_number = request.query_params.get("page", 1)
        alerte_page = paginator.get_page(page_number)
        serializer = AlerteSerializer(alerte_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": alerte_page.has_next(),
                "previous": alerte_page.has_previous(),
            }
        )


class AddAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddAlerteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        alerte = Alerte.objects.filter(id=id).first()
        if not alerte:
            return Response(
                {"detail": "Alerte non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = AlerteSerializer(alerte)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        alerte = Alerte.objects.filter(id=id).first()
        if not alerte:
            return Response(
                {"detail": "Alerte non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditAlerteSerializer(alerte, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alertes = Alerte.objects.filter(id__in=ids)
        if not alertes.exists():
            return Response(
                {"error": "Aucune alerte trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = alertes.delete()
        return Response(
            {"message": f"{count} alertes supprimées avec succès."},
            status=status.HTTP_200_OK,
        )


class GetAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        alerte = Alerte.objects.filter(id=id).first()
        if not alerte:
            return Response(
                {"detail": "Alerte non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = AlerteSerializer(alerte)
        return Response(serializer.data)


class ListDocumentAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get("search", "")
        page_number = request.query_params.get("page", 1)

        document_list = DocumentAlerte.objects.filter(
            Q(titre__icontains=search_query)
            | Q(alerte__reference__icontains=search_query)
        ).order_by("-created_at")

        paginator = Paginator(document_list, 10)
        document_page = paginator.get_page(page_number)
        serializer = DocumentAlerteSerializer(document_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": document_page.has_next(),
                "previous": document_page.has_previous(),
            }
        )


class AddDocumentAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddDocumentAlerteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditDocumentAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        document = DocumentAlerte.objects.filter(id=id).first()
        if not document:
            return Response(
                {"detail": "Document non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = DocumentAlerteSerializer(document)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        document = DocumentAlerte.objects.filter(id=id).first()
        if not document:
            return Response(
                {"detail": "Document non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditDocumentAlerteSerializer(
            document, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteDocumentAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        documents = DocumentAlerte.objects.filter(id__in=ids)
        if not documents.exists():
            return Response(
                {"error": "Aucun document trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = documents.delete()
        return Response(
            {"message": f"{count} documents supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class GetDocumentAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        document = DocumentAlerte.objects.filter(id=id).first()
        if not document:
            return Response(
                {"detail": "Document non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = DocumentAlerteSerializer(document)
        return Response(serializer.data)


class EnvoyerWarningView2(APIView):
    def post(self, request, *args, **kwargs):
        alerte_reference = request.data.get("alerte_reference")
        client_ids = request.data.get("client_ids", [])

        if not alerte_reference or not client_ids:
            return Response(
                {
                    "error": "La référence de l'alerte et les IDs des clients sont requis."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        alerte = get_object_or_404(Alerte, reference=alerte_reference)
        clients = Client.objects.filter(id__in=client_ids)

        for client in clients:
            subject = f"Warning: {alerte.objet}"
            recipient_list = [client.email]
            context = {
                "client": client,
                "alerte": alerte,
                "content": self.clean_html_content(alerte.content),
            }
            self.send_email(
                subject, recipient_list, "main/emails/email_warning.html", context
            )

        return Response(
            {"message": "Le warning a été envoyé avec succès."},
            status=status.HTTP_200_OK,
        )

    def clean_html_content(self, content):
        # Liste des balises autorisées
        allowed_tags = ["p", "strong", "em", "a", "ul", "ol", "li", "br"]
        # Nettoyer le contenu HTML
        cleaned_content = bleach.clean(content, tags=allowed_tags, strip=True)
        return cleaned_content

    def send_email(self, subject, recipient_list, template_name, context):
        """Envoie un email HTML avec un sujet et un contenu donné."""
        html_message = render_to_string(template_name, context)
        from_email = "bucrepcontact@gmail.com"
        send_mail(
            subject,
            "",  # Corps texte vide (on utilise HTML)
            from_email,
            recipient_list,
            fail_silently=False,
            html_message=html_message,
        )


class EnvoyerWarningView(APIView):
    def post(self, request, *args, **kwargs):
        alerte_reference = request.data.get("alerte_reference")
        client_ids = request.data.get("client_ids", [])

        if not alerte_reference or not client_ids:
            return Response(
                {
                    "error": "La référence de l'alerte et les IDs des clients sont requis."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        alerte = get_object_or_404(Alerte, reference=alerte_reference)
        clients = Client.objects.filter(id__in=client_ids)

        for client in clients:
            # Envoyer l'email au client
            subject = f"Warning: {alerte.objet}"
            recipient_list = [client.email]
            context = {
                "client": client,
                "alerte": alerte,
                "content": self.clean_html_content(alerte.content),
            }
            self.send_email(
                subject, recipient_list, "main/emails/email_warning.html", context
            )

            # Récupérer et envoyer l'email aux contacts actifs associés au client
            contacts_actifs = Contact.objects.filter(client=client, actif=True)
            for contact in contacts_actifs:
                recipient_list = [contact.email]
                self.send_email(
                    subject, recipient_list, "main/emails/email_warning.html", context
                )

        return Response(
            {"message": "Le warning a été envoyé avec succès."},
            status=status.HTTP_200_OK,
        )

    def clean_html_content(self, content):
        # Liste des balises autorisées
        allowed_tags = ["p", "strong", "em", "a", "ul", "ol", "li", "br"]
        # Nettoyer le contenu HTML
        cleaned_content = bleach.clean(content, tags=allowed_tags, strip=True)
        return cleaned_content

    def send_email(self, subject, recipient_list, template_name, context):
        """Envoie un email HTML avec un sujet et un contenu donné."""
        html_message = render_to_string(template_name, context)
        from_email = "bucrepcontact@gmail.com"
        send_mail(
            subject,
            "",  # Corps texte vide (on utilise HTML)
            from_email,
            recipient_list,
            fail_silently=False,
            html_message=html_message,
        )
