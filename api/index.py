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
# Automatically load the service-account JSON placed beside this index.py.
# FIREBASE_SERVICE_ACCOUNT_JSON environment variable still takes priority.
_SA_JSON = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON', '').strip()
if _SA_JSON:
    try:
        FIREBASE_SERVICE_ACCOUNT_JSON = json.loads(_SA_JSON)
    except Exception as e:
        raise RuntimeError('Invalid FIREBASE_SERVICE_ACCOUNT_JSON') from e
else:
    _SA_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'gfxtool-bb32f-firebase-adminsdk-70hn7-440af8a6f8.json'
    )
    if not os.path.isfile(_SA_FILE):
        raise RuntimeError(
            'Firebase service-account JSON not found: ' + _SA_FILE
        )
    with open(_SA_FILE, 'r', encoding='utf-8') as _f:
        FIREBASE_SERVICE_ACCOUNT_JSON = json.load(_f)

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
