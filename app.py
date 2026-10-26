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
import json
import os
import sys
from flask import Flask, render_template, redirect, request, send_from_directory

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


@app.route("/config")
def config():
    """Reglages partages par tous les telephones.

    L'adresse de destination ne peut pas vivre dans le telephone : il faudrait
    la saisir trente fois, et la changer trente fois. Elle ne peut pas non plus
    etre figee dans le code, sinon il faut redeployer a chaque correction.

    Elle vit donc dans une variable d'environnement, modifiable depuis le
    tableau de bord de l'hebergeur en quelques secondes, sans redeploiement et
    sans toucher au code. Ce n'est pas un secret : c'est un reglage.
    """
    return {"adresse": os.environ.get("ADRESSE_RAPPORTS", "")}


@app.route("/journal", methods=["POST"])
def journal():
    """Recueille les erreurs survenues sur les telephones.

    Sans ca, personne ne sait rien : si la fabrication du PDF casse sur une
    version d'iOS, le technicien recommence trois fois puis abandonne, et
    l'information ne remonte jamais.

    Rien n'est stocke et rien n'est transmis ailleurs : on ecrit sur la sortie
    standard, que l'hebergeur affiche. Et surtout, le message n'emporte aucune
    donnee de chantier -- ni nom de client, ni adresse, ni photo. Ce service ne
    doit jamais devenir un endroit ou transitent les affaires du client.
    """
    try:
        d = request.get_json(force=True, silent=True) or {}
    except Exception:
        return "", 204
    propre = {c: str(d.get(c, ""))[:300] for c in ("quoi", "message", "version", "appareil")}
    print("JOURNAL " + json.dumps(propre, ensure_ascii=False), file=sys.stderr, flush=True)
    return "", 204


@app.route("/chantier-sw.js")
def service_worker():
    """Le worker DOIT être servi depuis la racine.

    Un service worker ne contrôle que les pages situées sous le dossier d'où il
    est servi. Depuis /static/ il ne couvrait que /static/ : il s'enregistrait
    sans erreur, et ne prenait jamais la main sur /chantier. L'application
    paraissait installée et ne fonctionnait pas hors ligne.
    """
    r = send_from_directory("static", "chantier-sw.js", mimetype="application/javascript")
    r.headers["Cache-Control"] = "no-cache"
    r.headers["Service-Worker-Allowed"] = "/"
    return r


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=True)
