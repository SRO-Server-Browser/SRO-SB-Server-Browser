import asyncio, itertools, os, dotenv, socket, aiohttp, json, time
import threading,random,ping3,hashlib
import traceback
import logging


# Loglama ayarları
logging.basicConfig(
    filename='hub.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

if __name__ != "__main__":
    from utils.helper import check_ping, create_message
    from core.HealthChecker import HealthChecker

random.seed(3131)

dotenv.load_dotenv()

class Gateway:
    def __init__(self, ip_list: list, gw_port: int, _hub):
        self.ip_list = ip_list
        self.target_port = gw_port
        self.server_cycle = itertools.cycle(ip_list)
        self.localIP = self.getLocalIP()
        self.lock = threading.Lock()
        self.GW_IP = os.getenv("Gateway_IP")
        self._Port = int(os.getenv("Gateway_Port"))
        self.HUB = _hub
        self.public_ip = None
        self.connection_counter = 0

    async def fetch_ip(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.ipify.org') as response:
                    self.public_ip = await response.text()
                    print(f"[INFO] Public IP alınan: {self.public_ip}")
        except Exception as e:
            print(f"[fetch_ip] IP alınamadı: {e}")
            self.public_ip = "0.0.0.0"

    def getLocalIP(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    async def forward(self, reader, writer):
        #peer_ip = writer.get_extra_info('peername')[0]
        while data := await reader.read(32):
            hex_data = data.hex()
            #print(peer_ip, hex_data)
            writer.write(data)
            await writer.drain()

    async def close_connection(self, writer):
        try:
            writer.close()
            await writer.wait_closed()
            print(writer.get_extra_info("peername"),f"Closed counter {self.connection_counter}")
        except:
            pass

    async def handle_client(self, reader, writer):
        _reader = _writer = None
        self.connection_counter += 1
        for attempt in range(25):
            host = next(self.server_cycle)
            port = self.target_port
            try:
                _reader, _writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=2.0
                )
                print(f"[FORWARD] Bağlandı: {host}:{port}")
                break
            except:
                print(f"[FORWARD] Attempt {attempt+1} başarısız: {host}:{port}")

        if not _reader:
            print("[FORWARD] Uygun sunucu bulunamadı.")
            return
        try:
            await asyncio.gather(
                self.forward(reader, _writer),
                self.forward(_reader, writer)
            )
        except:
            await self.close_connection(writer)
            await self.close_connection(_writer)
        self.connection_counter -= 1

    async def serve(self):
        self.server = await asyncio.start_server(self.handle_client, self.GW_IP, self._Port)
        addr = self.server.sockets[0].getsockname()
        print(f"[SERVER] Dinleniyor: {addr}")
        async with self.server:
            await self.server.serve_forever()

    async def start(self):
        print("[SYSTEM] Gateway başlatılıyor...")
        await self.fetch_ip()
        await self.serve()

class HUB:
    def __init__(self, ip, port):
        self.IP = ip
        self.port = int(port)
        self.GW = None
        self.identifier = None
        self.reader = None
        self.gw_loop = None
        self.gw_thread = None
        self.lock = threading.Lock()
        self.servers_cache = []
        self.loop = None
        self.health_checker = HealthChecker(self)
        self.write_lock = threading.Lock()
        self.console_callback = None

    async def listen_servers_broadcast(self):
        while True:
            try:
                data = await self.reader.read(2048)
                if not data:
                    await asyncio.sleep(0.5)
                    continue
                decoded = json.loads(data.decode())
                self.console_log(decoded)
                if decoded["data"]["type"] == "request" and decoded["data"]["value"] == "servers":
                    servers = decoded["data"]["data"]
                    if isinstance(servers, list):
                        for item in servers:
                            self.servers_cache.append(item)
                        self.console_log(f"[INFO] Servers güncellendi: {len(servers)} adet sunucu.")
                    else:
                        self.console_log("[WARNING] Geçersiz server listesi formatı.")
            except Exception as e:
                self.console_log(f"[ERROR] Broadcast dinleme hatası: {e}")
                await asyncio.sleep(3)

    def start_broadcast_listener(self):
        def thread_target():
            if not self.loop:
                raise RuntimeError("Event loop henüz ayarlanmadı. 'startHUB()' tamamlanmalı.")
            loop = self.loop
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.listen_servers_broadcast())

        threading.Thread(target=thread_target, daemon=True).start()

    def set_console_callback(self, callback):
        """GUI konsoluna mesaj göndermek için callback ayarla."""
        self.console_callback = callback
        
    def scanServer(self):
        if len(self.servers_cache) > 1:
            return self.servers_cache.pop(0)
        return None

    def console_log(self, message):
        """Konsola, log dosyasına ve GUI’ye mesaj gönder."""
        print(message, flush=True)
        logging.info(message)
        if self.console_callback:
            try:
                self.console_callback(f"{message}\n")
            except Exception as e:
                print(f"[ERROR] GUI log hatası: {e}", flush=True)
                
    def write_thread(self, package):
        """Veriyi ayrı bir thread'de thread-safe şekilde gönderir."""
        def thread_target():
            self.console_log(f"[DEBUG] write_thread çağrıldı: {package['data']['type']} (Thread ID: {threading.get_ident()})")
            if not self.loop:
                self.console_log("[ERROR] Event loop başlatılmadı")
                return
            try:
                self.console_log(f"[DEBUG] Loop durumu: Çalışıyor mu: {self.loop.is_running()}, Kapalı mı: {self.loop.is_closed()}")
                future = asyncio.run_coroutine_threadsafe(self.write(package), self.loop)
                future.result()
                self.console_log(f"[DEBUG] write_thread tamamlandı: {package['data']['type']}")
            except Exception as e:
                self.console_log(f"[ERROR] Thread-safe yazma hatası: {e}\n{traceback.format_exc()} (Paket: {package['data']['type']})")
        
        threading.Thread(target=thread_target, daemon=True).start()
    
    def joinServer(self, server, username, password):
        username = username.strip()
        password = password.strip()
        ip = self.public_ip
        if username == "" or password == "":
            username = "unknown"
        else:
            password = hashlib.md5(password.encode()).hexdigest()
        try:
            ping = check_ping(server["IP"])
        except:
            print("Ping Error with ",server["IP"])
            ping = 50
        package = {
                    "id": self.identifier,
                    "data": {"type": "join", "target":server["ID"], "ping":ping, "username":username,"password":password,"ip":ip},
                    "timestamp": time.time()
                    }
        self.write_thread(package)

    async def inform_health(self):
        try:
            if not self.identifier:
                print("No identifier, skipping inform_health")
                return
            _package = await self.health_checker.get_data_hub()
            package = create_message(self.identifier, "info", _package)
            self.write_thread(package)
        except Exception as e:
            print("Health Check Error:", e, type(e))

    def check_connection(self):
        with self.lock:
            if self.reader:
                return True
            return False
    
    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.IP, self.port)
            print("HUB Connected")
            if self.reader:
                await self.handshake()
                return True
        except Exception as e:
            self.reader = self.writer = None
            print("HUB Not Connected ",e)
            return False

    async def read(self):
        return await self.reader.read(1024)

    async def write(self, package):
        """Veri yazar."""
        with self.write_lock:  # Yazma işlemlerini senkronize et
            try:
                self.console_log(f"[DEBUG] write çağrıldı: {package['data']['type']} (Paket: {package})")
                if not self.check_connection():
                    self.console_log("[WARNING] Bağlantı yok, yeniden bağlanılıyor...")
                    await self.connect()
                    if not self.check_connection():
                        raise ValueError("Bağlantı sağlanamadı")
                self.console_log(f"[DEBUG] Writer durumu: {self.writer}, Kapalı mı: {self.writer.is_closing()}")
                package_data = json.dumps(package).encode() + b'\n'  # Yeni satır ayırıcısı ekle
                self.console_log("[DEBUG] Veri yazılıyor...")
                self.writer.write(package_data)
                await asyncio.wait_for(self.writer.drain(), timeout=5)
                self.console_log(f"[INFO] Veri gönderildi: {package['data']['type']}")
            except Exception as e:
                self.console_log(f"[ERROR] Veri yazma hatası: {e}\n{traceback.format_exc()}")
                self.reader = self.writer = None
                raise
        
    async def heartbeat(self):
        while True:
            await asyncio.sleep(10)  # Her 10 saniyede bir
            if self.writer and self.identifier:
                try:
                    package = {
                        "id": self.identifier,
                        "data": {"type": "Heartbeat"},
                        "timestamp": time.time()
                    }
                    await self.write(package)
                except Exception as e:
                    print(f"[HUB] Heartbeat gönderilemedi: {e}")
                    
    async def handshake(self):
        data = await self.read()
        if data:
            self.identifier = data.decode()
        else:
            return
        package = {
            "id": self.identifier,
            "data": {
                "type": "Client",
                "client_ip": self.public_ip,
                "client_port": self.port
            },
            "timestamp": time.time()
        }
        await self.write(package)
        
    async def fetch_ip(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.ipify.org') as response:
                    self.public_ip = await response.text()
                    print(f"[INFO] Public IP alınan: {self.public_ip}")
        except Exception as e:
            print(f"[fetch_ip] IP alınamadı: {e}")
            self.public_ip = "0.0.0.0"
    
    def startGateWay(self, iplist, port):
        def runner():
            self.gw_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.gw_loop)
            self.GW = Gateway(iplist, port, self)
            self.gw_loop.run_until_complete(self.GW.start())

        self.gw_thread = threading.Thread(target=runner, daemon=True)
        self.gw_thread.start()
        return self.GW
    
    async def start(self):
        await self.fetch_ip()
        while not self.check_connection():
            await self.connect()

if __name__ == "__main__":
    Server_GWIPs = [
    'gateway1.kguardedge.com',
    'gateway2.kguardedge.com',
    'gateway3.kguardedge.com',
    'gateway4.kguardedge.com',
    'gateway5.kguardedge.com',
    'gateway6.kguardedge.com',
    'gateway7.kguardedge.com',
    'gateway8.kguardedge.com',
    ]
    Server_GWPort = 13304
    GW = Gateway(Server_GWIPs, Server_GWPort, None)
    asyncio.run(GW.start())