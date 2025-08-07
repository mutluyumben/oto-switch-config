import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import serial.tools.list_ports
import threading
from config_generator import generate_config
from serial_manager import SerialManager
import time

class OtoConfigGUI:

    def handle_command_enter(self, event):
        cmd = self.command_entry.get().strip()
        if cmd:
            self.send_manual_command()  # Zaten ENTER içeriyor
        else:
            if self.serial_manager and self.serial_manager.ser:
                self.serial_manager.send_line("")  # ENTER gönder
                self.print_log(f"[MANUAL] <ENTER>")

    def __init__(self, root):
        self.root = root
        self.root.title("Aidata Oto-Config")
        self.root.iconbitmap("assets/logo.ico")
        self.serial_manager = None
        self.build_gui()

    def build_gui(self):
        self.root.geometry("900x650")
        form_frame = tk.LabelFrame(self.root, text="Giriş Bilgileri", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=5)

        self.entries = {}
        labels = ["Okul Adı", "Tesis Kodu", "IP Adresi", "Switch No"]
        for i, label in enumerate(labels):
            tk.Label(form_frame, text=label).grid(row=0, column=i * 2, sticky="e")
            entry = tk.Entry(form_frame, width=20)
            entry.grid(row=0, column=i * 2 + 1, padx=5)
            self.entries[label] = entry

        tk.Label(form_frame, text="Switch Türü").grid(row=1, column=0, sticky="e")
        self.switch_type = ttk.Combobox(
            form_frame,
            values=[
                "1 - 28 Port (Tip 1)",
                "2 - 28 Port (Tip 2)",
                "3 - 52 Port (Tip 3)",
                "4 - 52 Port (Tip 4)"
            ],
            state="readonly",
            width=25
        )
        self.switch_type.grid(row=1, column=1, padx=5)
        self.switch_type.current(0)

        tk.Label(form_frame, text="COM Port").grid(row=1, column=2, sticky="e")
        self.port_select = ttk.Combobox(form_frame, values=self.get_ports(), state="readonly", width=18)
        self.port_select.grid(row=1, column=3, padx=5)

        self.start_btn = tk.Button(form_frame, text="Bağlan ve Başlat", command=self.start_process, bg="green", fg="white")
        self.start_btn.grid(row=1, column=5, padx=10)

        self.show_config_button = tk.Button(form_frame, text="Configi Göster", command=self.send_show_config_sequence)
        self.show_config_button.grid(row=1, column=6, padx=5, pady=5)


        log_frame = tk.LabelFrame(self.root, text="Log Paneli", padx=10, pady=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_box = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20, bg="black", fg="lime", font=("Courier", 10))
        self.log_box.pack(fill="both", expand=True)

        terminal_frame = tk.LabelFrame(self.root, text="Manuel Komut Terminali", padx=10, pady=5)
        terminal_frame.pack(fill="x", padx=10, pady=5)

        self.command_entry = tk.Entry(terminal_frame, width=100)
        self.command_entry.pack(side="left", padx=5)
        self.command_entry.bind("<Return>", self.handle_command_enter)

        self.send_btn = tk.Button(terminal_frame, text="Gönder", command=self.send_manual_command)
        self.send_btn.pack(side="left", padx=5)

    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def print_log(self, message):
        self.log_box.insert(tk.END, f"{message}\n")
        self.log_box.see(tk.END)

    def send_manual_command(self):
        cmd = self.command_entry.get()
        if self.serial_manager and self.serial_manager.ser and cmd:
            self.serial_manager.send_line(cmd)
            self.print_log(f"[MANUAL] {cmd}")
            self.command_entry.delete(0, tk.END)

    def start_process(self):
        thread = threading.Thread(target=self.run_config_process)
        thread.daemon = True
        thread.start()

    def run_config_process(self):
        user_data = {
            "okul_adi": self.entries["Okul Adı"].get(),
            "tesis_kodu": self.entries["Tesis Kodu"].get(),
            "ip_adresi": self.entries["IP Adresi"].get(),
            "switch_no": self.entries["Switch No"].get(),
            "switch_turu": self.switch_type.get(),
            "serial_port": self.port_select.get()
        }

        if not all(user_data.values()):
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun.")
            return

        try:
            tur = int(user_data["switch_turu"].split()[0])
            port_haritasi = {1: 28, 2: 28, 3: 52, 4: 52}
            port_sayisi = port_haritasi.get(tur, 28)

            config_path = generate_config(user_data)
            self.serial_manager = SerialManager(port=user_data["serial_port"], 
            log_callback=self.print_log)
            self.serial_manager.gui_logger = self.print_log
            self.serial_manager.open()

            self.serial_manager.wait_for_boot_menu_or_password()
            self.serial_manager.send_line("Admin@huawei.com")

            self.serial_manager.wait_for_prompt("Enter your choice(1-8):")
            self.serial_manager.send_line("7")
            self.serial_manager.send_enter()

            self.serial_manager.wait_for_prompt("(Y/N)")
            self.serial_manager.send_line("y")
            self.serial_manager.send_enter()

            self.serial_manager.wait_for_prompt("Enter your choice(1-8):")
            self.serial_manager.send_line("1")
            self.serial_manager.send_enter()

            self.serial_manager.wait_for_prompt("Press ENTER to get started.")
            self.serial_manager.send_enter()

            buffer = ""
            while True:
                output = self.serial_manager.read_output()
                if output:
                    buffer += output
                    self.serial_manager.log(output.strip())

                    if self.serial_manager.check_initial_password_prompt(buffer):
                        buffer = ""  # yakaladıysan sıfırla
                        time.sleep(1)
                        break


            self.serial_manager.wait_for_last_port(port_sayisi)
            
            self.serial_manager.send_enter() 
            self.serial_manager.wait_for_prompt(">")
            self.serial_manager.send_with_retry("reset saved-configuration")

            self.serial_manager.send_enter()

            self.serial_manager.wait_for_prompt("[Y/N]:")
            self.serial_manager.send_line("y")
            self.serial_manager.send_enter()
            self.serial_manager.send_line("reboot")
            self.serial_manager.send_enter()
            self.serial_manager.wait_for_prompt("[Y/N]:")
            self.serial_manager.send_line("n")
            self.serial_manager.send_enter()
            self.serial_manager.wait_for_prompt("[Y/N]:")
            self.serial_manager.send_line("y")
            self.serial_manager.send_enter()
            
            self.serial_manager.wait_for_boot_menu_or_password()
            self.serial_manager.send_line("Admin@huawei.com")

            self.serial_manager.wait_for_prompt("Enter your choice(1-8):")
            self.serial_manager.send_line("7")
            self.serial_manager.send_enter()
            self.serial_manager.wait_for_prompt("(Y/N)")
            self.serial_manager.send_line("y")
            self.serial_manager.send_enter()

            self.serial_manager.wait_for_prompt("Enter your choice(1-8):")
            self.serial_manager.send_line("1")
            self.serial_manager.send_enter()

            self.serial_manager.wait_for_prompt("Press ENTER to get started.")
            self.serial_manager.send_enter()

            buffer = ""
            while True:
                output = self.serial_manager.read_output()
                if output:
                    buffer += output
                    self.serial_manager.log(output.strip())

                    if self.serial_manager.check_initial_password_prompt(buffer):
                        buffer = ""  # yakaladıysan sıfırla
                        time.sleep(1)
                        break
            
            time.sleep(3)
            self.serial_manager.send_enter()
            self.serial_manager.send_enter()
            self.serial_manager.send_config_file(config_path)
            self.print_log("[~] Konfigürasyon başarıyla yüklendi.")

            self.serial_manager.wait_for_prompt("]")

            # return ile çık
            self.serial_manager.send_line("return")
            self.print_log("[>>] return gönderildi, çıkılıyor...")
 
            self.serial_manager.wait_for_prompt(">") 
 
            self.serial_manager.send_line("save")
            self.serial_manager.wait_for_prompt("[Y/N]")
            self.serial_manager.send_line("y")
            self.serial_manager.wait_for_prompt("[Y/N]")
            self.serial_manager.send_line("y")

            self.serial_manager.wait_for_prompt(">" or "")
            self.print_log("[✓] Konfigürasyon başarıyla kaydedildi.")

            self.serial_manager.close()

        except Exception as e:
            self.print_log(f"[HATA] {str(e)}")

    def send_show_config_sequence(self):
        if not self.serial_manager or not self.serial_manager.ser:
            self.print_log("[HATA] Seri bağlantı bulunamadı.")
            return

        def run():
            try:
                self.print_log("[Başlatıldı] Config görüntüleme işlemi başlatılıyor...")

                self.serial_manager.wait_for_boot_menu_or_password()
                self.serial_manager.send_line("Admin@huawei.com")

                self.serial_manager.wait_for_prompt("Enter your choice(1-8):")
                self.serial_manager.send_line("7")
                self.serial_manager.send_enter()

                self.serial_manager.wait_for_prompt("(Y/N)")
                self.serial_manager.send_line("y")
                self.serial_manager.send_enter()

                self.serial_manager.wait_for_prompt("Enter your choice(1-8):")
                self.serial_manager.send_line("1")
                self.serial_manager.send_enter()

                self.serial_manager.wait_for_prompt("Press ENTER to get started.")
                self.serial_manager.send_enter()

                buffer = ""
                while True:
                    output = self.serial_manager.read_output()
                    if output:
                        buffer += output
                        self.serial_manager.log(output.strip())

                        if self.serial_manager.check_initial_password_prompt(buffer):
                            buffer = ""  # yakaladıysan sıfırla
                            time.sleep(1)
                            break

                self.serial_manager.wait_for_prompt(">", timeout=20)
                self.serial_manager.send_line("system-view")
                self.serial_manager.wait_for_prompt("]", timeout=5)
                self.serial_manager.send_line("display current-configuration")

                self.serial_manager.read_display_output_with_space_spam()

                self.print_log("[✓] Config gösterimi tamamlandı.")
            except Exception as e:
                self.print_log(f"[HATA] İşlem sırasında hata oluştu: {e}")

        threading.Thread(target=run).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = OtoConfigGUI(root)
    root.mainloop()