import os, json, hmac, hashlib, secrets, string
from datetime import datetime, timezone
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

# ── Config from environment ───────────────────────────────────────────────────
DATABASE_URL   = os.environ.get('FIREBASE_DATABASE_URL', 'https://gfxtool-bb32f-default-rtdb.firebaseio.com/').rstrip('/')
ADMIN_SECRET   = os.environ.get('ADMIN_SECRET', 'sz7rEmsBrld9RSzRPl4MkFNom17xIpSC_k9skhehDz6v-gyaGdLN-0SfPc42mzclCuOeJaqDiefQ8vEziaZf97nHifbF_d31O2RaKpWAncJKdCscrxQ_nX03cInsuUdyRv1Hxgh3N78iUtwAFu7qlc9IemgAo_D4-3HFvJ89trUlMHJMq3ksqw4sXTLv8dIGHC-iIxpz6MTY6nb4rz65LE6VtOsTBWGFAPMvQ9vEjb4k0xqKKNy3y5I7I4XSiuSagwek8Czl1WlsdycvAKS4cdhr1l5MPqq5XB3V-26_k2MTMhJgHOGJPc1qx6Jz-kZsb28mpVnxKmBkdP8r9KoUklGvS9CKDgV5YxgQGAg0m-HywlTCAOap59LjV7Z6285Pu_I09C7PmZVlo-pBCIzqt31BzfblAH47X2bWJWibDDbnhwia4F-Jd0MioyjLEuVllci1y5IPH-16309QpjQkIKbufhrIoXcI1PQDsc801m1GpWfnoNC6naJw6tRCFkgOpi1tUUvpEy7_gUhqMyR9bA').strip()
BOT_API_SECRET = os.environ.get('BOT_API_SECRET', 'oSoUSURijE1-DC05Au8Z1sJiePeSzdgpua3Ca-I3UW_-LVlAGxJz-eRAABYFEUB6').strip()

# Firebase credentials
# Automatically use the service-account JSON embedded below.
# FIREBASE_SERVICE_ACCOUNT_JSON environment variable still takes priority. Embedded credentials are used when it is not set.
_SA_JSON = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON', '').strip()
if _SA_JSON:
    try:
        FIREBASE_SERVICE_ACCOUNT_JSON = json.loads(_SA_JSON)
    except Exception as e:
        raise RuntimeError('Invalid FIREBASE_SERVICE_ACCOUNT_JSON') from e
