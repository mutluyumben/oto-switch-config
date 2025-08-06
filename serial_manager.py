import serial
import time

class SerialManager:
    def __init__(self, port, baudrate=9600, log_callback=None):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.log_callback = log_callback or print
        self.gui_logger = None  # GUI log fonksiyonu


    def log(self, message, direction="info"):
        # Temiz ama görünmeyen karakterleri kaçırmamak için repr() kullan
        debug_line = repr(message)

        if direction == "in":
            tagged = f"[⬅ GİREN VERİ] {debug_line}"
        elif direction == "out":
            tagged = f"[➡ GÖNDERİLEN] {debug_line}"
        else:
            tagged = f"[~] {debug_line}"

        print(tagged)
        if self.gui_logger:
            self.gui_logger(tagged)



    def open(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        self.log(f"[+] {self.port} bağlantısı açıldı")

    def close(self):
        if self.ser:
            self.ser.close()
            self.log(f"[+] {self.port} bağlantısı kapatıldı")
    
    def send_enter(self):
        self.ser.write(b"\r\n")
        self.log("[>>] ENTER gönderildi")
        time.sleep(1)


    def wait_for_boot_menu_or_password(self):
        self.log("[~] Ctrl+B spam başlatıldı...")
        buffer = ""
        found = False

        def spam_ctrl_b():
            while not found and self.ser and self.ser.is_open:
                self.ser.write(b'\x02')  # Ctrl+B
                time.sleep(0.2)  # 200ms delay (daha hızlı tepki verir)
        
        import threading
        spam_thread = threading.Thread(target=spam_ctrl_b)
        spam_thread.start()

        try:
            while True:
                line = self.ser.readline().decode(errors='ignore')
                if line:
                    self.log(line.strip())
                    buffer += line
                    if "BootROM MENU" in line or "password:" in line:
                        self.log("[+] BootROM menüye geçildi veya şifre istendi")
                        found = True
                        break
        finally:
            found = True  # spam thread duracak
            spam_thread.join()


    def send_line(self, text):
        self.ser.write((text + "\r\n").encode())
        self.log(f"[>>] Gönderildi: {text}")
        time.sleep(1)

    def send_ctrl_b(self):
        self.ser.write(b'\x02')
        self.log("[>>] CTRL+B gönderildi")
        time.sleep(1)

    


    def wait_for_log(self, keyword):
        return self.wait_for_prompt(keyword)
    
    def wait_for_last_port(self, port_number):
        self.log(f"[~] {port_number}. port logu bekleniyor...")
        while True:
            line = self.ser.readline().decode(errors="ignore").strip()
            if line:
                self.log(line)
                if f"[{port_number}]" in line:
                    self.log("[+] Son port logu görüldü, sistem hazır.")
                    break

    
    def wait_for_system_ready(self):
        self.log("[~] Switch başlatma logları bekleniyor...")
        enable_counter = 0
        last_prompt_seen = False
        while True:
            line = self.ser.readline().decode(errors='ignore').strip()
            if line:
                self.log(line)
                if "%%01IFNET/4/IF_ENABLE" in line:
                    enable_counter += 1
                    last_prompt_seen = False
                elif "<HUAWEI>" in line:
                    if last_prompt_seen:
                        self.log("[+] Switch açıldı ve hazır.")
                        break
                    else:
                        last_prompt_seen = True
                else:
                    last_prompt_seen = False

    def read(self, size=4096):
        if self.ser.in_waiting:
            data = self.ser.read(size).decode(errors='ignore')
            self.log(data.strip())
            return data
        return ""

    def send_with_retry(self, command, retries=3, delay=5):
        for attempt in range(retries):
            self.send_line(command)
            self.send_enter()
            time.sleep(2)  # biraz cevap gelmesi için bekle
            response = self.read()
            if "Error: The system is busy" in response:
                self.log("[!] Sistem meşgul, tekrar deneniyor...")
                time.sleep(delay)
            else:
                self.log("[+] Komut başarıyla çalıştı.")
                return
        self.log("[HATA] Komut başarısız oldu: Sistem meşgul kalmaya devam etti.")


    def wait_for_prompt(self, keyword):
            self.log(f"[~] Bekleniyor: '{keyword}'")
            buffer = ""
            while True:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode(errors='ignore')
                    if line:
                        self.log(line.strip())
                        buffer += line
                        if keyword in line:
                            return buffer
                time.sleep(0.1)

    def check_initial_password_prompt(self, data):
        if "Continue to set it?" in data or "[Y/N]" in data:
            self.log("[~] Şifre belirleme ekranı algılandı, 'n' gönderiliyor...")
            self.send_line("n")
            time.sleep(1)
            return True
        return False

    def check_initial_password_prompt(self, data):
        """
        Eğer 'Continue to set it?' gibi bir şifre ayarlama isteği gelirse 'n' gönderir.
        """
        if "Continue to set it?" in data or "initial" in data:
            self.log("[~] Şifre belirleme isteği algılandı, 'n' gönderiliyor...")
            self.send_line("n")
            time.sleep(1)  # küçük bekleme süresi
            return True
        return False
    
    def read_output(self):
        if self.ser.in_waiting:
            return self.ser.read(self.ser.in_waiting).decode(errors="ignore")
        return ""
    
    def wait_for_response_or_prompt(self, timeout=10):
        buffer = ""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.ser.in_waiting:
                data = self.ser.read(self.ser.in_waiting).decode(errors="ignore")
                buffer += data
                self.log(data.strip())  # gelen tüm çıktı loglansın

                # Bazı cevaplar prompt içermese bile komutun tamamlandığını anlayabiliriz:
                if "]" in buffer or ">" in buffer or "#" in buffer or "has been" in buffer or "successfully" in buffer:
                    return
            time.sleep(1)
        self.log("[⚠️] Yanıt süresi aşıldı!")


    def send_config_file(self, filepath):
        self.log("[~] Config dosyası gönderiliyor...")
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        blocks = content.split("#")

        for i, block in enumerate(blocks):
            lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
            if not lines:
                continue

            self.log(f"[>>] Blok {i+1} gönderiliyor...")
            for line in lines:
                self.send_line(line)
                self.wait_for_response_or_prompt()  # zamanlamayı buna bırak

            self.send_enter()
            self.wait_for_response_or_prompt()
            self.log(f"[✓] Blok {i+1} başarıyla gönderildi.")

        self.log("[✓] Tüm config blokları başarıyla gönderildi.")



