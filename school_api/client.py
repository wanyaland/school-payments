import requests
class SchoolAPIClient:
    def __init__(self, conn):
        self.conn = conn
    def _headers(self):
        return {"Authorization": f"Bearer {self.conn.api_key}", "Accept": "application/json"}
    def get_by_provider_student_id(self, provider_student_id: str) -> dict | None:
        url = self.conn.base_url.rstrip("/") + self.conn.student_by_provider_id_path.format(provider_student_id=provider_student_id)
        r = requests.get(url, headers=self._headers(), timeout=self.conn.timeout_seconds)
        return r.json() if r.status_code == 200 else None