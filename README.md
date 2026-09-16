# Vercel + Firebase Realtime Database License API

Firebase URL is preconfigured as `https://gfxtool-bb32f-default-rtdb.firebaseio.com/`.

## Vercel Environment Variables

Set these in Vercel Project Settings -> Environment Variables:

- `FIREBASE_DATABASE_URL` = `https://gfxtool-bb32f-default-rtdb.firebaseio.com/`
- `ADMIN_SECRET` = a long random secret
- `FIREBASE_SERVICE_ACCOUNT_JSON` = the complete Firebase service-account JSON, as one line

Do NOT put the service-account JSON into the launcher or commit it to GitHub.

## API endpoints

- `GET /`
- `POST /verify`
- `POST /admin/create-key`
- `GET /admin/status/<KEY>`
- `POST /admin/revoke/<KEY>`
- `POST /admin/unrevoke/<KEY>`
- `POST /admin/reset-devices/<KEY>`
- `GET /admin/list`

Admin endpoints require header `x-admin-secret`.

## Create key

```bash
curl -X POST "https://YOUR-PROJECT.vercel.app/admin/create-key" \
  -H "Content-Type: application/json" \
  -H "x-admin-secret: YOUR_ADMIN_SECRET" \
  -d '{"days":30,"max_devices":0,"app_id":"myapp"}'
```

`max_devices: 0` = unlimited devices.

## Verify

```bash
curl -X POST "https://YOUR-PROJECT.vercel.app/verify" \
  -H "Content-Type: application/json" \
  -d '{"license_key":"ENC-XXXXXXXX","app_id":"myapp","device_id":"DEVICE-ID"}'
```
