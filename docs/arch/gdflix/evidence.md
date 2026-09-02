# GDFlix Evidence & Technical Traces

## 1. HTTP Response Headers (`GET /file/8fgJTUqlTWKJ874`)

```http
HTTP/2 403 
date: Tue, 01 Sep 2026 05:52:04 GMT
content-type: text/html; charset=UTF-8
server: cloudflare
cf-ray: a342028ac8158ab9-MRS
```

---

## 2. Cloudflare Challenge Payload

```html
<!DOCTYPE html>
<html lang="en-US">
<head>
    <title>Just a moment...</title>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="robots" content="noindex,nofollow">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta http-equiv="content-security-policy" content="default-src 'none'; script-src 'nonce-...' https://challenges.cloudflare.com; ...">
</head>
<body>
    <div class="main-content">
        <div id="challenge-running" class="challenge-running">
            <p>Checking if the site connection is secure</p>
        </div>
    </div>
</body>
</html>
```

---

## 3. Network & Certificate Verification

```text
Host: gdflix.dev
Resolved Anycast IPs: 104.21.52.244, 172.67.205.213
Issuer: Google Trust Services LLC (WE1)
Subject: gdflix.dev
SAN: gdflix.dev, *.gdflix.dev
```