# Service-account credentials are embedded here so no separate JSON file is required.
# The credential values below come from the provided Firebase service-account file.
# Keep this file private because it contains a private key.
else:
    FIREBASE_SERVICE_ACCOUNT_JSON = {
        'type': 'service_account', 'project_id': 'gfxtool-bb32f',
        'private_key_id': '440af8a6f85d7dd4d2af263339e60ca55fe3aa31', 'private_key': '-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQC12YN8iMCAytkk\nwmoypMBJhko50yU9DogYbW/Gyt82L7xhIWlS6d3FKSTe2H+nLyorgthOKy7TCr2q\nqCy24KQGeqE/vwnKWqq/G38aDlsmA2O916ODpYMnqYl3KvzCIRdsBbtJEh/9dXiH\n2Icdh4h1kS0Y0ot4P74/uK1xb69LKUYtTbQA5h2cuOcoVJK+vAAWDMd57cAat76o\n5PfJN34rWMFTfOrhFP0N+W2GsR2oYFr40hDwNkkljUXnW3TeaP2Bz7Q3y3oAzvMe\nsEUB9HmquFLtSNecSVorxqw7UOaO+VVb5OxNcZUx3e1SZ26v/Yp7ogrpNx9MQTsF\n4nJagOq5AgMBAAECggEAD3k1K30VaEAabvrN/4YuSHNRUI9LXWElqnJxbuhnStyP\n+nHV3PTCZprkJMQmRIsKWw50ql4ZS2LgFavetibyPgzkOKDgS+QgIEfOLmDnV5o1\nO/uj0bldKhxOcqHpRPl83Te1oneU2kPLIEAH6zbToTFbtX+A15gQ76oetAbNUydI\nsLw68hP4bSvmSy+1WuThm0KlDzgwrYlGLOOKXXV25s4CS9WbgrlOt2/J98+9U4Lf\nB+zPimacfLNkfWC9PKNO1YXZZttGhhDW8CYUWDWPylOGvPsaRKMdO9CVxkbjt5x+\nEUoTcy7cwMPo60T9JK64l/XBTF4GXyHJzKXWe2vokwKBgQDfB4BkyHbVaWewwRkG\n1eME8SE71cRUoYeaHB5miEG6yzv7MqGC+ErQvYOkWjTvfB7evRGcGemdk5slp9ny\nOdUfmTFmfjdcod55XhLxBMwcYtdaZW/3VQvyxg4gaTElmOWKVgLtFKA07CsWA57b\n0sKwUnm7NRhKkxahNCWVsdWGOwKBgQDQu5O1/e4fZ9e+jyvpzrc3adxbyh2I3cuY\nzT31rNlgS8G8YVxXtkEqpoMsDX0F+Ee0KEtlMjK86JnE8yET2iYgqkSyXc1vXjAr\n2U/KpSKsBCyrG7iAEb2gvQVvqcmKclxXO5Zas9to37tZK5O9Ivf/wA98ni9ekxor\nWOGmf+6fmwKBgQCknXDS8nNjiW0TNTM3rF7nouKYu2sx3BeuU9rMav241ZDsE67K\ncGEoOPkVMc+og8B1Pq/ku+uGdxAodv+SncUEkZm4wKg0IvWGNz1bz+KngPzap8xA\njfFHu49ptLqluXiS5nE6c+LbrQUQNpPmRGWWpwlaeBH52R721Pp4xs2HSQKBgQDD\nyf7eqaZPfRcoXqFBOa4v4zNYQfh8JhdQZ8wjgpOPuN+rtONqPsFXoULO8oQAMogH\nm/hEntZqzf9Wdvvi5C/5Wd0ANe559S5YIwmuOkGQeoXvphvkvT9S45qSx/8MxwKI\nrJL211gKQjo4hSCaO4/GLEAak0I5gt/8Iu3eQIfy2wKBgQCC3IjFaobn6b55DSV/\nmuOsx8NgS36GpXxA9I5LGr1M6IPAAfhafXS9CAjAHCrbvnp9naSB+tYLAPSuhw4g\noOO/VRPb7FpO+xc8KAyqw9RPlqLbLlitxNhIxDDk7f9h51N+iSDfB2rN9EKuk2Wn\nwnPOQslFpD6G4g5EY6VgIHbwYg==\n-----END PRIVATE KEY-----\n',
        'client_email': 'firebase-adminsdk-70hn7@gfxtool-bb32f.iam.gserviceaccount.com', 'client_id': '113521204726986896638',
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth', 'token_uri': 'https://oauth2.googleapis.com/token',
        'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs', 'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-70hn7%40gfxtool-bb32f.iam.gserviceaccount.com',
        'universe_domain': 'googleapis.com'
    }
if not firebase_admin._apps:
    firebase_admin.initialize_app(
        credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_JSON),
        {'databaseURL': DATABASE_URL}
    )

# ── Helpers ───────────────────────────────────────────────────────────────────
def now_ms():
    return int(datetime.now(timezone.utc).timestamp() * 1000)

def clean(k):
    return str(k or '').strip().upper()

def kid(k):
    """Firebase key ID — sha256 of the cleaned license key."""
    return hashlib.sha256(clean(k).encode()).hexdigest()

def auth_admin():
    """Verify x-admin-secret header."""
    if not ADMIN_SECRET:
        return False
    return hmac.compare_digest(
        request.headers.get('x-admin-secret', ''), ADMIN_SECRET
    )

