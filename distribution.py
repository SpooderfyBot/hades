
class LiveServer:
    def __init__(
            self,
            id: str,
            rtmp_domain: str,
            control_domain: str,
    ):
        self.id = id
        self.control = f"https://{control_domain}"
        self.rtmp = f"rtmp://{rtmp_domain}/live"


class LiveServerManager:
    def __init__(self, default: LiveServer):
        self.default = default
        self.selectable_urls = {}

    def get(self, sub_domain=None) -> LiveServer:
        return self.selectable_urls.get(sub_domain, self.default)

    def add_server(self, server: LiveServer):
        self.selectable_urls[server.id] = server
