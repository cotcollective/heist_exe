# Exposer HEIST.EXE publiquement

L'app tourne sur **un seul port** : FastAPI sert l'API, le frontend bâti, le
service worker et le manifeste. Un tunnel n'a donc qu'une cible.

```bash
./deploy/serve.sh              # http://127.0.0.1:8000
PORT=8090 ./deploy/serve.sh    # autre port
```

Le script refuse de démarrer sans `ADMIN_KEY` — l'administration répondrait
503 de toute façon, autant le dire tout de suite.

---

## Ce qui est déjà en place sur cette machine

Un tunnel **dédié** au jeu, distinct de `gdc` qui sert `legarsdeschandails.store`
sur le port 3400 :

| | |
|---|---|
| Tunnel | `heist` — `dce36269-d6f7-4a12-a0d3-958a2331a578` |
| Config | `~/.cloudflared/heist.yml` (ingress local, pas de token) |
| Hôte | `https://chasse.legarsdeschandails.store` |
| Cible | `http://127.0.0.1:8000` |

Le CNAME a été créé avec `cloudflared tunnel route dns`, qui s'authentifie
avec le `cert.pem` de `cloudflared tunnel login` — **pas besoin de token API**.
C'est ce qu'il faut utiliser : un token « Edit zone DNS » ne peut pas créer de
tunnel ni poser d'ingress.

> ⚠️ `cloudflared tunnel route dns heist …` résout parfois le nom vers un
> **autre** tunnel et le dit dans sa sortie (`tunnelID=…`). Toujours lire cette
> ligne. Passer l'UUID explicite évite l'ambiguïté.

### Poser les services (survit à la session)

```bash
sudo cp deploy/heist.service deploy/heist-tunnel.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now heist heist-tunnel
systemctl status heist heist-tunnel --no-pager
```

---

## Ajouter une autre route

```bash
cloudflared tunnel route dns dce36269-d6f7-4a12-a0d3-958a2331a578 <hôte>
```
puis ajouter le `hostname` correspondant dans `~/.cloudflared/heist.yml` et
redémarrer `heist-tunnel`.

Un CNAME ne peut pas être réécrit : s'il existe déjà pour cet hôte, il faut le
supprimer d'abord (dashboard → DNS), sinon `route dns` renvoie `code: 1003`.

---

## Ce qui est exposé, et ce qui ne l'est pas

| Route | Public | Garde |
|-------|--------|-------|
| `/`, `/world`, `/hunt`… | oui | — |
| `/api/missions/*`, `/api/waypoints/*` | oui | jeton joueur (PIN) |
| `/api/world/caches` | oui | lecture seule |
| `/api/world/caches/{id}/claim` | oui | signature ECDSA de l'appareil |
| `/api/world/publish` | oui | `ADMIN_KEY` |
| `/api/admin/*` | oui | `ADMIN_KEY` |
| `/api/docs` | oui | — |

`ADMIN_KEY` est un secret partagé sans limite de débit. Sur une URL publique
c'est le maillon faible. Deux façons de le sortir du chemin :

1. **Ne pas exposer `/admin`** : le builder reste utilisé en local
   (`http://127.0.0.1:8000/admin`), le tunnel ne sert qu'aux joueurs. C'est le
   plus simple et c'est suffisant — papa construit à la maison.
2. **Cloudflare Access** devant `/admin/*` (gratuit jusqu'à 50 utilisateurs) si
   tu veux vraiment builder à distance.

Option 1 par défaut. Rien à configurer.

---

## Si le tunnel casse

Le service `cloudflared` du système (`gdc`) contient un `--token` dans son
`ExecStart` : c'est ce token qui porte sa configuration, pas le fichier local.
Un tunnel tokenisé ignore `config.yml`. Le tunnel `heist`, lui, est localement
géré et lit `~/.cloudflared/heist.yml`.

```bash
systemctl status heist heist-tunnel --no-pager
journalctl -u heist-tunnel -n 50 --no-pager
```
