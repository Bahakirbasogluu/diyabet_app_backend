# 🚀 Backend Production Checklist
# Frontend tamamlandıktan sonra bu adımlar yapılacak.

---

## 🔴 KRİTİK - Store'a Koymadan Önce

### 1. Güvenlik Düzeltmeleri
- [ ] `.env` → `DEBUG=false`
- [ ] `main.py` → `allow_origins=["*"]` yerine spesifik origin yaz
- [ ] `main.py` → Production'da `/docs` ve `/redoc` kapat
- [ ] JWT_SECRET_KEY'in güçlü olduğundan emin ol (✅ yapıldı)

### 2. Deploy (Cloud Hosting)
- [ ] Railway.app veya Render.com hesabı aç
- [ ] GitHub'a push et
- [ ] Platform üzerinde repo bağla
- [ ] Environment variables ekle (tüm .env içeriği)
- [ ] Deploy et → HTTPS otomatik gelir

### 3. Veritabanı Migration
```bash
alembic revision --autogenerate -m "initial_tables"
alembic upgrade head
```

---

## 🟡 Store Onayı İçin

### 4. Gizlilik Politikası
- [ ] Web sayfası oluştur (GitHub Pages yeterli)
- [ ] KVKK/GDPR uyumlu metin yaz
- [ ] Store listing'e URL ekle

### 5. Veri Silme Mekanizması
- [x] `DELETE /users/data` endpoint'i var ✅
- [ ] Store listing'e "veri silme talimatları" linki ekle

### 6. Email Domain
- [ ] Resend'de kendi domainini doğrula
- [ ] `EMAIL_FROM=noreply@senin-domainin.com` yap

---

## 🟢 İYİ OLUR

### 7. CORS Ayarı (main.py)
```python
allow_origins=[
    "https://senin-domainin.com",
    "capacitor://localhost",
    "http://localhost"
]
```

### 8. Swagger Koruması (main.py)
```python
app = FastAPI(
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)
```

### 9. Sentry Error Tracking (opsiyonel)
- [ ] sentry.io hesap aç
- [ ] `sentry-sdk[fastapi]` ekle

---

## Önerilen Deploy Platformları

| Platform | Fiyat | Not |
|----------|-------|-----|
| Railway.app | $5/ay | En kolay, önerilen |
| Render.com | Ücretsiz (yavaş) | Cold start sorunu var |
| Fly.io | $5/ay | Hızlı |
| DigitalOcean | $5/ay | Güvenilir |

> Supabase DB + Upstash Redis zaten cloud. Sadece FastAPI deploy edilecek.
