import os
import asyncio
import aiohttp
import psutil
from time import time
from ping3 import ping
from dotenv import load_dotenv

load_dotenv()

class HealthChecker:
    def __init__(self, parent):
        self.process_name = os.getenv("client_name")
        self.gw_port = int(os.getenv("Gateway_Port") or 0)
        self.hub_port = int(os.getenv("HUB_Port") or 0)
        self.hub_host = os.getenv("HUB_HOST")
        self.status = False
        self.measures = {"status": False, "ping_latency": 0, "packet_loss_count": 0, "timestamp": 0}
        self.measuredb = {key: [] for key in self.measures}
        self.maxSize = 60 * 5
        self.connection = (None, None, None, None)
        self.parent = parent

    def add_measure(self, measure):
        for key in measure:
            if len(self.measuredb[key]) >= self.maxSize:
                self.measuredb[key].pop(0)
            self.measuredb[key].append(measure[key])

    def get_measure_avg(self):
        _timestamp = self.measuredb["timestamp"]
        if not _timestamp:
            return {key: 0 for key in self.measuredb}
        
        ret_measure = {}
        for key in self.measuredb:
            measure = self.measuredb[key]
            if not measure:
                ret_measure[key] = 0
                continue
            if key == "status":
                ret_measure[key] = sum(1 for m in measure if m) / len(measure)
            elif key == "packet_loss_count":
                ret_measure[key] = sum(measure)
            else:
                ret_measure[key] = sum(measure) / len(measure) if measure else 0
        return ret_measure

    def get_active_connection(self):
        try:
            valid_pids = {
                p.info['pid']
                for p in psutil.process_iter(attrs=['pid', 'name'])
                if self.process_name in p.info['name'].lower()
            }
            if not valid_pids:
                return None, None, None, None

            for conn in psutil.net_connections(kind='tcp'):
                if conn.status == psutil.CONN_ESTABLISHED and conn.pid in valid_pids:
                    laddr, raddr = conn.laddr, conn.raddr
                    if laddr and raddr and raddr.port not in (self.gw_port, self.hub_port) and laddr.port not in (self.gw_port, self.hub_port):
                        if raddr.ip == "127.0.0.1":  # Yerel bağlantıları ignore et
                            continue
                        self.status = True
                        return laddr.ip, laddr.port, raddr.ip, raddr.port
            self.status = False
            return None, None, None, None
        except Exception as e:
            print(f"Error checking connection: {e}")
            self.status = False
            return None, None, None, None

    def check_connection(self):
        self.connection = self.get_active_connection()
        if not self.connection[0]:
            self.status = False
        self.measures["status"] = self.status

    async def update_measure(self):
        try:
            if self.connection[2]:
                ping_latency = ping(self.connection[2], timeout=2)
                if ping_latency is not None:
                    self.measures["ping_latency"] = ping_latency * 1000
                else:
                    self.measures["ping_latency"] = float('inf')
                    self.measures["packet_loss_count"] += 1
            else:
                print("No valid remote IP for ping")
                self.measures["ping_latency"] = float('inf')
            self.measures["status"] = self.status
            self.measures["timestamp"] = time()
        except Exception as e:
            print(f"update_measure error: {e}")
            self.measures["ping_latency"] = float('inf')
            self.measures["packet_loss_count"] += 1
            self.measures["status"] = self.status
            self.measures["timestamp"] = time()

    async def get_data_hub(self):
        print("Checking connection")  # Debug
        self.check_connection()
        print("Updating measure")  # Debug
        await self.update_measure()
        print("Adding measure")  # Debug
        self.add_measure(self.measures)
        print("Getting measure avg")  # Debug
        avg_measures = self.get_measure_avg()
        print("get_data_hub result:", avg_measures)  # Debug
        return avg_measures

    async def loop(self):
        print("HealthChecker Loop Started")
        while True:
            self.check_connection()
            await self.update_measure()
            self.add_measure(self.measures)
            avg_measures = self.get_measure_avg()
            await self.send_to_hub(avg_measures)
            print(f"Measures: {self.measures}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    HC = HealthChecker()
    asyncio.run(HC.loop())