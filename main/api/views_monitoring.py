from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.serializers import *

# === Vues Monitoring === #


class ListClientView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        client_list = Client.objects.filter(nom__icontains=search_term).order_by("nom")

        paginator = Paginator(client_list, 10)
        client_page = paginator.get_page(page_number)
        serializer = ClientSerializer(client_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": client_page.has_next(),
                "previous": client_page.has_previous(),
            }
        )


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
            return Response(
                {"detail": "Client non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetClientSerializer(client)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        client = Client.objects.filter(id=id).first()
        if not client:
            return Response(
                {"detail": "Client non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

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
            return Response(
                {"detail": "Client non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CheckClientSerializer(client)
        return Response(serializer.data)


class DeleteClientView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        clients = Client.objects.filter(id__in=ids)
        if not clients.exists():
            return Response(
                {"error": "Aucun client trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = clients.delete()
        return Response(
            {"message": f"{count} clients supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class ListPortefeuilleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        portefeuille_list = Portefeuille.objects.filter(
            nom__icontains=search_term
        ).order_by("nom")

        paginator = Paginator(portefeuille_list, 10)
        portefeuille_page = paginator.get_page(page_number)
        serializer = PortefeuilleSerializer(portefeuille_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": portefeuille_page.has_next(),
                "previous": portefeuille_page.has_previous(),
            }
        )


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
            portefeuille_data = request.data.get("portefeuille")
            portefeuille_serializer = AddPortefeuilleSerializer(data=portefeuille_data)

            if portefeuille_serializer.is_valid():
                portefeuille = portefeuille_serializer.save()

                clients_data = request.data.get("clients", [])
                for client_data in clients_data:
                    client_data["portefeuille"] = portefeuille.id
                    client_serializer = AddPortefeuilleClientSerializer(
                        data=client_data
                    )
                    if not client_serializer.is_valid():
                        transaction.set_rollback(True)
                        return Response(
                            client_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                        )
                    client_serializer.save()

                return Response(
                    portefeuille_serializer.data, status=status.HTTP_201_CREATED
                )

            return Response(
                portefeuille_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


class AddPortefeuilleWithAcheteursView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            # Extraire les données de la requête
            portefeuille_data = {
                "client": request.data.get("client"),
                "nom": request.data.get("nom"),
                "frequence_alertes": request.data.get("frequence_alertes"),
                "elements_surveillance_actifs": request.data.get(
                    "elements_surveillance_actifs", []
                ),
                "acheteurs": request.data.get("acheteurs", []),
            }

            # Valider et enregistrer les données
            portefeuille_serializer = AddPortefeuilleWithAcheteursSerializer(
                data=portefeuille_data
            )
            if portefeuille_serializer.is_valid():
                portefeuille_serializer.save()
                return Response(
                    portefeuille_serializer.data, status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    portefeuille_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )


class EditPortefeuilleView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id, *args, **kwargs):
        with transaction.atomic():
            portefeuille = Portefeuille.objects.filter(id=id).first()
            if not portefeuille:
                return Response(
                    {"detail": "Portefeuille non trouvé."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            portefeuille_data = {
                "client": request.data.get("client"),
                "nom": request.data.get("nom"),
                "frequence_alertes": request.data.get("frequence_alertes"),
                "elements_surveillance_actifs": request.data.get(
                    "elements_surveillance_actifs", []
                ),
                "acheteurs": request.data.get("acheteurs", []),
            }

            portefeuille_serializer = EditPortefeuilleSerializer(
                portefeuille, data=portefeuille_data, partial=True
            )
            if portefeuille_serializer.is_valid():
                portefeuille = portefeuille_serializer.save()

                # Supprimer les anciennes liaisons
                PortefeuilleClient.objects.filter(portefeuille=portefeuille).delete()

                # Ajouter les nouvelles liaisons
                acheteurs_ids = request.data.get("acheteurs", [])
                for acheteur_id in acheteurs_ids:
                    PortefeuilleClient.objects.create(
                        portefeuille=portefeuille, acheteur_id=acheteur_id
                    )

                return Response(portefeuille_serializer.data)

            return Response(
                portefeuille_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


class EditPortefeuilleWithClientsView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id, *args, **kwargs):
        with transaction.atomic():
            portefeuille = Portefeuille.objects.filter(id=id).first()
            if not portefeuille:
                return Response(
                    {"detail": "Portefeuille non trouvé."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            portefeuille_data = request.data.get("portefeuille")
            portefeuille_serializer = EditPortefeuilleSerializer(
                portefeuille, data=portefeuille_data, partial=True
            )

            if portefeuille_serializer.is_valid():
                portefeuille = portefeuille_serializer.save()

                # Supprimer les anciennes liaisons
                PortefeuilleClient.objects.filter(portefeuille=portefeuille).delete()

                # Ajouter les nouvelles liaisons
                clients_data = request.data.get("clients", [])
                for client_data in clients_data:
                    client_data["portefeuille"] = portefeuille.id
                    client_serializer = AddPortefeuilleClientSerializer(
                        data=client_data
                    )
                    if not client_serializer.is_valid():
                        transaction.set_rollback(True)
                        return Response(
                            client_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                        )
                    client_serializer.save()

                return Response(portefeuille_serializer.data)

            return Response(
                portefeuille_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


class GetPortefeuilleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        portefeuille = Portefeuille.objects.filter(id=id).first()
        if not portefeuille:
            return Response(
                {"detail": "Portefeuille non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CheckPortefeuilleSerializer(portefeuille)
        return Response(serializer.data)


class GetPortefeuilleWithClientsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        portefeuille = Portefeuille.objects.filter(id=id).first()
        if not portefeuille:
            return Response(
                {"detail": "Portefeuille non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        # Récupérer les liaisons associées au portefeuille
        portefeuille_clients = PortefeuilleClient.objects.filter(
            portefeuille=portefeuille
        )

        # Sérialiser les données du portefeuille et des liaisons
        portefeuille_serializer = CheckPortefeuilleSerializer(portefeuille)
        portefeuille_clients_serializer = PortefeuilleClientSerializer(
            portefeuille_clients, many=True
        )

        # Combiner les données dans une seule réponse
        response_data = portefeuille_serializer.data
        response_data["portefeuille_clients"] = portefeuille_clients_serializer.data

        return Response(response_data)


class DeletePortefeuilleView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        portefeuilles = Portefeuille.objects.filter(id__in=ids)
        if not portefeuilles.exists():
            return Response(
                {"error": "Aucun portefeuille trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = portefeuilles.delete()
        return Response(
            {"message": f"{count} portefeuilles supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class ListPortefeuilleClientView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        portefeuille_client_list = PortefeuilleClient.objects.filter(
            acheteur__nom__icontains=search_term
        ).order_by("acheteur__nom")

        paginator = Paginator(portefeuille_client_list, 10)
        portefeuille_client_page = paginator.get_page(page_number)
        serializer = PortefeuilleClientSerializer(portefeuille_client_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": portefeuille_client_page.has_next(),
                "previous": portefeuille_client_page.has_previous(),
            }
        )


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
            return Response(
                {"detail": "Portefeuille client non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetPortefeuilleClientSerializer(portefeuille_client)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        portefeuille_client = PortefeuilleClient.objects.filter(id=id).first()
        if not portefeuille_client:
            return Response(
                {"detail": "Portefeuille client non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AddPortefeuilleClientSerializer(
            portefeuille_client, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetPortefeuilleClientView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        portefeuille_client = PortefeuilleClient.objects.filter(id=id).first()
        if not portefeuille_client:
            return Response(
                {"detail": "Portefeuille client non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CheckPortefeuilleClientSerializer(portefeuille_client)
        return Response(serializer.data)


class DeletePortefeuilleClientView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        portefeuille_clients = PortefeuilleClient.objects.filter(id__in=ids)
        if not portefeuille_clients.exists():
            return Response(
                {"error": "Aucun portefeuille client trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = portefeuille_clients.delete()
        return Response(
            {"message": f"{count} portefeuilles clients supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class ListContactView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        contact_list = Contact.objects.filter(nom__icontains=search_term).order_by(
            "nom"
        )

        paginator = Paginator(contact_list, 10)
        contact_page = paginator.get_page(page_number)
        serializer = ContactSerializer(contact_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": contact_page.has_next(),
                "previous": contact_page.has_previous(),
            }
        )


class AddContactView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditContactView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        contact = Contact.objects.filter(id=id).first()
        if not contact:
            return Response(
                {"detail": "Contact non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetContactSerializer(contact)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        contact = Contact.objects.filter(id=id).first()
        if not contact:
            return Response(
                {"detail": "Contact non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditContactSerializer(contact, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetContactView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        contact = Contact.objects.filter(id=id).first()
        if not contact:
            return Response(
                {"detail": "Contact non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CheckContactSerializer(contact)
        return Response(serializer.data)


class DeleteContactView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contacts = Contact.objects.filter(id__in=ids)
        if not contacts.exists():
            return Response(
                {"error": "Aucun contact trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = contacts.delete()
        return Response(
            {"message": f"{count} contacts supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
