# dans votre fichier views.py

from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import *
from main.models import Liabilities  # Importer le modèle Liabilities
from main.models import Assets
from main.serializers import *
from main.serializers import AddAssetsSerializer  # Importer les serializers
from main.serializers import (AddLiabilitiesSerializer, AssetsSerializer,
                              EditAssetsSerializer, LiabilitiesSerializer)


class ListAssetsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        # Filtre les actifs par l'acheteur spécifié dans l'URL
        asset_list = Assets.objects.filter(acheteur_id=acheteur_id).order_by(
            "-annee__annee", "-semestre"
        )

        paginator = Paginator(asset_list, 10)  # 10 éléments par page
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)

        serializer = AssetsSerializer(page_obj, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
            },
            status=status.HTTP_200_OK,
        )


class AddMultiYearAssetsView(APIView):
    """Vue pour gérer la soumission du formulaire multi-années."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        created_assets = []
        errors = {}

        # Boucle sur les 3 années possibles
        for suffix in ["n", "n1", "n2"]:
            # Vérifie si des données pour cette année ont été envoyées
            if f"type_bilan_{suffix}" in data:
                asset_data = {}
                # Récupère tous les champs pour le suffixe courant
                for key, value in data.items():
                    if key.endswith(f"_{suffix}"):
                        base_key = key.rsplit("_", 1)[0]
                        asset_data[base_key] = value

                # Vérifier si l'acheteur est présent et non vide
                if not asset_data.get("acheteur"):
                    continue  # Ignore cette année si aucun acheteur n'est sélectionné

                serializer = AddAssetsSerializer(
                    data=asset_data, context={"request": request}
                )
                if serializer.is_valid():
                    instance = serializer.save()
                    created_assets.append(AssetsSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        if not created_assets:
            return Response(
                {"detail": "Aucune donnée valide à enregistrer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(created_assets, status=status.HTTP_201_CREATED)


class GetAssetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, asset_id, *args, **kwargs):
        try:
            asset = Assets.objects.get(id=asset_id)
            serializer = AssetsSerializer(asset)
            return Response(serializer.data)
        except Assets.DoesNotExist:
            return Response(
                {"detail": "Actif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )


class EditAssetView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, asset_id, *args, **kwargs):
        try:
            asset = Assets.objects.get(id=asset_id)
            serializer = EditAssetsSerializer(
                asset, data=request.data, partial=True, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Assets.DoesNotExist:
            return Response(
                {"detail": "Actif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )


class DeleteAssetsView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"error": "La liste des IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        count, _ = Assets.objects.filter(id__in=ids).delete()

        if count == 0:
            return Response(
                {"error": "Aucun actif trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"message": f"{count} actif(s) supprimé(s) avec succès."},
            status=status.HTTP_200_OK,
        )


class ListLiabilitiesView(APIView):
    """Vue pour lister les passifs d'un acheteur avec pagination."""

    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        # Filtre les passifs par l'acheteur spécifié dans l'URL
        liability_list = Liabilities.objects.filter(acheteur_id=acheteur_id).order_by(
            "-annee__annee", "-semestre"
        )

        paginator = Paginator(liability_list, 10)  # 10 éléments par page
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)

        serializer = LiabilitiesSerializer(page_obj, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
            },
            status=status.HTTP_200_OK,
        )


