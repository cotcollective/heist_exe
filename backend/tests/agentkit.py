"""Utilitaires de test : génération de clés et signature de réclamation.

On signe pour de vrai — avec la même courbe (P-256), le même message
canonique et le même encodage que le navigateur — pour que les tests
exercent le chemin de vérification réel, pas un mock.
"""
import base64
import time

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature


def _b64(i: int) -> str:
    return base64.urlsafe_b64encode(i.to_bytes(32, "big")).decode().rstrip("=")


def make_agent() -> tuple[ec.EllipticCurvePrivateKey, dict]:
    """Paire de clés P-256 + JWK publique, comme WebCrypto les produit."""
    priv = ec.generate_private_key(ec.SECP256R1())
    nums = priv.public_key().public_numbers()
    jwk = {"kty": "EC", "crv": "P-256", "x": _b64(nums.x), "y": _b64(nums.y)}
    return priv, jwk


def sign_claim(priv, waypoint_id: int, player_name: str, ts: int | None = None):
    """Signe « waypoint_id|player_name|ts » et renvoie (signature, ts).

    WebCrypto sort une signature brute r‖s de 64 octets ; `cryptography`
    renvoie du DER. On convertit pour coller au format navigateur.
    """
    ts = int(time.time()) if ts is None else ts
    message = f"{waypoint_id}|{player_name}|{ts}".encode("utf-8")
    der = priv.sign(message, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    raw = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return base64.urlsafe_b64encode(raw).decode().rstrip("="), ts
