#!/usr/bin/env python3
"""Relevés de site et comptes rendus d'intervention — service autonome.

Ce service ne fait qu'une chose : servir l'application de terrain. Pas de base,
pas de clé d'API, pas d'accès à un CRM, aucun secret dans l'environnement.

C'est délibéré, et c'est la raison d'être de ce dépôt séparé. Trente techniciens
en dépendent tous les jours : un redéploiement fait pour tout autre chose ne doit
pas les couper en plein chantier, et une faille ici ne doit donner accès à rien.

Les rapports ne transitent pas par ici. Le PDF est fabriqué sur le téléphone et
part par le partage iOS vers le bot WhatsApp du client. Aucune donnée de leurs
clients ne touche ce serveur — ce qui évite aussi d'en devenir sous-traitant au
sens du RGPD.
"""
import os
from flask import Flask, render_template, redirect

app = Flask(__name__)


@app.after_request
def entetes(r):
    """Garde-fous pour un service exposé au public."""
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["X-Frame-Options"] = "DENY"
    r.headers["Referrer-Policy"] = "no-referrer"
    # La page doit toujours être revalidée : le service worker est en réseau
    # d'abord, mais un cache navigateur figerait une version corrigée.
    if r.mimetype == "text/html":
        r.headers["Cache-Control"] = "no-cache"
    return r


@app.route("/")
def accueil():
    return redirect("/chantier", code=302)


@app.route("/ping")
def ping():
    """Réveil. L'hébergement gratuit s'endort au bout de quinze minutes, et le
    premier technicien de la journée attendrait quarante secondes devant un
    écran blanc. Un moniteur externe frappe ici toutes les cinq minutes."""
    return "ok", 200


@app.route("/chantier")
def chantier():
    return render_template("chantier.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=True)
