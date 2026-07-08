
import base64
import json
import hmac
import hashlib
from urllib.parse import urlparse, parse_qsl, unquote


class Signature:

    B64_SECRET = "QITQBCVRgQ9uiybRXQ9P2t+UkenqHS/YpyHqMTBOfWZeN9NEjxjIkQC5agvsq5KTjDHmChvrKlpydYTU1mRMlA=="
    SECRET = base64.b64decode(B64_SECRET)

    def _normalize_url(self, url_str: str) -> str:
        parsed = urlparse(url_str)
        path_segments = [seg for seg in parsed.path.split("/") if seg]
        query_params = parse_qsl(parsed.query, keep_blank_values=True)

        normalized_params = []
        for name, value in query_params:
            if name:
                normalized_params.append((name.lower(), value.lower()))
        normalized_params.sort(key=lambda x: (x[0], x[1]))

        rebuilt_path = "/" + "/".join(path_segments) if path_segments else ""
        if normalized_params:
            query_string = "&".join(f"{k}={v}" for k, v in normalized_params)
            rebuilt_uri = f"{rebuilt_path}?{query_string}"
        else:
            rebuilt_uri = rebuilt_path

        return unquote(rebuilt_uri).lower()

    def gen_signature_headers(self, url: str, body = None) -> dict:
        normalized_url = self._normalize_url(url)

        combined_bytes = bytearray(normalized_url.encode("utf-8"))
        if body is not None:
            body_str = json.dumps(body, separators=(",", ":"))
            combined_bytes.extend(body_str.encode("utf-8"))

        signature_bytes = hmac.new(self.SECRET, combined_bytes, hashlib.sha256).digest()
        signature_b64 = base64.b64encode(signature_bytes).decode("utf-8")

        return {"Signature": signature_b64, "KeyVersion": "1"}
