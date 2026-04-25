<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi"/>
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat-square&logo=openai"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square"/>
  <img src="https://img.shields.io/badge/WAF-Bypass-red?style=flat-square"/>
  <img src="https://img.shields.io/badge/Stealth-Chrome-grey?style=flat-square&logo=googlechrome"/>

  <br/>
  <br/>

  <h1>👻 PhantomAPI</h1>
  <p>
    <b>Stealth WAF-bypass scraping engine with AI-powered structured data extraction.</b>
  </p>
  <p>
    Turn any website into a structured JSON API — no matter what WAF protects it.
  </p>
</div>

---

## What is PhantomAPI?

PhantomAPI is a production-grade REST API framework that turns any website into a
structured data source — even if that site has no public API and is protected by
Cloudflare, Datadome, or similar WAF layers.

It drives a real, fingerprint-spoofed Chrome browser, cleans the DOM, then feeds
the content to **GPT-4o** which returns exactly the data you asked for as a
clean JSON object.

---

## Flow

```text
POST /api/v1/extract
        │
        ▼
┌─────────────────────────────────┐
│  Stealth Chrome Engine          │
│  · undetected-chromedriver      │
│  · Fingerprint spoofing         │
│  · Proxy rotation               │
│  · Exponential backoff retry    │
└─────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────┐
│  BeautifulSoup DOM Cleaner      │
│  · script / style / svg removed │
│  · Attribute stripping          │
│  · 12 000 char token guard      │
└─────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────┐
│  OpenAI GPT-4o                  │
│  · json_object response mode    │
│  · Zero-temperature extraction  │
└─────────────────────────────────┘
        │
        ▼
   Clean JSON Response
```

---

## Stack

| Layer       | Technology                         |
|-------------|------------------------------------|
| API         | FastAPI + Uvicorn                  |
| Scraping    | undetected-chromedriver + Selenium |
| DOM Parsing | BeautifulSoup4 + lxml              |
| AI Engine   | OpenAI GPT-4o                      |
| Validation  | Pydantic v2                        |
| Rate Limit  | SlowAPI                            |
| Retries     | Tenacity + exponential backoff     |
| Logging     | colorlog                           |

---

## Setup

```bash
git clone https://github.com/ossiqn/PhantomAPI.git
cd PhantomAPI
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

---

## Preview

![PhantomAPI Terminal Preview](https://i.imgur.com/PLACEHOLDER.png)

> Engine startup log showing proxy status, rate limit config and readiness signal.

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

### Request Body

| Field                 | Type   | Required | Description                                       |
|-----------------------|--------|----------|---------------------------------------------------|
| `url`                 | string | ✅       | Full URL of the target page                       |
| `prompt`              | string | ✅       | What data to extract and how to structure it      |
| `wait_for_selector`   | string | ❌       | CSS selector to wait for before capturing the DOM |
| `javascript`          | string | ❌       | Custom JS to execute after page load (max 2000c)  |

### Headers

| Header          | Required | Description              |
|-----------------|----------|--------------------------|
| `X-OpenAI-Key`  | ✅       | Your OpenAI API key      |

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
# Lines starting with # are ignored

http://user:pass@1.2.3.4:8080
socks5://9.10.11.12:1080
http://5.6.7.8:3128
```

- Proxies are selected randomly on each request.
- Bad proxies (timeout / WebDriver failure) are **auto-removed** from the rotation pool.
- If the file does not exist, PhantomAPI runs on your direct IP without interruption.

---

## Endpoints

| Method | Path              | Description         |
|--------|-------------------|---------------------|
| POST   | `/api/v1/extract` | Run extraction      |
| GET    | `/api/v1/health`  | Engine health check |
| GET    | `/docs`           | Swagger UI          |
| GET    | `/redoc`          | ReDoc UI            |

---

## Environment Variables

Copy `.env.example` to `.env` and edit as needed:

| Variable                | Default        | Description                    |
|-------------------------|----------------|--------------------------------|
| `APP_HOST`              | `0.0.0.0`      | Server bind host               |
| `APP_PORT`              | `8000`         | Server port                    |
| `APP_ENV`               | `production`   | Environment label              |
| `PAGE_LOAD_TIMEOUT`     | `30`           | Seconds before browser timeout |
| `RETRY_ATTEMPTS`        | `3`            | Max browser retry count        |
| `RETRY_DELAY`           | `2`            | Base delay between retries (s) |
| `MAX_CONTENT_CHARS`     | `12000`        | Max chars forwarded to OpenAI  |
| `PROXY_FILE_PATH`       | `proxies.txt`  | Path to proxy list file        |
| `RATE_LIMIT_PER_MINUTE` | `30`           | Max requests per minute per IP |

---

## Error Codes

| Status | Meaning                                          |
|--------|--------------------------------------------------|
| `401`  | Missing or invalid `X-OpenAI-Key` header         |
| `408`  | Target page timed out after all retry attempts   |
| `422`  | Validation error or empty page content           |
| `429`  | Rate limit exceeded                              |
| `503`  | WAF bypass failed or OpenAI unreachable          |
| `500`  | Unexpected internal error                        |

---

## Project Structure

```
PhantomAPI/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── src/
    ├── api/
    │   ├── routes.py
    │   └── middleware.py
    ├── core/
    │   ├── config.py
    │   ├── schemas.py
    │   └── exceptions.py
    ├── services/
    │   ├── scraper.py
    │   └── ai_parser.py
    └── utils/
        ├── proxy_manager.py
        ├── rate_limiter.py
        └── logger.py
```

---

## Security

- API keys are **never** stored, logged, or hardcoded — passed per-request via header only.
- Rate limiting is enforced per IP via SlowAPI.
- Custom JavaScript input is capped at 2 000 characters to prevent abuse.
- All exception traces are server-side only; clients receive sanitized error messages.

---

## License

This project is licensed under the **MIT License**.
See the [LICENSE](LICENSE) file for details.

---

<div align="center">

## 🌐 Community & Support

Stay updated with the latest tools, scripts, and security research:

<br/>

| Platform          | Link                                                                 |
|-------------------|----------------------------------------------------------------------|
| 📢 Telegram       | [t.me/ossiqn](https://t.me/ossiqn)                                  |
| 📦 Telegram Archive | [t.me/ossiqnarsiv](https://t.me/ossiqnarsiv)                      |
| 🌍 Website        | [ossiqn.com.tr](https://ossiqn.com.tr)                              |
| 📸 Instagram      | [instagram.com/ossiqnstwo](https://instagram.com/ossiqnstwo)        |
| 🛡️ Forum          | [blueshield.com.tr](https://www.blueshield.com.tr)                  |

<br/>

---

<sub>
  Built with 👻 by
  <a href="https://ossiqn.com.tr"><b>Ossiqn</b></a>
  — PhantomAPI is intended for legal use only.
  Always ensure you have permission to scrape a target website.
</sub>

</div>
