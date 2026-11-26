import socket
import struct
import random
import base64
import threading
import time
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

STUN_SERVERS = [
    ("stun.l.google.com", 19302),
    ("stun1.l.google.com", 19302),
    ("74.125.250.129", 19302),
]



def get_local_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip, _ = s.getsockname()
        s.close()
        return ip
    except Exception:
        return None


def try_upnp_forward_udp(internal_port, external_port, desc="SoulLinkHub P2P"):
    lan_ip = get_local_lan_ip()
    if not lan_ip:
        return False, "No LAN IP"

    ssdp_req = (
        "M-SEARCH * HTTP/1.1\r\n"
        "HOST: 239.255.255.250:1900\r\n"
        "MAN: \"ssdp:discover\"\r\n"
        "MX: 2\r\n"
        "ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1\r\n\r\n"
    ).encode("utf-8")

    location_url = None
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(1.5)
    try:
        sock.sendto(ssdp_req, ("239.255.255.250", 1900))
        for _ in range(5):
            data, _ = sock.recvfrom(4096)
            text = data.decode("utf-8", errors="ignore")
            for line in text.splitlines():
                if line.lower().startswith("location:"):
                    _, loc_val = line.split(":", 1)
                    location_url = loc_val.strip()
                    break
            if location_url:
                break
    except Exception:
        pass
    finally:
        sock.close()

    if not location_url:
        return False, "UPnP router not found"

    try:
        xml_bytes = urllib.request.urlopen(location_url, timeout=2.0).read()
        root = ET.fromstring(xml_bytes)
        control_url = None
        service_type = None
        for srv in root.iter():
            if srv.tag.endswith("service"):
                stype = ""
                curl = ""
                for child in srv:
                    if child.tag.endswith("serviceType"):
                        stype = (child.text or "").strip()
                    elif child.tag.endswith("controlURL"):
                        curl = (child.text or "").strip()
                if "WANIPConnection" in stype or "WANPPPConnection" in stype:
                    service_type = stype
                    control_url = urllib.parse.urljoin(location_url, curl)
                    break

        if not control_url or not service_type:
            return False, "UPnP WAN service unavailable"

        soap_body = f"""<?xml version="1.0"?>
<s:Envelope xmlns:s="http://xmlsoap.org" s:encodingStyle="http://xmlsoap.org">
  <s:Body>
    <u:AddPortMapping xmlns:u="{service_type}">
      <NewRemoteHost></NewRemoteHost>
      <NewExternalPort>{external_port}</NewExternalPort>
      <NewProtocol>UDP</NewProtocol>
      <NewInternalPort>{internal_port}</NewInternalPort>
      <NewInternalClient>{lan_ip}</NewInternalClient>
      <NewEnabled>1</NewEnabled>
      <NewPortMappingDescription>{desc}</NewPortMappingDescription>
      <NewLeaseDuration>0</NewLeaseDuration>
    </u:AddPortMapping>
  </s:Body>
</s:Envelope>""".encode("utf-8")

        req = urllib.request.Request(
            control_url,
            data=soap_body,
            headers={
                "Content-Type": 'text/xml; charset="utf-8"',
                "SOAPAction": f'"{service_type}#AddPortMapping"',
            },
        )
        urllib.request.urlopen(req, timeout=2.0).read()
        return True, f"UPnP UDP {external_port} -> {lan_ip}:{internal_port}"
    except Exception as e:
        return False, f"UPnP blocked ({type(e).__name__})"


