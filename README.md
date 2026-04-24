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
structured data source - even if that site has no public API and is protected by
Cloudflare, Datadome, or similar WAF layers.

**Flow:**
```text
POST /api/v1/extract
        |
        V
Stealth Chrome (undetected-chromedriver)
  + Proxy rotation
  + Fingerprint spoofing
        |
        V
BeautifulSoup DOM cleaner
  (scripts / styles / svg stripped)
        |
        V
OpenAI GPT-4o
  (json_object mode)
        |
        V
Clean JSON response
StackLayerTechnologyAPIFastAPI + UvicornScrapingundetected-chromedriver + SeleniumDOM ParsingBeautifulSoup4 + lxmlAI EngineOpenAI GPT-4oValidationPydantic v2Rate LimitSlowAPIRetriesTenacityLoggingcolorlogSetupBashgit clone [https://github.com/ossiqn/PhantomAPI.git](https://github.com/ossiqn/PhantomAPI.git)
cd PhantomAPI
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
UsageBashcurl -X POST "http://localhost:8000/api/v1/extract" \
     -H "Content-Type: application/json" \
     -H "X-OpenAI-Key: sk-..." \
     -d '{
           "url": "[https://target-site.com/products](https://target-site.com/products)",
           "prompt": "Extract all product names and prices as a JSON array."
         }'
Optional fieldsFieldTypeDescriptionwait_for_selectorstringCSS selector to wait for before capturing DOMjavascriptstringCustom JS to execute after page load (max 2000c)ResponseJSON{
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
Proxy SupportCreate a proxies.txt file in the project root:Plaintext[http://user:pass@1.2.3.4:8080](http://user:pass@1.2.3.4:8080)
socks5://9.10.11.12:1080
[http://5.6.7.8:3128](http://5.6.7.8:3128)
Lines starting with # are ignored.Bad proxies (timeout/WebDriver failure) are auto-removed from rotation.EndpointsMethodPathDescriptionPOST/api/v1/extractRun extractionGET/api/v1/healthEngine health checkGET/docsSwagger UIGET/redocReDoc UIEnvironment VariablesVariableDefaultDescriptionAPP_HOST0.0.0.0Server hostAPP_PORT8000Server portAPP_ENVproductionEnvironment labelPAGE_LOAD_TIMEOUT30Seconds before timeoutRETRY_ATTEMPTS3Max browser retry countRETRY_DELAY2Base delay between retriesMAX_CONTENT_CHARS12000Max chars sent to OpenAIPROXY_FILE_PATHproxies.txtPath to proxy listRATE_LIMIT_PER_MINUTE30Max requests per minute / IP🌐 Community & SupportStay updated with the latest security news, tools, and scripts:Telegram (Main): t.me/ossiqnTelegram Archive: t.me/ossiqnarsivWebsite & Portfolio: ossiqn.com.trInstagram: instagram.com/ossiqnstwoOfficial Forum: www.blueshield.com.tr
