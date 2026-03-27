import asyncio
import aiohttp
import socket
import hashlib
from typing import Optional, Tuple, List


class auto_find_server:
    def __init__(self, concurrency: int = 10, timeout: int = 2, user_agent: str = "curl/7.0"):
        self.concurrency = concurrency
        self.timeout = timeout
        self.headers = {"User-Agent": user_agent}

    @staticmethod
    def get_local_ipv4() -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = socket.gethostbyname(socket.gethostname())
        finally:
            s.close()
        return ip

    async def fetch_hash(self, session: aiohttp.ClientSession, ip: str) -> Optional[Tuple[str, str, int]]:
        url = f"http://{ip}/server_found.php?iq=169"
        try:
            async with session.get(url, timeout=self.timeout) as resp:
                body = await resp.read()
                if not body:
                    return None
                result_decoded = body.decode().strip().split(":")
                h, port = result_decoded[0], result_decoded[1]
                return (ip, h, port)
        except Exception:
            return None

    async def scan_network(self, base: str, start: int = 1, stop: int = 255) -> List[Tuple[str, str, int]]:
        """
        Scans the given /24 network range asynchronously.
        Returns a list of (ip, sha256) tuples for all found servers.
        """
        sem = asyncio.Semaphore(self.concurrency)
   
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async def limited_fetch(ip: str):
                async with sem:
                    return await self.fetch_hash(session, ip)

            tasks = [asyncio.create_task(limited_fetch(f"{base}.{i}")) for i in range(start, stop)]
            for task in asyncio.as_completed(tasks):
                result = await task
                if result:
                    ip, sha, port = result
                    print(f"Server: {ip}:{port} : {sha}")
                    
                    return (ip, sha, port)  # Return immediately after finding the first server
        return None

    async def run(self, base: Optional[str] = None, start: int = 2, stop: int = 255) -> List[str]:
        """
        Determines network base if not provided, scans it,
        and returns a list of IPs where a server was found.
        """
        if base is None:
            local_ip = self.get_local_ipv4()
            print(f"Local IPv4 address detected: {local_ip}")
            parts = local_ip.split(".")
            if len(parts) != 4:
                raise SystemExit("Couldn't determine an IPv4 address.")
            base = ".".join(parts[:3])

        print(f"Scanning {base}.0/24 ... (range {start}-{stop-1}, concurrency={self.concurrency})")
        found = await self.scan_network(base, start=start, stop=stop)
        print("Scan complete.")
        return found  # only IPs


