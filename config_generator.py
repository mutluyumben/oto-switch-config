def generate_config(user_data):
    template_path = f"templates/switch_type_{user_data['switch_turu']}.txt"

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Değiştirilecek alanlar
    sysname = f"{user_data['tesis_kodu']}-{user_data['okul_adi']}-{user_data['switch_no']}"
    ip_address = user_data['ip_adresi']

    # Yerine koy
    template = template.replace("sysname <TesisKodu-OkulAdı-SWNo>", f"sysname {sysname}")
    template = template.replace("ip address 10.x.x.x 255.255.255.x", f"ip address {ip_address} 255.255.255.0")
    template = template.replace("ip route-static 0.0.0.0 0.0.0.0 10.x.x.x", f"ip route-static 0.0.0.0 0.0.0.0 {ip_address}")

    # Çıktı dosyasını kaydet
    output_path = f"generated_config_{user_data['switch_no']}.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(template)

    print(f"[+] Config dosyası oluşturuldu: {output_path}")
    return output_path