def auth_bot():
    """Verify x-bot-secret header (for user-facing endpoints)."""
    if not BOT_API_SECRET:
        return False
    return hmac.compare_digest(
        request.headers.get('x-bot-secret', ''), BOT_API_SECRET
    )

def auth_any():
    """Accept either admin or bot secret."""
    return auth_admin() or auth_bot()

def get_license(k):
    return db.reference(f'licenses/{kid(k)}').get()

def newkey():
    return 'ENC-' + ''.join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16)
    )

def check(k, app_id, device_id):
    k         = clean(k)
    app_id    = str(app_id or '').strip()
    device_id = str(device_id or '').strip()

    if not k or not app_id or not device_id:
        return False, 'missing_fields', None

    lic = get_license(k)
    if not lic:
        return False, 'invalid_license', None
    if lic.get('revoked') is True:
        return False, 'revoked', lic
    expires = int(lic.get('expires_at', 0) or 0)
    if expires and now_ms() >= expires:
        return False, 'expired', lic
    if str(lic.get('app_id', '') or '') and lic.get('app_id') != app_id:
        return False, 'app_mismatch', lic

    devices = lic.get('devices') or {}
    limit   = int(lic.get('max_devices', 1))
    if device_id not in devices:
        if limit != 0 and len(devices) >= limit:
            return False, 'device_limit', lic
        devices[device_id] = {'bound_at': now_ms()}
        db.reference(f'licenses/{kid(k)}').update({'devices': devices})

    return True, 'ok', lic

# ── Public endpoints ──────────────────────────────────────────────────────────
@app.get('/')
def home():
    return jsonify(ok=True, service='license-api', database='firebase-realtime-database')

@app.post('/verify')
def verify():
    d = request.get_json(silent=True) or {}
    ok, reason, lic = check(d.get('license_key'), d.get('app_id'), d.get('device_id'))
    if not ok:
        return jsonify(ok=False, reason=reason), 403
    return jsonify(
        ok=True,
        license_key=clean(d.get('license_key')),
        app_id=d.get('app_id'),
        expires_at=lic.get('expires_at'),
        max_devices=lic.get('max_devices'),
    )

# ── User endpoints (x-bot-secret) ────────────────────────────────────────────
@app.post('/user/create-key')
def user_create_key():
    """Normal user license creation — requires x-bot-secret."""
    if not auth_bot():
        return jsonify(ok=False, error='unauthorized'), 401

    d = request.get_json(silent=True) or {}
    try:
        days  = int(d.get('days', 30))
        limit = int(d.get('max_devices', 1))
    except (TypeError, ValueError):
        return jsonify(ok=False, error='days and max_devices must be integers'), 400

    app_id           = str(d.get('app_id', '') or '').strip()
    owner_telegram_id = str(d.get('owner_telegram_id', '') or '').strip()

    if days < 1 or limit < 0:
        return jsonify(ok=False, error='invalid parameters'), 400
    if not owner_telegram_id:
        return jsonify(ok=False, error='owner_telegram_id required'), 400

    k       = newkey()
    created = now_ms()
    rec = {
        'app_id':             app_id,
        'created_at':         created,
        'expires_at':         created + days * 86400000,
        'max_devices':        limit,
        'revoked':            False,
        'devices':            {},
        'owner_telegram_id':  owner_telegram_id,
    }
    db.reference(f'licenses/{kid(k)}').set(rec)
    return jsonify(ok=True, license_key=k, **rec), 201

