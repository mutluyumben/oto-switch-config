# switch-oto-config

Proje Özeti
Bu proje, Huawei switch cihazlarının seri port (COM port) üzerinden otomatik konfigürasyon yapılmasını sağlar.
Kullanıcı, basit bir arayüz üzerinden okul adı, tesis kodu, IP adresi, switch no ve switch türü gibi bilgileri girer. Proje bu bilgilere göre otomatik bir config dosyası üretir ve switch’e yükler.

Özellikler
Seri bağlantı (COM port) üzerinden switch erişimi

Boot menüsüne otomatik giriş (CTRL+B)
Tam otomasyon: reset, saved-configuration temizleme ve yeniden başlatma
Dinamik config dosyası oluşturma (template üzerinden)
Log paneli: Gönderilen komutlar ve switch’ten gelen tüm yanıtlar anlık görünür
Arayüz üzerinden manuel komut gönderme
COM port seçimi ve otomatik algılama
Blok bazlı config gönderme (interface altındaki komutları grup halinde işleme)

Kullanılan Teknolojiler
Python 3
Tkinter (GUI)
pySerial (Seri port haberleşmesi)
Custom config generator

Kurulum
Projeyi klonla:
git clone https://github.com/mutluyumben/switch-oto-config.git
cd switch-oto-config

Gerekli paketleri yükle:
pip install -r requirements.txt

Programı çalıştır:
python gui.py
