from __future__ import annotations

import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.schemas import SchemaValidator


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def _canonical_hash(payload: Any) -> str:
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _p95(values: list[float]) -> float:
    if not values: return 0.0
    s=sorted(values); idx=max(0, math.ceil(.95*len(s))-1); return float(s[idx])

@dataclass(frozen=True)
class IngestionResult:
    accepted: int
    rejected: int
    duplicate_receipt: bool
    source_hash: str
    environment_fingerprint: str


class NodeDurationRegistry:
    """Versioned duration history keyed by exact pytest nodeid + environment fingerprint.

    This component never schedules or executes tests. It only ingests immutable telemetry,
    derives robust estimates, and exposes deterministic previews for FRX-v2.2-C.
    """
    schema_id='devpilot.testing.node_duration_registry.v1'
    version='1.0.0'

    def __init__(self, root: Path, *, registry_path: Path | None=None) -> None:
        self.root=Path(root).resolve()
        self.path=registry_path or self.root/'.devpilot/testing/node_duration_registry.json'

    def empty(self) -> dict[str,Any]:
        return {'schema_id':self.schema_id,'version':self.version,'updated':_now(),'scheduler_enabled':False,'parallel_workers':1,'aging_policy':{'method':'sequential_ewma','alpha':0.35,'older_observations_lose_geometric_weight':True,'evidence_deleted':False},'ingested_receipts':{},'environments':{},'rejections':[]}

    def load(self) -> dict[str,Any]:
        if not self.path.exists(): return self.empty()
        return json.loads(self.path.read_text(encoding='utf-8'))

    def save(self, data: dict[str,Any]) -> None:
        self.path.parent.mkdir(parents=True,exist_ok=True)
        data['updated']=_now()
        self.path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')

    def ingest_payload(self, payload: dict[str,Any], *, environment_fingerprint: str | None=None, source_receipt: str='inline') -> IngestionResult:
        data=self.load(); samples=list(payload.get('samples') or [])
        env=str(environment_fingerprint or payload.get('environment_fingerprint') or '').strip()
        if not env: raise ValueError('environment_fingerprint is required')
        source_hash=_canonical_hash(payload)
        receipt_key=hashlib.sha256(f'{source_receipt}|{source_hash}|{env}'.encode()).hexdigest()
        if receipt_key in data['ingested_receipts']:
            return IngestionResult(0,0,True,source_hash,env)
        env_data=data['environments'].setdefault(env,{'nodes':{},'samples_total':0})
        accepted=0; rejected=0
        for i,item in enumerate(samples):
            nodeid=item.get('nodeid'); duration=item.get('duration_seconds')
            reason=None
            if not isinstance(nodeid,str) or not nodeid or '::' not in nodeid: reason='invalid_nodeid'
            try: dur=float(duration)
            except (TypeError,ValueError): dur=-1; reason=reason or 'invalid_duration'
            if not math.isfinite(dur) or dur < 0: reason=reason or 'invalid_duration'
            if reason:
                rejected+=1; data['rejections'].append({'source_receipt':source_receipt,'sample_index':i,'nodeid':nodeid,'reason':reason}); continue
            rec=env_data['nodes'].setdefault(nodeid,{'samples':[]})
            rec['samples'].append({'duration_seconds':round(dur,6),'observed_at':str(item.get('observed_at') or payload.get('generated_at') or _now()),'outcome':str(item.get('outcome') or 'UNKNOWN'),'source_receipt':str(item.get('source_receipt') or source_receipt)})
            self._derive(rec); accepted+=1
        env_data['samples_total']+=accepted
        data['ingested_receipts'][receipt_key]={'source_receipt':source_receipt,'source_hash':source_hash,'environment_fingerprint':env,'accepted':accepted,'rejected':rejected,'ingested_at':_now()}
        self.save(data)
        return IngestionResult(accepted,rejected,False,source_hash,env)

    def ingest_file(self, path: Path, *, environment_fingerprint: str | None=None) -> IngestionResult:
        p=Path(path).resolve()
        payload=json.loads(p.read_text(encoding='utf-8'))
        try:
            source_receipt=p.relative_to(self.root).as_posix()
        except ValueError:
            source_receipt=p.as_posix()
        return self.ingest_payload(payload,environment_fingerprint=environment_fingerprint,source_receipt=source_receipt)

    @staticmethod
    def _derive(rec: dict[str,Any]) -> None:
        vals=[float(x['duration_seconds']) for x in rec['samples']]
        ewma=vals[0]
        alpha=.35
        for v in vals[1:]: ewma=(alpha*v)+((1-alpha)*ewma)
        rec.update({'sample_count':len(vals),'median':round(float(statistics.median(vals)),6),'p95':round(_p95(vals),6),'robust_estimate':round(float(statistics.median(vals) if len(vals)<3 else ewma),6),'min':round(min(vals),6),'max':round(max(vals),6),'last_seen':rec['samples'][-1]['observed_at'],'classification':'warm' if len(vals)>=3 else 'cold','confidence':'high' if len(vals)>=5 else ('medium' if len(vals)>=3 else 'low')})

    def estimate(self, nodeid: str, environment_fingerprint: str) -> dict[str,Any]:
        data=self.load(); rec=((data.get('environments') or {}).get(environment_fingerprint) or {}).get('nodes',{}).get(nodeid)
        if not rec:
            return {'nodeid':nodeid,'environment_fingerprint':environment_fingerprint,'known':False,'estimate_seconds':None,'classification':'unknown','fallback':'stable-nodeid-order/count-char-bounds'}
        return {'nodeid':nodeid,'environment_fingerprint':environment_fingerprint,'known':True,'estimate_seconds':rec['robust_estimate'],'sample_count':rec['sample_count'],'median':rec['median'],'p95':rec['p95'],'classification':rec['classification'],'confidence':rec['confidence'],'last_seen':rec['last_seen']}

    def validate_schema(self, payload: dict[str,Any] | None = None):
        """Validate the complete duration registry JSON Schema."""
        validator=SchemaValidator(self.root)
        if payload is None:
            return validator.validate(schema='NodeDurationRegistry',instance=self.path)
        return validator.validate_payload(schema='NodeDurationRegistry',payload=payload,instance_label=self.path.as_posix())

    def status(self) -> dict[str,Any]:
        data=self.load(); envs=data.get('environments') or {}
        return {'schema_id':data.get('schema_id'),'version':data.get('version'),'environments_total':len(envs),'nodeids_total':sum(len(v.get('nodes') or {}) for v in envs.values()),'samples_total':sum(int(v.get('samples_total') or 0) for v in envs.values()),'rejections_total':len(data.get('rejections') or []),'ingested_receipts_total':len(data.get('ingested_receipts') or {}),'scheduler_enabled':bool(data.get('scheduler_enabled')),'parallel_workers':int(data.get('parallel_workers') or 1)}

    def preview(self, environment_fingerprint: str, *, limit: int=20) -> dict[str,Any]:
        data=self.load(); nodes=((data.get('environments') or {}).get(environment_fingerprint) or {}).get('nodes',{})
        ranked=sorted(({'nodeid':k,**{x:v[x] for x in ('robust_estimate','median','p95','sample_count','classification','confidence')}} for k,v in nodes.items()),key=lambda x:(-x['robust_estimate'],x['nodeid']))
        return {'environment_fingerprint':environment_fingerprint,'scheduler_enabled':False,'parallel_workers':1,'nodes_total':len(nodes),'slowest':ranked[:max(1,min(limit,100))]}
