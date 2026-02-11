# Diyabet Takip Uygulaması – Flutter Frontend (Store Ready)

Bu proje, Google Play ve Apple App Store’a yayınlanmak üzere tasarlanmış bir diyabet takip mobil uygulamasıdır.

Bu README, bir AI coding agent tarafından projeyi uçtan uca geliştirmek için hazırlanmıştır.

---

## 1. AMAÇ

Flutter uygulaması aşağıdaki özellikleri sağlamalıdır:

- Güvenli giriş sistemi
- Sağlık verisi girişi
- Grafik ve analiz ekranları
- Kişisel AI chatbot
- Gizlilik uyum ekranları
- Veri silme ve dışa aktarma

---

## 2. ZORUNLU TEKNOLOJİLER

- Flutter (latest stable)
- Dart
- Riverpod
- Dio
- fl_chart
- Hive
- Firebase Push Notification

---

## 3. STORE GEREKSİNİMLERİ

Uygulama aşağıdaki politikaları karşılamalıdır:

- Privacy Policy ekranı
- Kullanıcı rızası alma
- Account delete özelliği
- Data export özelliği
- Açık izin yönetimi
- Offline kullanım

---

## 4. KLASÖR YAPISI

lib/
├── main.dart
├── core/
├── features/
│   ├── auth/
│   ├── dashboard/
│   ├── health/
│   ├── analytics/
│   ├── chat/
│   └── compliance/
├── widgets/
└── providers/

---

## 5. ZORUNLU EKRANLAR

### Auth

- Login  
- Register  
- MFA  

### Compliance

- Privacy Policy  
- Terms  
- Consent  
- Delete Account  

### Ana Özellikler

- Dashboard  
- Health Entry  
- Analytics  
- Chatbot  
- Profile  

---

## 6. API ENTEGRASYONU

Backend ile aşağıdaki endpointler üzerinden iletişim kurulacaktır:

/auth/*  
/health/*  
/analytics/*  
/chat/*  
/compliance/*  

---

## 7. AI CHATBOT EKRANI

Chatbot ekranı:

- Mesajlaşma arayüzü  
- Geçmiş sohbetler  
- Her mesajda yasal uyarı  

göstermelidir.

---

## 8. GİZLİLİK AKIŞI

Uygulama ilk açıldığında:

1. Privacy Policy göster  
2. Consent al  
3. Ondan sonra kullanıma izin ver  

---

## 9. STATE MANAGEMENT

Tüm uygulama Riverpod ile yazılmalıdır.

Örnek providerlar:

- authProvider  
- healthProvider  
- analyticsProvider  
- chatProvider  
- consentProvider  

---

## 10. PUSH NOTIFICATION

Firebase kullanılarak:

- Yüksek kan şekeri uyarısı  
- Hatırlatıcılar  

gönderilmelidir.

---

## 11. VIBE CODING GELİŞTİRME SIRASI

AI agent şu sırayla ilerlemelidir:

1. Proje kurulumu  
2. Auth ekranları  
3. Compliance ekranları  
4. Dashboard  
5. Health entry  
6. Analytics  
7. Chatbot  

---

## 12. APP STORE UYUMLULUK

Uygulama:

- Apple App Privacy Manifest  
- Google Data Safety Form  

gereksinimlerini karşılamalıdır.

---

## 13. TEST

Zorunlu:

- Widget testleri  
- Integration testleri  

---

## 14. ÇALIŞTIRMA

flutter pub get  
flutter run  

---

## 15. SONUÇ

Bu README takip edilerek:

- Store’a yayınlanabilir  
- Güvenli  
- Regülasyon uyumlu  

bir Flutter mobil uygulaması geliştirilmelidir.
