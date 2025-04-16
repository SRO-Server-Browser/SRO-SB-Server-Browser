# 🧭 SRO:Server Browser System

A modern, lightweight infrastructure for **discovering, synchronizing, and connecting to Silkroad Online private servers**.  
This project aims to streamline the experience for both players and server administrators.

> ⚙️ Designed to run efficiently on low-end hardware (e.g. Samsung A31)  
> 🌐 Capable of listing and syncing a wide array of Silkroad private servers with minimal overhead

---

## 📦 System Components

### 🔹 SRO:SB – Server Browser
> **For players**

A desktop client that provides:
- Real-time private server listings
- Server metadata: ping, player count, language, description, website, etc.
- Delta synchronization with a reference client (downloads only modified files)
- Local gateway setup for seamless in-game connection
- Optional remote account registration (if supported by the server)

---

### 🔹 SRO:SH – Server Hub
> **For server administrators**

A lightweight background service that:
- Runs alongside the private server software
- Reads server details from a simple `.cfg` configuration file
- Sends updates to a centralized hub (hosted on a lightweight edge device)
- Can interface with SQL databases for remote account creation

---

### 🔹 SRO:CD – Client Database
> **For reference and synchronization**

An open-source GitHub repository that hosts a reference Silkroad client:
- Server owners fork and commit their modifications
- Clients download only the differences, reducing data usage and sync time

---

## 🌍 Why This Project?

Silkroad's private server community is vibrant but fragmented. This project addresses common pain points:

- No centralized, reliable list of active servers
- Unclear server status and metadata
- Inconvenient and repetitive client downloads
- Lack of automation in account creation and patching

**SRO:Server Browser System** offers a structured yet decentralized approach that brings:
- Transparency for players
- Discoverability for servers
- Efficiency for everyone involved

---

## ⚙️ Technical Overview

- Python with asyncio for non-blocking I/O
- TCP-based communication using JSON payloads
- Designed for environments with limited bandwidth and processing power
- Fully operational on Android-based Linux systems (e.g. Termux)

---

## 🧪 Status

The system is fully functional in its core form. A GUI-based version is under development.

---

## 📥 Installation & Usage

Release binaries and documentation will be published soon.  
In the meantime, manual setup is possible for advanced users.

---

## 🤝 Contributions Welcome

We encourage contributions in the following areas:
- Documentation & localization
- GUI development
- Server/client integration
- Community management & testing

> Made with ❤️ by a Silkroad enthusiast, for the Silkroad community.

---

---

# 🇹🇷 SRO:Sunucu Tarayıcı Sistemi

Silkroad Online özel sunucularını **keşfetmek**, **senkronize etmek** ve **bağlanmak** için geliştirilen modern ve hafif bir altyapı.  
Hem oyuncular hem de sunucu sahipleri için süreci basitleştirmeyi hedefler.

> ⚙️ Düşük donanımlı cihazlarda (örneğin Samsung A31) dahi verimli şekilde çalışır  
> 🌐 Farklı Silkroad sunucularını minimal kaynak kullanımı ile listeler ve senkronize eder

---

## 📦 Sistem Bileşenleri

### 🔹 SRO:SB – Server Browser
> **Oyuncular için**

Masaüstü istemci uygulaması:
- Gerçek zamanlı sunucu listesi
- Sunucu bilgileri: ping, oyuncu sayısı, açıklama, dil, web sitesi vb.
- Referans client ile farkları indirerek senkronizasyon (delta sync)
- Local gateway kurarak oyun içi bağlantıyı kolaylaştırır
- Desteklenirse uzaktan hesap oluşturma imkanı

---

### 🔹 SRO:SH – Server Hub
> **Sunucu sahipleri için**

Sunucu yazılımı ile birlikte çalışan arka plan hizmeti:
- `.cfg` dosyasından yapılandırma bilgilerini okur
- Merkezi HUB'a sunucu bilgilerini iletir (Samsung A31 gibi düşük donanımda çalışan sistem)
- İstenirse SQL veritabanına bağlanarak uzaktan kullanıcı oluşturabilir

---

### 🔹 SRO:CD – Client Database
> **Referans ve senkronizasyon için**

Açık kaynaklı bir GitHub deposudur:
- Sunucu sahipleri fork’layarak kendi düzenlemelerini commit’ler
- Oyuncular sadece fark dosyalarını indirir – bant genişliği ve zaman tasarrufu sağlar

---

## 🌍 Neden Bu Sistem?

Silkroad özel sunucu topluluğu canlı ama dağınıktır. Bu sistem şu sorunları çözmeyi hedefler:

- Aktif sunucuların merkezi ve güvenilir listesi yok
- Sunucu durumları ve bilgileri belirsiz
- Sürekli baştan client indirme zorunluluğu
- Hesap oluşturma ve yama işlemlerinde otomasyon eksikliği

**SRO Sunucu Tarayıcı Sistemi**, yapıyı merkezileştirmeden görünürlüğü artırır:

- Oyuncular için şeffaflık
- Sunucular için keşfedilebilirlik
- Herkes için daha az çaba, daha fazla eğlence

---

## ⚙️ Teknik Özellikler

- Python (asyncio) ile eş zamanlı, bloklamayan yapı
- TCP + JSON veri alışverişi
- Bant genişliği ve işlemci yükü düşük ortamlara uygun
- Android/Linux sistemlerde çalışır (örneğin Termux)

---

## 🧪 Geliştirme Durumu

Sistem temel fonksiyonlarıyla çalışmaktadır.  
Grafik arayüz (GUI) sürümü şu anda geliştirilmektedir.

---

## 📥 Kurulum ve Kullanım

Yakında kuruluma hazır paketler ve dökümantasyon yayınlanacaktır.  
Şimdilik ileri düzey kullanıcılar için manuel kurulum mümkündür.

---

## 🤝 Katkı Sağlayın

Açık kaynaklı bu projeye şu alanlarda katkıda bulunabilirsiniz:
- Dokümantasyon ve çeviri
- GUI / istemci geliştirme
- Sunucu entegrasyonu ve testler
- Topluluk desteği

> Silkroad topluluğu için bir Silkroad tutkunu tarafından ❤️ ile geliştirildi.

