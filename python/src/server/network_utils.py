import socket

class NetworkUtils:
    @classmethod
    def is_free_port(cls, host: str, port: int) -> bool:
        """
        Checks if a given port is free on the specified host.
        Note: There's still a potential race condition between this check
        and the actual binding of the port by a server.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return True
            except OSError:
                return False

    @classmethod
    def is_resolvable_hostname(cls, hostname: str) -> bool:
        """
        Checks if a given hostname can be resolved to an IP address.
        """
        try:
            socket.gethostbyname(hostname)
            return True
        except socket.gaierror:
            return False