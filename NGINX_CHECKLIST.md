# Nginx verification checklist

## 1. Admin page responds via nginx

```bash
curl -I http://localhost/admin/login/
```

Expected: `200 OK` with `Server: nginx/...` in headers.

---

## 2. Static files served with caching headers

```bash
curl -I http://localhost/static/admin/css/base.css
```

Expected: `200 OK` with `Cache-Control: max-age=...` header.

---

## 3. API returns JSON

```bash
curl http://localhost/api/posts/
```

Expected: JSON list of posts.

---

## 4. Nginx returns 502 when web is down

```bash
docker compose stop web
curl -I http://localhost/api/posts/
```

Expected: `502 Bad Gateway` (returned by nginx, not connection refused).

```bash
docker compose start web
```

---

## 5. Port 8000 is not exposed to host

```bash
curl http://localhost:8000/
```

Expected: `connection refused` — daphne is internal only.

---

## 6. WebSocket upgrade works

Install `wscat` if not already installed:

```bash
npm install -g wscat
```

Connect to WebSocket:

```bash
wscat -c "ws://localhost/ws/posts/<existing-slug>/comments/?token=<jwt>"
```

Expected: `101 Switching Protocols`.

Then post a comment via REST API and confirm the WebSocket message arrives:

```bash
curl -X POST http://localhost/api/posts/<slug>/comments/ \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"text": "hello"}'
```

Alternatively use browser DevTools → Network tab → WS filter to inspect the WebSocket connection.
