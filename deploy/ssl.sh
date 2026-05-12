#!/bin/bash
# ===========================================================================
# BUCREP — Obtention et renouvellement des certificats SSL (Let's Encrypt)
# À exécuter APRÈS setup.sh et APRÈS avoir configuré les DNS
# ===========================================================================
set -e

EMAIL="ton@email.com"   # ← Remplacer par ton email

echo "Vérification DNS..."
for domain in bucrep.net www.bucrep.net application.bucrep.net; do
    ip=$(dig +short "$domain" 2>/dev/null | tail -1)
    echo "  $domain → $ip"
done

echo ""
echo "Obtention du certificat pour bucrep.net + www.bucrep.net..."
certbot --apache \
    -d bucrep.net -d www.bucrep.net \
    --email "$EMAIL" \
    --agree-tos --no-eff-email \
    --redirect

echo ""
echo "Obtention du certificat pour application.bucrep.net..."
certbot --apache \
    -d application.bucrep.net \
    --email "$EMAIL" \
    --agree-tos --no-eff-email \
    --redirect

echo ""
echo "Renouvellement automatique activé."
echo "Test renouvellement : certbot renew --dry-run"
systemctl reload apache2
