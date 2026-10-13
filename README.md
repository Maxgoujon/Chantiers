# Chantiers

Relevés de site et comptes rendus d'intervention, sur le téléphone du technicien.
Application web installable (PWA), fonctionnelle hors ligne.

## Pourquoi ce dépôt est séparé

Trente techniciens s'en servent tous les jours. Le service ne doit donc rien
partager avec quoi que ce soit d'autre :

- **Aucun secret.** Pas de clé d'API, pas d'identifiant de CRM, pas de jeton.
  L'environnement est vide. Si ce service est compromis, il n'y a rien à prendre.
- **Aucun redéploiement subi.** Un correctif sur un autre projet ne redémarre pas
  l'application en plein chantier.
- **Aucune donnée client.** Le PDF est fabriqué sur le téléphone et part par le
  partage iOS. Rien ne transite par le serveur, qui ne stocke donc rien —
  et n'est pas sous-traitant au sens du RGPD.

## Ce que fait le serveur

Trois routes, et c'est tout.

| Route | Rôle |
|---|---|
| `/chantier` | L'application |
| `/ping` | Réveil pour l'hébergement gratuit |
| `/` | Redirige vers `/chantier` |

Tout le reste — formulaire, photos, génération du PDF, signatures — se passe
dans le navigateur. `templates/chantier.html` contient l'application entière.

## Où vivent les données

| Quoi | Où |
|---|---|
| Dossiers, textes, signatures | `localStorage` du téléphone |
| Photos | `IndexedDB` du téléphone |
| Coquille de l'app hors ligne | Cache du service worker |
| Rapport fini | PDF partagé vers le bot WhatsApp du client |

**L'ajout à l'écran d'accueil n'est pas un confort.** iOS efface les données d'un
site non visité pendant environ sept jours, mais épargne les applications
installées. Un technicien qui garde l'app dans un onglet perdra ses relevés.

## Mise en service

```bash
pip install -r requirements.txt
python3 app.py            # http://127.0.0.1:5000/chantier
```

### Déploiement

Hébergement type Render, plan gratuit :

1. Nouveau **Web Service** pointé sur ce dépôt
2. Build : `pip install -r requirements.txt` · Start : lu dans le `Procfile`
3. Aucune variable d'environnement à définir
4. Domaine personnalisé : `chantiers.<domaine-du-client>` → un CNAME chez eux

### Garder le service éveillé

L'hébergement gratuit s'endort après quinze minutes. Le premier technicien de la
journée attendrait quarante secondes devant un écran blanc.

Un moniteur externe gratuit — UptimeRobot, cron-job.org — qui appelle `/ping`
toutes les cinq minutes suffit, sans consommer de quota.

## Mettre à jour l'application

Le service worker sert la page en **réseau d'abord** : une correction déployée
atteint le téléphone au prochain lancement, sans manipulation.

En revanche, modifier un fichier de `static/` impose de **changer le numéro de
version du cache** dans `static/chantier-sw.js` (`const CACHE`), sinon les
téléphones gardent l'ancien.
