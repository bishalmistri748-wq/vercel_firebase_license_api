import os, json, hmac, hashlib, secrets, string
from datetime import datetime, timezone
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
DATABASE_URL   = 'https://gfxtool-bb32f-default-rtdb.firebaseio.com'
ADMIN_SECRET   = os.environ.get('ADMIN_SECRET', 'SlFVoNDazRPb3A0n1DvWmXuEdcfoIfiMOjL7diW-hVLR-u4DC9MgqkpVK8JSN2NyUrvYVBC-wviN5D6KBoIzlwRvsw4VC9hYR9yi2V6yPzUV4sHhClDRqPVufwqivGXGEUxX9gY74ZxS9m1jSrNq9jP_PWzJwecJox0BeGBS9DA3yuwuVzTG5XLqI2r6pXEaY4CgNNbhz0jkpoKVzWiwnEhAbgFhTVHpaafmXJo1Ipx0PIVklKZdmjVf1t1Pgt-IaYC1ZVq394JxmT6uKTjGdd1Cm7RqOvJyEYNtlx5MfoRglVBJTbIRpSVGUN7cL-bfhGKNR3tarOSZI4eM9EL9rQ').strip()
BOT_API_SECRET = os.environ.get('BOT_API_SECRET', 'oSoUSURijE1-DC05Au8Z1sJiePeSzdgpua3Ca-I3UW_-LVlAGxJz-eRAABYFEUB6').strip()

# ── Firebase Service Account ──────────────────────────────────────────────────
FIREBASE_SA = {
    "type": "service_account",
    "project_id": "gfxtool-bb32f",
    "private_key_id": "063b8bf0f6652c70c745ef33bc98bc569864fc90",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCnmb4s9Q+c3yrb\n7vX/4YQFlNthVCnio+h3ocJJ4NrM5I9wASoVdHsjrPexKmiaFkUC0afN7g74pocZ\nDk4k+JFHBPpZzzUlu8plaU+XhS9e8wSECgIFrX4NKeUMm8eXS+7nSKqKUthAzLr0\np3N56US9ZeQGJPW6mQgDsH1S+SvnjOCMQAudt/81AYHl007qoJ6CHpvw0xneEXel\n8JhG7wmOFePNcN2Ax3jQRWQ48ydt7ahGBv6Yi4t3UYf3gjIQxvGsaFnBD19rDQu7\n7C3D4aSO9AmAXUMVUu6LwHo7PF/szIWuZXfMDcd/uvs9ZkNRQ0C+U12jjLUqF2pH\nK/bZcs33AgMBAAECggEAASiKm4NfesX/DALKXNHGSUxI9A1BpYyqjNOOg5nxSpXv\nCZkjl6uWKnchk6W4K+GB9PITDeAuCAyHpGuPaal7A2TR2UWUDIur/BefXwfEL/aC\nBeq7cV4U0hRiOKBZQ9fpYSSKeTThM6nM1uexuWhUHIOyovn5YB0LWZIicSyg6uFg\nTEgusNlFjVUbcGcjCCW6PGyGIT2bbEai0xAylUycs+9avTaNQnQGg9vo740lckJL\nBv5l7pSZV9QQBfyR1ZgeqBTYzVTe3VA/nJBGzCkTkY/6CUn1bjdYX0CdRENw1/26\nikg2X3wjI4avkmkUSELfkwjkdsQaRTeVZXZY6g5YEQKBgQDZtdV2d4hPTx4jIZl0\n7vZjuXQXOAhw5YRnk1z5wgLSsNA1d6vcP6sga8sRVPx/WN/WwrQsaj3BNEI+wfIq\nAN6ZiQlXJ3oPYB2JxxgQLNO6KNDmyqW1TsEZJYe1CNRvT+wPasHZaQ+yGoQJeziR\nt1A77k6LvhsvEh6tZHZCIEBAQwKBgQDFE8YImXRDuxpSQ/llng44lcOQjTNbx6q2\n8duSXqaS2cyySjpX64KDNuzgJRWYWQW4Nn1M4p1AtRHTuSJwgJ/owjIh2qP+ptXr\npvJbdpdVLPFhls6ji/FV0sSKzqIw0sLSW3FRAX5xlh2N6enTPurOXKffs+EWq+8B\nGTW22r2qPQKBgADkwyyKTw/sRjZks+mL9YzxPO2/eCFmf8WhEDeiOTq+KQyfIiB0\nTnKCnsHCdIrdRYXvJKguA3TgjwkM6L6NZFyC+HvYGKMphNWE8K9YT8Iq2rinykhV\nO2usAMOYdq7CSDjD+mm3Ca50d2hGjjPi6bxlPQNL03a8/0085VNeKIVbAoGBALNE\nH1lnLQkHQxQd3NiAg3MZWAE/T75my3UKX66vBlqCX962AohDJD7zUVk6ooAoSjmc\n5zFu2ZgonQS4XQl1FwCE1VFSLubPH7vx6nckUtgZv6ADrAe8nlRxGnMhLwu2S51J\nrLQA5eGwqUWTxyxvCOuaAOJOH6udzhRzuBaStwAJAoGAEk+LfuslmpKBSC+9m6Gr\nWl6/uPjxMwphU/yBtd3zDlG4Uwx0DTLmLvRuSaoXbbAPLiABhB7eanhHyOdzKvZM\ncXxBZmA5SJ3BWx8HTq83fnwicJyc08qqRrJgYlgyCqsDxVdSQBuc3Olj8j/KX4l8\nOrTkNV11ZYtR/oCWf2fw25Q=\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-70hn7@gfxtool-bb32f.iam.gserviceaccount.com",
    "client_id": "113521204726986896638",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-70hn7%40gfxtool-bb32f.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

if not firebase_admin._apps:
    firebase_admin.initialize_app(
        credentials.Certificate(FIREBASE_SA),
        {'databaseURL': DATABASE_URL}
    )

# ── Helpers ───────────────────────────────────────────────────────────────────
def now_ms():
    return int(datetime.now(timezone.utc).timestamp() * 1000)

def clean(k):
    return str(k or '').strip().upper()

def kid(k):
    return hashlib.sha256(clean(k).encode()).hexdigest()

def auth_admin():
    if not ADMIN_SECRET:
        return False
    return hmac.compare_digest(request.headers.get('x-admin-secret', ''), ADMIN_SECRET)

def auth_bot():
    # Agar BOT_API_SECRET set nahi toh admin secret se bhi allow karo
    if BOT_API_SECRET:
        return hmac.compare_digest(request.headers.get('x-bot-secret', ''), BOT_API_SECRET)
    # Fallback: admin secret se bhi bot endpoints kaam karein
    return auth_admin()

def get_lic(k):
    return db.reference(f'licenses/{kid(k)}').get()

def newkey():
    return 'ENC-' + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))

