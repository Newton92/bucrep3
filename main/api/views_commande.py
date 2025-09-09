from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.functions import TruncMonth
from django.db.models import Count

from main.serializers import *

# === Vues Commande === #

class CommandesParMois(APIView):
    def get(self, request):
        # Annoter les Commandes par mois et compter le nombre total par mois
        commandes_par_mois = Commande.objects.annotate(
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
            'labels': [mois_en_francais[entry['mois'].strftime('%B')] for entry in commandes_par_mois],
            'data': [entry['total'] for entry in commandes_par_mois]
        }
        return Response(data)






class ListCommandeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Utilise 'search_query' ou 'search_term' en fonction de ce qui est présent
        search_query = request.query_params.get("search", "")
        if not search_query:
            search_query = request.query_params.get("search_term", "")
            
        page_number = request.query_params.get("page", 1)

        # Création du queryset initial
        queryset = Commande.objects.all()

        # AJOUT : Récupère l'ID du pays depuis la session ou le profil utilisateur
        # Logique pour déterminer le pays sélectionné
        selected_pays_id = request.session.get('selected_pays_id')
        if not selected_pays_id and hasattr(request.user, 'pays') and request.user.pays:
            selected_pays_id = request.user.pays.id

        # Applique le filtre si un pays est sélectionné
        if selected_pays_id:
            queryset = queryset.filter(pays_id=selected_pays_id)

        # Filtrage conditionnel par terme de recherche
        if search_query:
            queryset = queryset.filter(
                Q(notre_ref__icontains=search_query)
                | Q(reference_client__icontains=search_query)
                | Q(raison_sociale__icontains=search_query)
                | Q(status__icontains=search_query)
                | Q(pays__nom__icontains=search_query)
                | Q(ville__nom__icontains=search_query)
            )

        # Tri du queryset
        queryset = queryset.order_by("-created_at")

        # Pagination manuelle du queryset
        paginator = Paginator(queryset, 10)
        
        try:
            commande_page = paginator.page(page_number)
        except Exception:
            return Response(
                {"detail": "Numéro de page invalide."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CommandeSerializer(commande_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": commande_page.has_next(),
                "previous": commande_page.has_previous(),
            }
        )






class SearchCommandeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        commande_list = Commande.objects.filter(
            Q(notre_ref__icontains=search_term)
            | Q(reference_client__icontains=search_term)
            | Q(raison_sociale__icontains=search_term)
            | Q(status__icontains=search_term)
            | Q(pays__nom__icontains=search_term)
            | Q(ville__nom__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(commande_list, 10)  # 10 éléments par page
        page_number = request.query_params.get("page", 1)
        commande_page = paginator.get_page(page_number)
        serializer = CommandeSerializer(commande_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": commande_page.has_next(),
                "previous": commande_page.has_previous(),
            }
        )






class ListCommandeViewOld(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get("search", "")
        page_number = request.query_params.get("page", 1)

        commande_list = Commande.objects.filter(
            Q(notre_ref__icontains=search_query)
            | Q(reference_client__icontains=search_query)
            | Q(raison_sociale__icontains=search_query)
            | Q(status__icontains=search_query)
            | Q(pays__nom__icontains=search_query)
            | Q(ville__nom__icontains=search_query)
        ).order_by("-created_at")

        paginator = Paginator(commande_list, 10)  # 10 éléments par page
        commande_page = paginator.get_page(page_number)
        serializer = CommandeSerializer(commande_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": commande_page.has_next(),
                "previous": commande_page.has_previous(),
            }
        )





class SearchCommandeViewOld(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        commande_list = Commande.objects.filter(
            Q(notre_ref__icontains=search_term)
            | Q(reference_client__icontains=search_term)
            | Q(raison_sociale__icontains=search_term)
            | Q(status__icontains=search_term)
            | Q(pays__nom__icontains=search_term)
            | Q(ville__nom__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(commande_list, 10)  # 10 éléments par page
        page_number = request.query_params.get("page", 1)
        commande_page = paginator.get_page(page_number)
        serializer = CommandeSerializer(commande_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": commande_page.has_next(),
                "previous": commande_page.has_previous(),
            }
        )





class ListCommandeViewOld1(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Récupérer le pays sélectionné depuis la requête ou utiliser celui de l'utilisateur
        selected_pays_id = request.query_params.get('pays_id', request.session.get('selected_pays_id', request.user.pays.id))

        # Filtrer par pays
        commande_list = Commande.objects.filter(pays_id=selected_pays_id)  # Utilisez 'pays' en minuscules

        # Appliquer la recherche si un terme est fourni
        search_query = request.query_params.get("search", "")
        if search_query:
            commande_list = commande_list.filter(
                Q(notre_ref__icontains=search_query)
                | Q(reference_client__icontains=search_query)
                | Q(raaison_sociale__icontains=search_query)
                | Q(status__icontains=search_query)
                | Q(pays__nom__icontains=search_query)  # Utilisez 'pays' en minuscules
                | Q(ville__nom__icontains=search_query)
            )

        # Tri et pagination
        commande_list = commande_list.order_by("-created_at")
        paginator = Paginator(commande_list, 10)  # 10 éléments par page
        page_number = request.query_params.get("page", 1)
        commande_page = paginator.get_page(page_number)

        # Sérialisation et réponse
        serializer = CommandeSerializer(commande_page, many=True)
        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": commande_page.has_next(),
                "previous": commande_page.has_previous(),
            }
        )




class SearchCommandeViewOld1(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Récupérer le pays sélectionné
        selected_pays_id = request.session.get('selected_pays_id', request.user.pays.id)

        # Filtrer par pays et appliquer la recherche
        commande_list = Commande.objects.filter(pays_id=selected_pays_id).filter(
            Q(notre_ref__icontains=search_term)
            | Q(reference_client__icontains=search_term)
            | Q(raison_sociale__icontains=search_term)
            | Q(status__icontains=search_term)
            | Q(pays__nom__icontains=search_term)
            | Q(ville__nom__icontains=search_term)
        ).order_by("-created_at")

        # Pagination
        paginator = Paginator(commande_list, 10)  # 10 éléments par page
        page_number = request.query_params.get("page", 1)
        commande_page = paginator.get_page(page_number)

        # Sérialisation et réponse
        serializer = CommandeSerializer(commande_page, many=True)
        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": commande_page.has_next(),
                "previous": commande_page.has_previous(),
            }
        )






class AddCommandeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddCommandeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditCommandeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        commande = Commande.objects.filter(id=id).first()
        if not commande:
            return Response(
                {"detail": "Commande non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetCommandeSerializer(commande)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        commande = Commande.objects.filter(id=id).first()
        if not commande:
            return Response(
                {"detail": "Commande non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditCommandeSerializer(commande, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteCommandeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        commandes = Commande.objects.filter(id__in=ids)
        if not commandes.exists():
            return Response(
                {"error": "Aucune commande trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = commandes.delete()
        return Response(
            {"message": f"{count} commandes supprimées avec succès."},
            status=status.HTTP_200_OK,
        )


class GetCommandeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        commande = Commande.objects.filter(id=id).first()
        if not commande:
            return Response(
                {"detail": "Commande non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CheckCommandeSerializer(commande)
        return Response(serializer.data)




class CommandeDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, commande_id, *args, **kwargs):
        try:
            # Vérifier que l'ID est un nombre valide
            if not str(commande_id).isdigit():
                return Response({
                    'success': False,
                    'message': 'ID de commande invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            commande = Commande.objects.get(pk=commande_id)
            serializer = CommandesSerializer(commande)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Commande.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Commande #{commande_id} non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur lors de la récupération de la commande: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)