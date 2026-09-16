import os, json, hmac, hashlib, secrets, string
from datetime import datetime, timezone
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)
DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL','https://gfxtool-bb32f-default-rtdb.firebaseio.com/').rstrip('/')
ADMIN_SECRET = os.environ.get('ADMIN_SECRET','SlFVoNDazRPb3A0n1DvWmXuEdcfoIfiMOjL7diW-hVLR-u4DC9MgqkpVK8JSN2NyUrvYVBC-wviN5D6KBoIzlwRvsw4VC9hYR9yi2V6yPzUV4sHhClDRqPVufwqivGXGEUxX9gY74ZxS9m1jSrNq9jP_PWzJwecJox0BeGBS9DA3yuwuVzTG5XLqI2r6pXEaY4CgNNbhz0jkpoKVzWiwnEhAbgFhTVHpaafmXJo1Ipx0PIVklKZdmjVf1t1Pgt-IaYC1ZVq394JxmT6uKTjGdd1Cm7RqOvJyEYNtlx5MfoRglVBJTbIRpSVGUN7cL-bfhGKNR3tarOSZI4eM9EL9rQ').strip()

# Firebase service-account credential embedded directly in this file.
FIREBASE_SERVICE_ACCOUNT_JSON = {'type': 'service_account', 'project_id': 'gfxtool-bb32f', 'private_key_id': '6e8e9d71814e066e369cbfee83cf2f514d1d2bcd', 'private_key': '-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC6LWwD/oR1/NPT\n1xeOVe+8O+MY+vPhNqRbFKMFl/t+oEtz8A/micKKGdxBFFPhr6xk3J5/sGoWGR5C\ndPPjEN1fstKof11QjJQLNYJS3EMBwJrTWe5o+88I9OU4G9TrJxAXIynmBa4B72tx\nXF3y5UEN5B/9RCdH9q+w0FsaSzR+5+w6I9y2zaJmvjdC4MqISEH58z6qW3akplRx\nR1hR3SFKEYIU+sib/MoLgmtn2NOwbJEE1WfyJfZpvwLwcl3zCfUDaKcTXxBcPnTl\n94j4G7/BnCXnH1G9VZ9JQLdEAz8ZmyuLZB+MIxpNyDBW4OGRIVHFjjq3NtpeQhWG\n25CQaG29AgMBAAECggEAMs5nbjWcN0iOE/7cHkskV5VuNWhyelC7jGF21XVyu80J\nmjN2W17XuHEzMo1WEL4siP/NvyHI6YvkPpWE4r+88bsukq3jLLKYSfDJxkv2ezlw\n5uFhVsP07UhLb0LlGWD5Gp9NdUiygjOweeiPeNQIKz7IXgilwZU3v8Q0QFoqksDH\nHVwHMbeHRe/ftpPPOSuZ2luVuza9lzu4B53qfU2fkHd7xILSI9Ue+n91bqFcoBJs\nvL+lm1vmTgt6kUpzGRoqWTInkpYjmM3ISONfkEzW/Z01Uq9V7VB0YlZE8y8ZcUG2\nkmUXv/Spsee0wvUJS2MFj8IFXBBoCfRAXPPhl9VgDwKBgQDtMSwFFNaBU1xwHUNu\nwFLwZc03E1gSncZSgWHmGG93scQZ2+CS2LlIIU2bSfwjZyL+/nCaqPB1zYBE/6rE\nLu95brmdZ5KRNZlf1fp0ecPZl5797JhbPV1yzf1oT7aUamWL+Z5wA8BXpVLj1RGB\nTvwsJT5ucGLLCPSpoijI2dcIHwKBgQDI8LB+OTY39uM/HSXIGJA1/Sokx3d+tWqX\ntvhRWVNektdDOKSf+mXUAvL2Sn8Mqb/LBWhh6oHLRfhZ1Muhs9MXjlmHYYb4elOe\noBmzpFzno5da+y7xrllFOfIUQMHj17HQjPXX4ihg14RiLR3Za8I8y/RB/o9Z01y/\nTkEEtaF+owKBgEh9N6PR64CYtm55Mwuc8XwQ0LfdTJRb7al3azEEFMTy6iiw/yBB\n5dY6f1pPMSSst5BQuJ87tEl8ZZAwxsKwSXXGNin55lxEkjwszB9eu1E7ulaGQUXZ\nKj8U3zZK7lTLc39k6Vv4eYcPupZwnqnzNrRTKZJc/IRql0NkkKxZjxMnAoGBAJF2\nhB3sJs7ewGWJITe4aHVc/yw+5cdpZ2/K+fpR8uNs4756+9n/98VCGUaoaU7ud7Ru\nBsGTdUCFN6M4Q+2ccz0DRNaXiJDKZUxY1CJS4xqhN8maOsKkl2Vg7FkzA+l/1O6H\njNUqmFZ6zhAQXyJtOuCuOPWpZXb+Zo7rBHB3WCCHAoGAXi2lTVIPajIJlbuIrV++\n3Qy2DpSwlhsT8R4NyfkrLWkHonVYnl6NZq+aL1kobMWbAoFMDr0q5bc2cA/uAUoh\n7Z1sf+XUTemAHSsAxBiRSrrGo9oHaBkWdo4fVi/+OJAH2vdFU0pHQwJBVsw7T+qn\niyRVIbq1NpRoX6mtrcP9ZKY=\n-----END PRIVATE KEY-----\n', 'client_email': 'firebase-adminsdk-70hn7@gfxtool-bb32f.iam.gserviceaccount.com', 'client_id': '113521204726986896638', 'auth_uri': 'https://accounts.google.com/o/oauth2/auth', 'token_uri': 'https://oauth2.googleapis.com/token', 'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs', 'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-70hn7%40gfxtool-bb32f.iam.gserviceaccount.com', 'universe_domain': 'googleapis.com'}