def discover_public_endpoint(udp_sock):
    old_timeout = udp_sock.gettimeout()
    udp_sock.settimeout(1.5)
    try:
        for host, port in STUN_SERVERS:
            try:
                txn_id = bytes(random.getrandbits(8) for _ in range(12))
                req = struct.pack("!HHI12s", 0x0001, 0, 0x2112A442, txn_id)
                udp_sock.sendto(req, (host, port))
                data, _ = udp_sock.recvfrom(2048)
                if len(data) < 20:
                    continue
                msg_type, msg_len, magic, resp_txn = struct.unpack("!HHI12s", data[:20])
                if msg_type != 0x0101 or resp_txn != txn_id:
                    continue
                idx = 20
                while idx + 4 <= len(data):
                    attr_type, attr_len = struct.unpack("!HH", data[idx:idx + 4])
                    val = data[idx + 4:idx + 4 + attr_len]
                    if attr_type == 0x0020 and len(val) >= 8:
                        _, family, raw_xport, raw_xip = struct.unpack("!BBHI", val[:8])
                        if family == 0x01:
                            xport = raw_xport ^ 0x2112
                            xip = raw_xip ^ 0x2112A442
                            return socket.inet_ntoa(struct.pack("!I", xip)), xport
                    elif attr_type == 0x0001 and len(val) >= 8:
                        _, family, xport = struct.unpack("!BBH", val[:4])
                        if family == 0x01:
                            return socket.inet_ntoa(val[4:8]), xport
                    idx += 4 + ((attr_len + 3) & ~3)
            except Exception:
                continue
    finally:
        udp_sock.settimeout(old_timeout)

    # Fallback: fetch public IP via HTTPS and use local bound UDP port for UPnP mapping
    try:
        pub_ip = urllib.request.urlopen("https://ipify.org", timeout=2.5).read().decode("utf-8").strip()
        socket.inet_aton(pub_ip)
        _, local_port = udp_sock.getsockname()
        return pub_ip, local_port
    except Exception:
        return None, None



def encode_room_code(ip, port):
    raw = socket.inet_aton(ip) + struct.pack("!H", int(port))
    return "SL-" + base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_room_code(code):
    code = code.strip()
    if ":" in code and not code.upper().startswith("SL-"):
        ip_part, port_part = code.rsplit(":", 1)
        socket.inet_aton(ip_part.strip())
        return ip_part.strip(), int(port_part.strip())
    if code.upper().startswith("SL-"):
        code = code[3:]
    pad = "=" * ((4 - len(code) % 4) % 4)
    raw = base64.urlsafe_b64decode(code + pad)
    if len(raw) != 6:
        raise ValueError("Invalid room code length")
    ip = socket.inet_ntoa(raw[:4])
    (port,) = struct.unpack("!H", raw[4:6])
    return ip, port


class StunUdpPeer:
    def __init__(self, on_message_cb, on_status_cb):
        self.on_message = on_message_cb
        self.on_status = on_status_cb
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", 0))
        self.sock.settimeout(0.5)
        _, self.local_port = self.sock.getsockname()

        self.public_ip, self.public_port = discover_public_endpoint(self.sock)
        self.upnp_active = False
        self.upnp_note = ""

        if self.public_ip and self.public_port:
            ok, note = try_upnp_forward_udp(self.local_port, self.public_port)
            self.upnp_active = ok
            self.upnp_note = note
            self.local_code = encode_room_code(self.public_ip, self.public_port)
        else:
            self.local_code = ""

        self.peer_addr = None
        self.connected = False
        self.running = True
        self.last_recv = 0.0

        threading.Thread(target=self._recv_loop, daemon=True).start()
        threading.Thread(target=self._punch_loop, daemon=True).start()

    def set_peer_code(self, code):
        ip, port = decode_room_code(code)
        self.peer_addr = (ip, port)
        self.connected = False
        self.last_recv = time.time()
        self.on_status(f"Punching NAT to {ip}:{port}...")

    def send_json(self, obj):
        if not self.peer_addr:
            return
        try:
            payload = json.dumps(obj, separators=(",", ":")).encode("utf-8")
            self.sock.sendto(b"MSG:" + payload, self.peer_addr)
        except Exception:
            pass

    def _punch_loop(self):
        while self.running:
            if self.peer_addr:
                try:
                    self.sock.sendto(b"PUNCH", self.peer_addr)
                except Exception:
                    pass
            if self.connected and (time.time() - self.last_recv > 30.0):
                self.connected = False
                self.on_status("Connection idle — re-punching NAT...")
            time.sleep(0.5)

    def _recv_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(65535)
                if not data:
                    continue
                if self.peer_addr != addr:
                    self.peer_addr = addr
                self.last_recv = time.time()
                if data == b"PUNCH":
                    try:
                        self.sock.sendto(b"PONG", addr)
                    except Exception:
                        pass
                if not self.connected:
                    self.connected = True
                    peer_ip, peer_port = addr
                    self.on_status(f"P2P Connected ({peer_ip}:{peer_port})")
                if data.startswith(b"MSG:"):
                    msg = json.loads(data[4:].decode("utf-8"))
                    self.on_message(msg)
            except socket.timeout:
                continue
            except Exception:
                continue
