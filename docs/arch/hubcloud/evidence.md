# HubCloud Evidence & Technical Traces

## 1. HTTP Response Headers (`GET /drive/yx3i8todxvnv7j9`)

```http
HTTP/2 200 
date: Tue, 01 Sep 2026 05:52:03 GMT
content-type: text/html; charset=UTF-8
server: cloudflare
cf-cache-status: HIT
nel: {"report_to":"cf-nel","max_age":604800,"endpoints":[{"url":"https://a.nel.cloudflare.com/report/v4"}]}
cf-ray: a3420286bc4ee178-MRS
```

---

## 2. Raw HTML Snippets

### Title & Header
```html
<html>
<head>
<title>(Movies4u.Foo).Ozark.S03E01.480p.WEB-DL.Hindi.English.ESub.x264.mkv</title>
<meta charset="utf-8">
<meta name="referrer" content="no-referrer"/>
<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.8.1/css/all.css" integrity="sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf" crossorigin="anonymous">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.0/dist/css/bootstrap.min.css" rel="stylesheet">
```

### Inlined Redirector Script
```javascript
var url = 'https://gamerxyt.com/hubcloud.php?host=hubcloud&id=yx3i8todxvnv7j9&token=MS9nUjVXQWRpYlBsbE1XbE1yQmZ1MjlwQVRtTE5TMjBwM1FqOXcwWkVjRT0=';

setTimeout(function(){
document.querySelector(".loading").classList.add("d-none");
document.querySelector(".vd").classList.remove("d-none");

if (false && !document.cookie.split(';').some(item => item.trim().startsWith('xlax='))) {
    stck('xlax',"s4t",1440);
    window.location.href = url;
}
}, 2000);
```

---

## 3. Network & Certificate Verification

```text
Host: hubcloud.cx
Resolved Anycast IPs: 172.67.199.249, 104.21.44.126
Issuer: Google Trust Services LLC (WE1)
Subject: hubcloud.cx
SAN: hubcloud.cx, *.hubcloud.cx
```
