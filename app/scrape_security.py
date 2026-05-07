import ipaddress
import socket
from urllib.parse import urlparse


def validate_scrape_url(restaurant_url: str):
    parsed = urlparse(restaurant_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("restaurant_url must start with http:// or https://")
    reject_private_destination(parsed.hostname)
    return parsed


def reject_private_destination(hostname: str | None) -> None:
    if not hostname:
        raise ValueError("restaurant_url must include a hostname")
    try:
        addresses = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError("restaurant_url hostname could not be resolved") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
        ):
            raise ValueError("restaurant_url cannot target private or local networks")
