from pathlib import Path
from fastapi.testclient import TestClient
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.interfaces.api.uoc011_hardening import FixedWindowRateLimiter

ROOT=Path(__file__).resolve().parents[1]

def test_uoc011_security_headers_and_size_limit() -> None:
    client=TestClient(create_app(ROOT, api_token='uoc011-token'))
    headers={'X-DevPilot-Token':'uoc011-token','Origin':'http://127.0.0.1:5173'}
    response=client.get('/api/v1/security/posture',headers=headers)
    assert response.status_code==200
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
    assert response.headers['x-frame-options']=='DENY'
    assert response.headers['cache-control']=='no-store'
    assert response.headers['x-devpilot-uoc011-hardening']=='csp+size+rate+cache'
    blocked=client.post('/api/v1/approvals/request',headers={**headers,'Content-Length':str(1_048_577)},content=b'{}')
    assert blocked.status_code==413
    assert 'API_REQUEST_BODY_SIZE_BLOCK' in blocked.text

def test_uoc011_rate_limiter_is_deterministic() -> None:
    limiter=FixedWindowRateLimiter()
    assert limiter.consume('k',limit=2,window_seconds=60,now=1.0)[0] is True
    assert limiter.consume('k',limit=2,window_seconds=60,now=2.0)[0] is True
    allowed,remaining,retry=limiter.consume('k',limit=2,window_seconds=60,now=3.0)
    assert allowed is False and remaining==0 and retry>0
    assert limiter.consume('k',limit=2,window_seconds=60,now=62.0)[0] is True
