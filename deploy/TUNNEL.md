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

## Cloudflare Tunnel

Le tunnel `gdc` de cette machine est **géré par token** : ses routes vivent
dans le dashboard, pas dans `~/.cloudflared/config.yml`. Éditer le fichier
local n'a aucun effet, et le tunnel sert déjà `legarsdeschandails.store` sur
le port 3400 — il ne faut pas le casser.

### Ajouter la route (dashboard, 1 minute)

1. **Cloudflare Zero Trust** → *Networks* → *Tunnels* → tunnel `gdc`
2. Onglet **Public Hostname** → *Add a public hostname*
3. Renseigner :
   - **Subdomain** : `heist`
   - **Domain** : la zone de ton choix (celle du tunnel, ex. `legarsdeschandails.store`)
   - **Service Type** : `HTTP`
   - **URL** : `127.0.0.1:8000`
4. *Save*. Le DNS et le certificat TLS sont créés automatiquement.

L'app est alors sur `https://heist.<ta-zone>` — HTTPS réel, donc `crypto.subtle`
fonctionne et la signature des réclamations aussi.

### Vérifier

```bash
curl -sS -o /dev/null -w "%{http_code}\n" https://heist.<ta-zone>/health
curl -sS https://heist.<ta-zone>/api/health
```

Les deux doivent répondre 200.

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

Le service tourne via `systemctl status cloudflared`. Son `ExecStart` contient
un `--token` : c'est ce token qui porte la configuration, pas le fichier local.
Un tunnel tokenisé ignore `config.yml`.

```bash
sudo systemctl restart cloudflared
journalctl -u cloudflared -n 50 --no-pager
```