def safe_str(v):
    """None values Firebase mein error deta hai — empty string do."""
    return str(v or '').strip()

def check(k, app_id, device_id):
    k         = clean(k)
    app_id    = safe_str(app_id)
    device_id = safe_str(device_id)
    if not k or not app_id or not device_id:
        return False, 'missing_fields', None
    lic = get_lic(k)
    if not lic:
        return False, 'invalid_license', None
    if lic.get('revoked') is True:
        return False, 'revoked', lic
    if int(lic.get('expires_at', 0) or 0) and now_ms() >= int(lic['expires_at']):
        return False, 'expired', lic
    if safe_str(lic.get('app_id')) and lic.get('app_id') != app_id:
        return False, 'app_mismatch', lic
    devices = lic.get('devices') or {}
    limit   = int(lic.get('max_devices', 1) or 1)
    if device_id not in devices:
        if limit != 0 and len(devices) >= limit:
            return False, 'device_limit', lic
        devices[device_id] = {'bound_at': now_ms()}
        db.reference(f'licenses/{kid(k)}').update({'devices': devices})
    return True, 'ok', lic

def make_rec(days, limit, app_id, owner_id=''):
    """Safe Firebase record — koi None value nahi."""
    created = now_ms()
    return {
        'app_id':            safe_str(app_id) or 'default',
        'created_at':        created,
        'expires_at':        created + int(days) * 86400000,
        'max_devices':       int(limit),
        'revoked':           False,
        'devices':           {},
        'owner_telegram_id': safe_str(owner_id),
    }

# ── Public ────────────────────────────────────────────────────────────────────
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

# ── User endpoints (bot.py ke liye) ──────────────────────────────────────────
@app.post('/user/create-key')
def user_create_key():
    if not auth_bot():
        return jsonify(ok=False, error='unauthorized'), 401
    d = request.get_json(silent=True) or {}
    try:
        days  = max(1, int(d.get('days', 30) or 30))
        limit = max(0, int(d.get('max_devices', 1) or 1))
    except (TypeError, ValueError):
        return jsonify(ok=False, error='days and max_devices must be integers'), 400
    owner_id = safe_str(d.get('owner_telegram_id'))
    if not owner_id:
        return jsonify(ok=False, error='owner_telegram_id required'), 400
    try:
        k   = newkey()
        rec = make_rec(days, limit, d.get('app_id'), owner_id)
        db.reference(f'licenses/{kid(k)}').set(rec)
        return jsonify(ok=True, license_key=k, **rec), 201
    except Exception as e:
        return jsonify(ok=False, error=f'firebase_error: {str(e)[:200]}'), 500

