import socket
from django.core.mail.backends.smtp import EmailBackend

class IPv4EmailBackend(EmailBackend):
    """
    Custom EmailBackend that forces IPv4 connections.
    This resolves the '[Errno 101] Network is unreachable' issue on platforms
    like Railway that might not fully route IPv6 traffic for SMTP ports.
    """
    def open(self):
        if self.connection:
            return False

        original_getaddrinfo = socket.getaddrinfo

        def ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
            return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

        socket.getaddrinfo = ipv4_getaddrinfo
        try:
            return super().open()
        finally:
            socket.getaddrinfo = original_getaddrinfo