if not firebase_admin._apps:
    firebase_admin.initialize_app(
        credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_JSON),
        {'databaseURL': DATABASE_URL}
    )

def now_ms(): return int(datetime.now(timezone.utc).timestamp()*1000)
def clean(k): return str(k or '').strip().upper()
def kid(k): return hashlib.sha256(clean(k).encode()).hexdigest()
def auth(): return bool(ADMIN_SECRET) and hmac.compare_digest(request.headers.get('x-admin-secret',''), ADMIN_SECRET)
def get(k): return db.reference(f'licenses/{kid(k)}').get()
def newkey(): return 'ENC-' + ''.join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(16))

def check(k, app_id, device_id):
    k=clean(k); app_id=str(app_id or '').strip(); device_id=str(device_id or '').strip()
    if not k or not app_id or not device_id: return False,'missing_fields',None
    lic=get(k)
    if not lic: return False,'invalid_license',None
    if lic.get('revoked') is True: return False,'revoked',lic
    if int(lic.get('expires_at',0) or 0) and now_ms() >= int(lic['expires_at']): return False,'expired',lic
    if str(lic.get('app_id','') or '') and lic.get('app_id') != app_id: return False,'app_mismatch',lic
    devices=lic.get('devices') or {}; limit=int(lic.get('max_devices', 1))
    if device_id not in devices:
        if limit != 0 and len(devices) >= limit: return False,'device_limit',lic
        devices[device_id]={'bound_at':now_ms()}
        db.reference(f'licenses/{kid(k)}').update({'devices':devices})
    return True,'ok',lic

@app.get('/')
def home(): return jsonify(ok=True,service='license-api',database='firebase-realtime-database')

@app.post('/verify')
def verify():
    d=request.get_json(silent=True) or {}; ok,reason,lic=check(d.get('license_key'),d.get('app_id'),d.get('device_id'))
    if not ok: return jsonify(ok=False,reason=reason),403
    return jsonify(ok=True,license_key=clean(d.get('license_key')),app_id=d.get('app_id'),expires_at=lic.get('expires_at'),max_devices=lic.get('max_devices'))

@app.post('/admin/create-key')
def create_key():
    if not auth(): return jsonify(ok=False,error='unauthorized'),401
    d=request.get_json(silent=True) or {}
    try:
        days = int(d.get('days', 30))
        limit = int(d.get('max_devices', 1))
    except (TypeError, ValueError):
        return jsonify(ok=False, error='days and max_devices must be integers'), 400
    app_id = str(d.get('app_id', '') or '').strip()
    if days < 1 or limit < 0:
        return jsonify(ok=False, error='invalid parameters'), 400
    k=newkey(); created=now_ms(); rec={'app_id':app_id,'created_at':created,'expires_at':created+days*86400000,'max_devices':limit,'revoked':False,'devices':{}}
    db.reference(f'licenses/{kid(k)}').set(rec)
    return jsonify(ok=True,license_key=k,**rec),201

@app.get('/admin/status/<key>')
def status(key):
    if not auth(): return jsonify(ok=False,error='unauthorized'),401
    lic=get(key)
    if not lic: return jsonify(ok=False,error='not_found'),404
    return jsonify(ok=True,license_key=clean(key),**lic)

@app.post('/admin/revoke/<key>')
def revoke(key):
    if not auth(): return jsonify(ok=False,error='unauthorized'),401
    if not get(key): return jsonify(ok=False,error='not_found'),404
    db.reference(f'licenses/{kid(key)}').update({'revoked':True,'revoked_at':now_ms()})
    return jsonify(ok=True,license_key=clean(key),revoked=True)

@app.post('/admin/unrevoke/<key>')
def unrevoke(key):
    if not auth(): return jsonify(ok=False,error='unauthorized'),401
    if not get(key): return jsonify(ok=False,error='not_found'),404
    db.reference(f'licenses/{kid(key)}').update({'revoked':False,'unrevoked_at':now_ms()})
    return jsonify(ok=True,license_key=clean(key),revoked=False)

@app.post('/admin/reset-devices/<key>')
def reset_devices(key):
    if not auth(): return jsonify(ok=False,error='unauthorized'),401
    if not get(key): return jsonify(ok=False,error='not_found'),404
    db.reference(f'licenses/{kid(key)}').update({'devices':{},'devices_reset_at':now_ms()})
    return jsonify(ok=True,license_key=clean(key),devices={})

@app.get('/admin/list')
def list_keys():
    if not auth(): return jsonify(ok=False,error='unauthorized'),401
    data=db.reference('licenses').get() or {}
    return jsonify(ok=True,count=len(data),licenses=[dict(v or {},id=k) for k,v in data.items()])

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify(ok=False, error='method_not_allowed', allowed=list(e.valid_methods or [])), 405

@app.errorhandler(404)
def not_found(e):
    return jsonify(ok=False, error='not_found'), 404


application=app
