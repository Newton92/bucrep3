from django.shortcuts import render
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from main.models import CustomUser
from main.serializers import *
import random
import string
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from django.contrib.auth.decorators import login_required
from main.utils import send_email_with_secret_code
from django.template.loader import render_to_string
from rest_framework import status
from django.contrib.auth import logout
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django.urls import reverse
from django.contrib.auth import login
from rest_framework.viewsets import ModelViewSet
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


# === Vues Monitoring === #



class ListClientView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        client_list = Client.objects.filter(
            nom__icontains=search_term
        ).order_by('nom')

        paginator = Paginator(client_list, 10)
        client_page = paginator.get_page(page_number)
        serializer = ClientSerializer(client_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': client_page.has_next(),
            'previous': client_page.has_previous()
        })



class AddClientView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddClientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class EditClientView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        client = Client.objects.filter(id=id).first()
        if not client:
            return Response({'detail': 'Client non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetClientSerializer(client)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        client = Client.objects.filter(id=id).first()
        if not client:
            return Response({'detail': 'Client non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditClientSerializer(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class GetClientView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        client = Client.objects.filter(id=id).first()
        if not client:
            return Response({'detail': 'Client non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CheckClientSerializer(client)
        return Response(serializer.data)




class DeleteClientView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        clients = Client.objects.filter(id__in=ids)
        if not clients.exists():
            return Response({'error': 'Aucun client trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = clients.delete()
        return Response({'message': f'{count} clients supprimés avec succès.'}, status=status.HTTP_200_OK)










class ListPortefeuilleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        portefeuille_list = Portefeuille.objects.filter(
            nom__icontains=search_term
        ).order_by('nom')

        paginator = Paginator(portefeuille_list, 10)
        portefeuille_page = paginator.get_page(page_number)
        serializer = PortefeuilleSerializer(portefeuille_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': portefeuille_page.has_next(),
            'previous': portefeuille_page.has_previous()
        })


class AddPortefeuilleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddPortefeuilleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
class AddPortefeuilleWithClientsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            portefeuille_data = request.data.get('portefeuille')
            portefeuille_serializer = AddPortefeuilleSerializer(data=portefeuille_data)

            if portefeuille_serializer.is_valid():
                portefeuille = portefeuille_serializer.save()

                clients_data = request.data.get('clients', [])
                for client_data in clients_data:
                    client_data['portefeuille'] = portefeuille.id
                    client_serializer = AddPortefeuilleClientSerializer(data=client_data)
                    if not client_serializer.is_valid():
                        transaction.set_rollback(True)
                        return Response(client_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    client_serializer.save()

                return Response(portefeuille_serializer.data, status=status.HTTP_201_CREATED)

            return Response(portefeuille_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
              
        
class AddPortefeuilleWithAcheteursView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            # Extraire les données de la requête
            portefeuille_data = {
                'client': request.data.get('client'),
                'nom': request.data.get('nom'),
                'acheteurs': request.data.get('acheteurs', [])
            }

            # Valider et enregistrer les données
            portefeuille_serializer = AddPortefeuilleWithAcheteursSerializer(data=portefeuille_data)
            if portefeuille_serializer.is_valid():
                portefeuille = portefeuille_serializer.save()
                return Response(portefeuille_serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(portefeuille_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


class EditPortefeuilleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        # Récupérer le portefeuille
        portefeuille = Portefeuille.objects.filter(id=id).first()
        if not portefeuille:
            return Response({'detail': 'Portefeuille non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        # Sérialiser les données du portefeuille
        serializer = GetPortefeuilleSerializer(portefeuille)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        # Récupérer le portefeuille
        portefeuille = Portefeuille.objects.filter(id=id).first()
        if not portefeuille:
            return Response({'detail': 'Portefeuille non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        # Mettre à jour les données du portefeuille
        serializer = EditPortefeuilleSerializer(portefeuille, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Mettre à jour les acheteurs associés
            acheteurs_ids = request.data.get('acheteurs', [])
            if acheteurs_ids:
                # Supprimer les anciennes associations
                PortefeuilleClient.objects.filter(portefeuille=portefeuille).delete()
                # Ajouter les nouvelles associations
                for acheteur_id in acheteurs_ids:
                    PortefeuilleClient.objects.create(portefeuille=portefeuille, acheteur_id=acheteur_id)

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

class EditPortefeuilleWithClientsView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id, *args, **kwargs):
        with transaction.atomic():
            portefeuille = Portefeuille.objects.filter(id=id).first()
            if not portefeuille:
                return Response({'detail': 'Portefeuille non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

            portefeuille_data = request.data.get('portefeuille')
            portefeuille_serializer = EditPortefeuilleSerializer(portefeuille, data=portefeuille_data, partial=True)

            if portefeuille_serializer.is_valid():
                portefeuille = portefeuille_serializer.save()

                # Supprimer les anciennes liaisons
                PortefeuilleClient.objects.filter(portefeuille=portefeuille).delete()

                # Ajouter les nouvelles liaisons
                clients_data = request.data.get('clients', [])
                for client_data in clients_data:
                    client_data['portefeuille'] = portefeuille.id
                    client_serializer = AddPortefeuilleClientSerializer(data=client_data)
                    if not client_serializer.is_valid():
                        transaction.set_rollback(True)
                        return Response(client_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    client_serializer.save()

                return Response(portefeuille_serializer.data)

            return Response(portefeuille_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class GetPortefeuilleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        portefeuille = Portefeuille.objects.filter(id=id).first()
        if not portefeuille:
            return Response({'detail': 'Portefeuille non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CheckPortefeuilleSerializer(portefeuille)
        return Response(serializer.data)
    
      

class GetPortefeuilleWithClientsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        portefeuille = Portefeuille.objects.filter(id=id).first()
        if not portefeuille:
            return Response({'detail': 'Portefeuille non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        # Récupérer les liaisons associées au portefeuille
        portefeuille_clients = PortefeuilleClient.objects.filter(portefeuille=portefeuille)

        # Sérialiser les données du portefeuille et des liaisons
        portefeuille_serializer = CheckPortefeuilleSerializer(portefeuille)
        portefeuille_clients_serializer = PortefeuilleClientSerializer(portefeuille_clients, many=True)

        # Combiner les données dans une seule réponse
        response_data = portefeuille_serializer.data
        response_data['portefeuille_clients'] = portefeuille_clients_serializer.data

        return Response(response_data)


class DeletePortefeuilleView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        portefeuilles = Portefeuille.objects.filter(id__in=ids)
        if not portefeuilles.exists():
            return Response({'error': 'Aucun portefeuille trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = portefeuilles.delete()
        return Response({'message': f'{count} portefeuilles supprimés avec succès.'}, status=status.HTTP_200_OK)











class ListPortefeuilleClientView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        portefeuille_client_list = PortefeuilleClient.objects.filter(
            acheteur__nom__icontains=search_term
        ).order_by('acheteur__nom')

        paginator = Paginator(portefeuille_client_list, 10)
        portefeuille_client_page = paginator.get_page(page_number)
        serializer = PortefeuilleClientSerializer(portefeuille_client_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': portefeuille_client_page.has_next(),
            'previous': portefeuille_client_page.has_previous()
        })


class AddPortefeuilleClientView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddPortefeuilleClientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditPortefeuilleClientView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        portefeuille_client = PortefeuilleClient.objects.filter(id=id).first()
        if not portefeuille_client:
            return Response({'detail': 'Portefeuille client non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetPortefeuilleClientSerializer(portefeuille_client)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        portefeuille_client = PortefeuilleClient.objects.filter(id=id).first()
        if not portefeuille_client:
            return Response({'detail': 'Portefeuille client non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AddPortefeuilleClientSerializer(portefeuille_client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetPortefeuilleClientView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        portefeuille_client = PortefeuilleClient.objects.filter(id=id).first()
        if not portefeuille_client:
            return Response({'detail': 'Portefeuille client non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CheckPortefeuilleClientSerializer(portefeuille_client)
        return Response(serializer.data)


class DeletePortefeuilleClientView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        portefeuille_clients = PortefeuilleClient.objects.filter(id__in=ids)
        if not portefeuille_clients.exists():
            return Response({'error': 'Aucun portefeuille client trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = portefeuille_clients.delete()
        return Response({'message': f'{count} portefeuilles clients supprimés avec succès.'}, status=status.HTTP_200_OK)


