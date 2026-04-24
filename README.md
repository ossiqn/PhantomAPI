<div align="center">
  <h1>👻 PhantomAPI</h1>
  <p>
    <b>Stealth WAF-bypass scraping engine with AI-powered structured data extraction.</b>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python"/>
    <img src="https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi"/>
    <img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat-square&logo=openai"/>
    <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square"/>
  </p>
</div>

---

## What is PhantomAPI?

PhantomAPI is a production-grade REST API framework that turns any website into a
structured data source — even if that site has no public API and is protected by
Cloudflare, Datadome, or similar WAF layers.

**Flow:**
```
POST /api/v1/extract
        │
        ▼
Stealth Chrome (undetected-chromedriver)
  + Proxy rotation
  + Fingerprint spoofing
        │
        ▼
BeautifulSoup DOM cleaner
  (scripts / styles / svg stripped)
        │
        ▼
OpenAI GPT-4o
  (json_object mode)
        │
        ▼
Clean JSON response
```

---

## Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| API         | FastAPI + Uvicorn                 |
| Scraping    | undetected-chromedriver + Selenium|
| DOM Parsing | BeautifulSoup4 + lxml             |
| AI Engine   | OpenAI GPT-4o                     |
| Validation  | Pydantic v2                       |
| Rate Limit  | SlowAPI                           |
| Retries     | Tenacity                          |
| Logging     | colorlog                          |

---

## Setup

```bash
git clone https://github.com/yourname/PhantomAPI.git
cd PhantomAPI
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

---

## Usage

```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
     -H "Content-Type: application/json" \
     -H "X-OpenAI-Key: sk-..." \
     -d '{
           "url": "https://target-site.com/products",
           "prompt": "Extract all product names and prices as a JSON array."
         }'
```

### Optional fields

| Field               | Type   | Description                                      |
|---------------------|--------|--------------------------------------------------|
| `wait_for_selector` | string | CSS selector to wait for before capturing DOM    |
| `javascript`        | string | Custom JS to execute after page load (max 2000c) |

### Response

```json
{
  "success": true,
  "url": "https://target-site.com/products",
  "extracted_data": {
    "products": [
      { "name": "Product A", "price": "$19.99" },
      { "name": "Product B", "price": "$34.99" }
    ]
  },
  "tokens_used": 812,
  "proxy_used": "http://1.2.3.4:8080",
  "elapsed_ms": 7430.21
}
```

---

## Proxy Support

Create a `proxies.txt` file in the project root:

```
http://user:pass@1.2.3.4:8080
socks5://9.10.11.12:1080
http://5.6.7.8:3128
```

Lines starting with `#` are ignored.
Bad proxies (timeout/WebDriver failure) are auto-removed from rotation.

---

## Endpoints

| Method | Path               | Description            |
|--------|--------------------|------------------------|
| POST   | `/api/v1/extract`  | Run extraction         |
| GET    | `/api/v1/health`   | Engine health check    |
| GET    | `/docs`            | Swagger UI             |
| GET    | `/redoc`           | ReDoc UI               |

---

## Environment Variables

| Variable               | Default        | Description                   |
|------------------------|----------------|-------------------------------|
| `APP_HOST`             | `0.0.0.0`      | Server host                   |
| `APP_PORT`             | `8000`         | Server port                   |
| `APP_ENV`              | `production`   | Environment label             |
| `PAGE_LOAD_TIMEOUT`    | `30`           | Seconds before timeout        |
| `RETRY_ATTEMPTS`       | `3`            | Max browser retry count       |
| `RETRY_DELAY`          | `2`            | Base delay between retries    |
| `MAX_CONTENT_CHARS`    | `12000`        | Max chars sent to OpenAI      |
| `PROXY_FILE_PATH`      | `proxies.txt`  | Path to proxy list            |
| `RATE_LIMIT_PER_MINUTE`| `30`           | Max requests per minute / IP  |

---

## License

MIT