@app.get('/user/licenses')
def user_licenses():
    """List licenses for a specific Telegram user — requires x-bot-secret."""
    if not auth_bot():
        return jsonify(ok=False, error='unauthorized'), 401

    owner_id = str(request.args.get('owner_telegram_id', '') or '').strip()
    if not owner_id:
        return jsonify(ok=False, error='owner_telegram_id required'), 400

    all_data = db.reference('licenses').get() or {}
    result = []
    for doc_id, lic in all_data.items():
        if not isinstance(lic, dict):
            continue
        if str(lic.get('owner_telegram_id', '') or '') == owner_id:
            # Find real license key stored in record or reconstruct
            entry = dict(lic)
            entry['id'] = doc_id
            # license_key field added at creation time
            result.append(entry)

    return jsonify(ok=True, count=len(result), licenses=result)

# ── Admin endpoints (x-admin-secret) ─────────────────────────────────────────
@app.post('/admin/create-key')
def create_key():
    if not auth_admin():
        return jsonify(ok=False, error='unauthorized'), 401

    d = request.get_json(silent=True) or {}
    try:
        days  = int(d.get('days', 30))
        limit = int(d.get('max_devices', 1))
    except (TypeError, ValueError):
        return jsonify(ok=False, error='days and max_devices must be integers'), 400

    app_id = str(d.get('app_id', '') or '').strip()
    if days < 1 or limit < 0:
        return jsonify(ok=False, error='invalid parameters'), 400

    k       = newkey()
    created = now_ms()
    rec = {
        'app_id':            app_id,
        'created_at':        created,
        'expires_at':        created + days * 86400000,
        'max_devices':       limit,
        'revoked':           False,
        'devices':           {},
        'owner_telegram_id': str(d.get('owner_telegram_id', '') or '').strip(),
    }
    db.reference(f'licenses/{kid(k)}').set(rec)
    return jsonify(ok=True, license_key=k, **rec), 201

@app.get('/admin/status/<key>')
def status(key):
    if not auth_admin():
        return jsonify(ok=False, error='unauthorized'), 401
    lic = get_license(key)
    if not lic:
        return jsonify(ok=False, error='not_found'), 404
    return jsonify(ok=True, license_key=clean(key), **lic)

@app.post('/admin/revoke/<key>')
def revoke(key):
    if not auth_admin():
        return jsonify(ok=False, error='unauthorized'), 401
    if not get_license(key):
        return jsonify(ok=False, error='not_found'), 404
    db.reference(f'licenses/{kid(key)}').update({'revoked': True, 'revoked_at': now_ms()})
    return jsonify(ok=True, license_key=clean(key), revoked=True)

@app.post('/admin/unrevoke/<key>')
def unrevoke(key):
    if not auth_admin():
        return jsonify(ok=False, error='unauthorized'), 401
    if not get_license(key):
        return jsonify(ok=False, error='not_found'), 404
    db.reference(f'licenses/{kid(key)}').update({'revoked': False, 'unrevoked_at': now_ms()})
    return jsonify(ok=True, license_key=clean(key), revoked=False)

@app.post('/admin/reset-devices/<key>')
def reset_devices(key):
    if not auth_admin():
        return jsonify(ok=False, error='unauthorized'), 401
    if not get_license(key):
        return jsonify(ok=False, error='not_found'), 404
    db.reference(f'licenses/{kid(key)}').update({'devices': {}, 'devices_reset_at': now_ms()})
    return jsonify(ok=True, license_key=clean(key), devices={})

@app.get('/admin/list')
def list_keys():
    if not auth_admin():
        return jsonify(ok=False, error='unauthorized'), 401
    data = db.reference('licenses').get() or {}
    licenses = []
    for doc_id, lic in data.items():
        if isinstance(lic, dict):
            entry = dict(lic)
            entry['id'] = doc_id
            licenses.append(entry)
    return jsonify(ok=True, count=len(licenses), licenses=licenses)

# ── Error handlers ────────────────────────────────────────────────────────────
@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify(ok=False, error='method_not_allowed',
                   allowed=list(e.valid_methods or [])), 405

@app.errorhandler(404)
def not_found(e):
    return jsonify(ok=False, error='not_found'), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify(ok=False, error='internal_server_error'), 500

application = app
