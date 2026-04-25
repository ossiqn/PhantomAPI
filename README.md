<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi"/>
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat-square&logo=openai"/>
  <img src="https://img.shields.io/badge/Docker-Supported-2496ED?style=flat-square&logo=docker"/>
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
clean JSON object. It supports both **Synchronous** (instant JSON return) and **Asynchronous** (Webhook delivery) extraction modes.

---

## Flow

```text
POST /api/v1/extract
        │
        ▼
┌─────────────────────────────────┐
│  Stealth Chrome Engine          │
│  · undetected-chromedriver      │
│  · Advanced Stealth Flags       │
│  · Proxy rotation               │
│  · Exponential backoff retry    │
└─────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────┐
│  BeautifulSoup DOM Cleaner      │
│  · script / style / svg removed │
│  · Attribute stripping          │
│  · 12 000 char token guard      │
└─────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────┐
│  OpenAI GPT-4o                  │
│  · json_object response mode    │
│  · Zero-temperature extraction  │
└─────────────────────────────────┘
        │
        ▼
   Clean JSON Response (Sync)
           OR 
   Webhook Delivery (Async)
StackLayerTechnologyAPIFastAPI + UvicornScrapingundetected-chromedriver + SeleniumDOM ParsingBeautifulSoup4 + lxmlAI EngineOpenAI GPT-4oValidationPydantic v2Rate LimitSlowAPI + Asyncio SemaphoreRetriesTenacity + exponential backoffDeploymentDocker + Docker ComposeLoggingcolorlogSetupOption 1: Docker (Recommended - 1 Click Install)PhantomAPI is fully containerized. You can run it effortlessly without dependency issues:Bashgit clone [https://github.com/ossiqn/PhantomAPI.git](https://github.com/ossiqn/PhantomAPI.git)
cd PhantomAPI
cp .env.example .env
docker-compose up -d --build
Option 2: Local EnvironmentBashgit clone [https://github.com/ossiqn/PhantomAPI.git](https://github.com/ossiqn/PhantomAPI.git)
cd PhantomAPI
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
PreviewEngine startup log showing proxy status, rate limit config and readiness signal.Usage1. Synchronous Extraction (Default)Returns the extracted JSON directly in the HTTP response.Bashcurl -X POST "http://localhost:8000/api/v1/extract" \
     -H "Content-Type: application/json" \
     -H "X-OpenAI-Key: sk-..." \
     -d '{
           "url": "[https://target-site.com/products](https://target-site.com/products)",
           "prompt": "Extract all product names and prices as a JSON array."
         }'
2. Asynchronous Webhook ExtractionFor heavy pages, provide a webhook_url. The API will immediately return a 202 Accepted response with a task_id and process the extraction in the background. Once completed, it sends the JSON payload to your webhook.Bashcurl -X POST "http://localhost:8000/api/v1/extract" \
     -H "Content-Type: application/json" \
     -H "X-OpenAI-Key: sk-..." \
     -d '{
           "url": "[https://target-site.com/products](https://target-site.com/products)",
           "prompt": "Extract all product names and prices as a JSON array.",
           "webhook_url": "[https://your-server.com/webhook/receive](https://your-server.com/webhook/receive)"
         }'
Request BodyFieldTypeRequiredDescriptionurlstring✅Full URL of the target pagepromptstring✅What data to extract and how to structure itwait_for_selectorstring❌CSS selector to wait for before capturing the DOMjavascriptstring❌Custom JS to execute after page load (max 2000c)webhook_urlstring❌Target URL to receive the extraction payloadHeadersHeaderRequiredDescriptionX-OpenAI-Key✅Your OpenAI API keyResponse (Synchronous)JSON{
  "success": true,
  "url": "[https://target-site.com/products](https://target-site.com/products)",
  "extracted_data": {
    "products": [
      { "name": "Product A", "price": "$19.99" },
      { "name": "Product B", "price": "$34.99" }
    ]
  },
  "tokens_used": 812,
  "proxy_used": "[http://1.2.3.4:8080](http://1.2.3.4:8080)",
  "elapsed_ms": 7430.21
}
Proxy SupportCreate a proxies.txt file in the project root:# Lines starting with # are ignored

[http://user:pass@1.2.3.4:8080](http://user:pass@1.2.3.4:8080)
socks5://9.10.11.12:1080
[http://5.6.7.8:3128](http://5.6.7.8:3128)
Proxies are selected randomly on each request.Bad proxies (timeout / WebDriver failure) are auto-removed from the rotation pool.If the file does not exist, PhantomAPI runs on your direct IP without interruption.EndpointsMethodPathDescriptionPOST/api/v1/extractRun extractionGET/api/v1/healthEngine health checkGET/docsSwagger UIGET/redocReDoc UIEnvironment VariablesCopy .env.example to .env and edit as needed:VariableDefaultDescriptionAPP_HOST0.0.0.0Server bind hostAPP_PORT8000Server portAPP_ENVproductionEnvironment labelPAGE_LOAD_TIMEOUT30Seconds before browser timeoutRETRY_ATTEMPTS3Max browser retry countRETRY_DELAY2Base delay between retries (s)MAX_CONTENT_CHARS12000Max chars forwarded to OpenAIPROXY_FILE_PATHproxies.txtPath to proxy list fileRATE_LIMIT_PER_MINUTE30Max requests per minute per IPMAX_CONCURRENT_TASKS5Max simultaneous browser instances (Queue cap)ADVANCED_STEALTH_MODEtrueEnable extreme WAF bypass Chrome flagsError CodesStatusMeaning401Missing or invalid X-OpenAI-Key header408Target page timed out after all retry attempts422Validation error or empty page content429Rate limit exceeded503WAF bypass failed, OpenAI unreachable, or Server Full500Unexpected internal errorProject StructurePhantomAPI/
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── src/
    ├── api/
    │   ├── routes.py
    │   └── middleware.py
    ├── core/
    │   ├── config.py
    │   ├── schemas.py
    │   └── exceptions.py
    ├── services/
    │   ├── scraper.py
    │   └── ai_parser.py
    └── utils/
        ├── proxy_manager.py
        ├── rate_limiter.py
        └── logger.py
SecurityAPI keys are never stored, logged, or hardcoded — passed per-request via header only.Rate limiting is enforced per IP via SlowAPI.Smart Queue (Semaphore) prevents server overload by capping max concurrent Chrome instances.Custom JavaScript input is capped at 2 000 characters to prevent abuse.All exception traces are server-side only; clients receive sanitized error messages.LicenseThis project is licensed under the MIT License.
See the LICENSE file for details.🌐 Community & SupportStay updated with the latest tools, scripts, and security research:PlatformLink📢 Telegramt.me/ossiqn📦 Telegram Archivet.me/ossiqnarsiv🌍 Websiteossiqn.com.tr📸 Instagraminstagram.com/ossiqnstwo🛡️ Forumblueshield.com.tr