class AddMultiYearLiabilitiesView(APIView):
    """Vue pour gérer l'ajout de passifs sur plusieurs années via un seul formulaire."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        created_liabilities = []
        errors = {}

        # Boucle sur les 3 années possibles (n, n1, n2)
        for suffix in ["n", "n1", "n2"]:
            # Vérifie si des données pour cette année ont été envoyées
            if f"type_bilan_{suffix}" in data:
                liability_data = {}
                # Récupère tous les champs pour le suffixe courant
                for key, value in data.items():
                    if key.endswith(f"_{suffix}"):
                        base_key = key.rsplit("_", 1)[0]
                        liability_data[base_key] = value

                # Ignore cette année si aucun acheteur n'est sélectionné
                if not liability_data.get("acheteur"):
                    continue

                serializer = AddLiabilitiesSerializer(
                    data=liability_data, context={"request": request}
                )
                if serializer.is_valid():
                    instance = serializer.save()
                    created_liabilities.append(LiabilitiesSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        if not created_liabilities:
            return Response(
                {"detail": "Aucune donnée valide à enregistrer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(created_liabilities, status=status.HTTP_201_CREATED)


class GetLiabilityView(APIView):
    """Vue pour récupérer les détails d'un passif spécifique."""

    permission_classes = [IsAuthenticated]

    def get(self, request, liability_id, *args, **kwargs):
        try:
            liability = Liabilities.objects.get(id=liability_id)
            serializer = LiabilitiesSerializer(liability)
            return Response(serializer.data)
        except Liabilities.DoesNotExist:
            return Response(
                {"detail": "Passif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )


class EditLiabilityView(APIView):
    """Vue pour modifier un passif existant."""

    permission_classes = [IsAuthenticated]

    def put(self, request, liability_id, *args, **kwargs):
        try:
            liability = Liabilities.objects.get(id=liability_id)
            # On utilise AddLiabilitiesSerializer qui contient la logique d'update
            serializer = AddLiabilitiesSerializer(
                liability, data=request.data, partial=True, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    LiabilitiesSerializer(liability).data
                )  # Retourne les données complètes
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Liabilities.DoesNotExist:
            return Response(
                {"detail": "Passif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )


class DeleteLiabilitiesView(APIView):
    """Vue pour supprimer un ou plusieurs passifs en bloc."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"error": "La liste des IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        count, _ = Liabilities.objects.filter(id__in=ids).delete()

        if count == 0:
            return Response(
                {"error": "Aucun passif trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"message": f"{count} passif(s) supprimé(s) avec succès."},
            status=status.HTTP_200_OK,
        )


# --- Vues pour la gestion des Dépenses (Expenses) ---


class ListExpensesView(APIView):
    """Vue pour lister les dépenses d'un acheteur avec pagination."""

    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        # Filtre les dépenses par l'acheteur spécifié dans l'URL
        expense_list = Expenses.objects.filter(acheteur_id=acheteur_id).order_by(
            "-annee__annee", "-semestre"
        )

        paginator = Paginator(expense_list, 10)  # 10 éléments par page
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)

        serializer = ExpensesSerializer(page_obj, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
            },
            status=status.HTTP_200_OK,
        )


class AddMultiYearExpensesView(APIView):
    """Vue pour gérer l'ajout de dépenses sur plusieurs années via un seul formulaire."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        created_expenses = []
        errors = {}

        # Boucle sur les 3 années possibles (n, n1, n2)
        for suffix in ["n", "n1", "n2"]:
            # Vérifie si des données pour cette année ont été envoyées
            if f"type_bilan_{suffix}" in data and data[f"type_bilan_{suffix}"]:
                expense_data = {}
                # Récupère tous les champs pour le suffixe courant
                for key, value in data.items():
                    if key.endswith(f"_{suffix}"):
                        base_key = key.rsplit("_", 1)[0]
                        expense_data[base_key] = value

                if not expense_data.get("acheteur"):
                    continue

                serializer = AddExpensesSerializer(
                    data=expense_data, context={"request": request}
                )
                if serializer.is_valid():
                    instance = serializer.save()
                    created_expenses.append(ExpensesSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        if not created_expenses:
            return Response(
                {"detail": "Aucune donnée de dépense valide à enregistrer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(created_expenses, status=status.HTTP_201_CREATED)


class GetExpenseView(APIView):
    """Vue pour récupérer les détails d'une dépense spécifique."""

    permission_classes = [IsAuthenticated]

    def get(self, request, expense_id, *args, **kwargs):
        try:
            expense = Expenses.objects.get(id=expense_id)
            serializer = ExpensesSerializer(expense)
            return Response(serializer.data)
        except Expenses.DoesNotExist:
            return Response(
                {"detail": "Dépense non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )


class EditExpenseView(APIView):
    """Vue pour modifier une dépense existante."""

    permission_classes = [IsAuthenticated]

    def put(self, request, expense_id, *args, **kwargs):
        try:
            expense = Expenses.objects.get(id=expense_id)
            serializer = AddExpensesSerializer(
                expense, data=request.data, partial=True, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    ExpensesSerializer(expense).data
                )  # Retourne les données complètes
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Expenses.DoesNotExist:
            return Response(
                {"detail": "Dépense non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )


class DeleteExpensesView(APIView):
    """Vue pour supprimer une ou plusieurs dépenses en bloc."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"error": "La liste des IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        count, _ = Expenses.objects.filter(id__in=ids).delete()

        if count == 0:
            return Response(
                {"error": "Aucune dépense trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"message": f"{count} dépense(s) supprimée(s) avec succès."},
            status=status.HTTP_200_OK,
        )


# --- Vues pour la gestion des Produits (Products) ---


class ListProductsView(APIView):
    """Vue pour lister les produits d'un acheteur avec pagination."""

    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        product_list = Products.objects.filter(acheteur_id=acheteur_id).order_by(
            "-annee__annee", "-semestre"
        )

        paginator = Paginator(product_list, 10)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)

        serializer = ProductSerializer(page_obj, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
            },
            status=status.HTTP_200_OK,
        )


class AddMultiYearProductsView(APIView):
    """Vue pour gérer l'ajout de produits sur plusieurs années via un seul formulaire."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        created_products = []
        errors = {}

        for suffix in ["n", "n1", "n2"]:
            if f"type_bilan_{suffix}" in data and data[f"type_bilan_{suffix}"]:
                product_data = {}
                for key, value in data.items():
                    if key.endswith(f"_{suffix}"):
                        base_key = key.rsplit("_", 1)[0]
                        product_data[base_key] = value

                if not product_data.get("acheteur"):
                    continue

                serializer = AddProductSerializer(
                    data=product_data, context={"request": request}
                )
                if serializer.is_valid():
                    instance = serializer.save()
                    created_products.append(ProductSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        if not created_products:
            return Response(
                {"detail": "Aucune donnée de produit valide à enregistrer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(created_products, status=status.HTTP_201_CREATED)


class GetProductView(APIView):
    """Vue pour récupérer les détails d'un produit spécifique."""

    permission_classes = [IsAuthenticated]

    def get(self, request, product_id, *args, **kwargs):
        try:
            product = Products.objects.get(id=product_id)
            serializer = ProductSerializer(product)
            return Response(serializer.data)
        except Products.DoesNotExist:
            return Response(
                {"detail": "Produit non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )


class EditProductView(APIView):
    """Vue pour modifier un produit existant."""

    permission_classes = [IsAuthenticated]

    def put(self, request, product_id, *args, **kwargs):
        try:
            product = Products.objects.get(id=product_id)
            serializer = AddProductSerializer(
                product, data=request.data, partial=True, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(ProductSerializer(product).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Products.DoesNotExist:
            return Response(
                {"detail": "Produit non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )


class DeleteProductsView(APIView):
    """Vue pour supprimer un ou plusieurs produits en bloc."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"error": "La liste des IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        count, _ = Products.objects.filter(id__in=ids).delete()

        if count == 0:
            return Response(
                {"error": "Aucun produit trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"message": f"{count} produit(s) supprimé(s) avec succès."},
            status=status.HTTP_200_OK,
        )


# --- Vues pour la gestion du Hors Bilan (OffBalanceSheet) ---


class ListOffBalanceSheetsView(APIView):
    """Vue pour lister les hors bilans d'un acheteur avec pagination."""

    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        off_balance_sheet_list = OffBalanceSheet.objects.filter(
            acheteur_id=acheteur_id
        ).order_by("-annee__annee", "-semestre")

        paginator = Paginator(off_balance_sheet_list, 10)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)

        serializer = OffBalanceSheetSerializer(page_obj, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
            },
            status=status.HTTP_200_OK,
        )


class AddMultiYearOffBalanceSheetsView(APIView):
    """Vue pour gérer l'ajout de hors bilans sur plusieurs années."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        created_items = []
        errors = {}

        for suffix in ["n", "n1", "n2"]:
            if f"type_bilan_{suffix}" in data and data[f"type_bilan_{suffix}"]:
                item_data = {}
                for key, value in data.items():
                    if key.endswith(f"_{suffix}"):
                        base_key = key.rsplit("_", 1)[0]
                        item_data[base_key] = value

                if not item_data.get("acheteur"):
                    continue

                serializer = AddOffBalanceSheetSerializer(
                    data=item_data, context={"request": request}
                )
                if serializer.is_valid():
                    instance = serializer.save(created_by=request.user)
                    created_items.append(OffBalanceSheetSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        if not created_items:
            return Response(
                {"detail": "Aucune donnée de hors bilan valide à enregistrer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(created_items, status=status.HTTP_201_CREATED)


class GetOffBalanceSheetView(APIView):
    """Vue pour récupérer les détails d'un hors bilan spécifique."""

    permission_classes = [IsAuthenticated]

    def get(self, request, off_balance_sheet_id, *args, **kwargs):
        try:
            item = OffBalanceSheet.objects.get(id=off_balance_sheet_id)
            serializer = OffBalanceSheetSerializer(item)
            return Response(serializer.data)
        except OffBalanceSheet.DoesNotExist:
            return Response(
                {"detail": "Hors bilan non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )


class EditOffBalanceSheetView(APIView):
    """Vue pour modifier un hors bilan existant."""

    permission_classes = [IsAuthenticated]

    def put(self, request, off_balance_sheet_id, *args, **kwargs):
        try:
            item = OffBalanceSheet.objects.get(id=off_balance_sheet_id)
            serializer = AddOffBalanceSheetSerializer(
                item, data=request.data, partial=True, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(OffBalanceSheetSerializer(item).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except OffBalanceSheet.DoesNotExist:
            return Response(
                {"detail": "Hors bilan non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )


class DeleteOffBalanceSheetsView(APIView):
    """Vue pour supprimer un ou plusieurs hors bilans en bloc."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"error": "La liste des IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        count, _ = OffBalanceSheet.objects.filter(id__in=ids).delete()

        if count == 0:
            return Response(
                {"error": "Aucun hors bilan trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"message": f"{count} hors bilan supprimé(s) avec succès."},
            status=status.HTTP_200_OK,
        )