@app.get('/user/licenses')
def user_licenses():
    if not auth_bot():
        return jsonify(ok=False, error='unauthorized'), 401
    owner_id = safe_str(request.args.get('owner_telegram_id'))
    if not owner_id:
        return jsonify(ok=False, error='owner_telegram_id required'), 400
    try:
        all_data = db.reference('licenses').get() or {}
    except Exception as e:
        return jsonify(ok=False, error=f'firebase_error: {str(e)[:200]}'), 500
    result = []
    for doc_id, lic in all_data.items():
        if isinstance(lic, dict) and safe_str(lic.get('owner_telegram_id')) == owner_id:
            entry = dict(lic)
            entry['id'] = doc_id
            result.append(entry)
    return jsonify(ok=True, count=len(result), licenses=result)

# ── Admin endpoints ───────────────────────────────────────────────────────────
@app.post('/admin/create-key')
def create_key():
    if not auth_admin():
        return jsonify(ok=False, error='unauthorized'), 401
    d = request.get_json(silent=True) or {}
    try:
        days  = max(1, int(d.get('days', 30) or 30))
        limit = max(0, int(d.get('max_devices', 1) or 1))
    except (TypeError, ValueError):
        return jsonify(ok=False, error='days and max_devices must be integers'), 400
    try:
        k   = newkey()
        rec = make_rec(days, limit, d.get('app_id'), d.get('owner_telegram_id'))
        db.reference(f'licenses/{kid(k)}').set(rec)
        return jsonify(ok=True, license_key=k, **rec), 201
    except Exception as e:
        return jsonify(ok=False, error=f'firebase_error: {str(e)[:200]}'), 500

@app.get('/admin/status/<key>')
def status(key):
    if not auth_admin():
        return jsonify(ok=False, error='unauthorized'), 401
    try:
        lic = get_lic(key)
    except Exception as e:
        return jsonify(ok=False, error=f'firebase_error: {str(e)[:200]}'), 500
    if not lic:
        return jsonify(ok=False, error='not_found'), 404
    return jsonify(ok=True, license_key=clean(key), **lic)

@app.post('/admin/revoke/<key>')
def revoke(key):
    if not auth_admin():
        return jsonify(ok=False, error='unauthorized'), 401
    try:
        if not get_lic(key):
            return jsonify(ok=False, error='not_found'), 404
        db.reference(f'licenses/{kid(key)}').update({'revoked': True, 'revoked_at': now_ms()})
    except Exception as e:
        return jsonify(ok=False, error=f'firebase_error: {str(e)[:200]}'), 500
    return jsonify(ok=True, license_key=clean(key), revoked=True)

@app.post('/admin/unrevoke/<key>')
def unrevoke(key):
    if not auth_admin():
        return jsonify(ok=False, error='unauthorized'), 401
    try:
        if not get_lic(key):
            return jsonify(ok=False, error='not_found'), 404
        db.reference(f'licenses/{kid(key)}').update({'revoked': False, 'unrevoked_at': now_ms()})
    except Exception as e:
        return jsonify(ok=False, error=f'firebase_error: {str(e)[:200]}'), 500
    return jsonify(ok=True, license_key=clean(key), revoked=False)

@app.post('/admin/reset-devices/<key>')
def reset_devices(key):
    if not auth_admin():
        return jsonify(ok=False, error='unauthorized'), 401
    try:
        if not get_lic(key):
            return jsonify(ok=False, error='not_found'), 404
        db.reference(f'licenses/{kid(key)}').update({'devices': {}, 'devices_reset_at': now_ms()})
    except Exception as e:
        return jsonify(ok=False, error=f'firebase_error: {str(e)[:200]}'), 500
    return jsonify(ok=True, license_key=clean(key), devices={})

@app.get('/admin/list')
def list_keys():
    if not auth_admin():
        return jsonify(ok=False, error='unauthorized'), 401
    try:
        data = db.reference('licenses').get() or {}
    except Exception as e:
        return jsonify(ok=False, error=f'firebase_error: {str(e)[:200]}'), 500
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
    return jsonify(ok=False, error='method_not_allowed', allowed=list(e.valid_methods or [])), 405

@app.errorhandler(404)
def not_found_handler(e):
    return jsonify(ok=False, error='not_found'), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify(ok=False, error='internal_server_error', detail=str(e)[:200]), 500

application = app
