Vercel Firebase License API — FIXED

Files:
- index.py — Flask + Firebase Realtime Database API
- requirements.txt — correct dependencies

Deploy:
1. Upload this folder/project to Vercel.
2. Vercel now supports Flask with zero configuration; no vercel.json or /api folder is required for a simple Flask app.
3. If index.py contains the Firebase service-account key, treat this project as sensitive. Rotate that Firebase key if it was exposed.
4. Set Vercel environment variable ADMIN_SECRET to your NEW admin secret if your code is configured to use it.
5. Deploy/redeploy.

API:
POST /verify
POST /admin/create-key
GET  /admin/status/<key>
POST /admin/revoke/<key>
POST /admin/unrevoke/<key>
POST /admin/reset-devices/<key>
GET  /admin/list

create-key JSON:
{"days":30,"max_devices":0,"app_id":"test-app"}

Important:
max_devices=0 means unlimited devices in this fixed version.
Browser opening /admin/create-key directly sends GET; the endpoint is POST, so use curl or an API client.
