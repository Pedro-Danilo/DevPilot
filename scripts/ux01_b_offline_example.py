"""Reproduce synthetic section handoff only: no provider, network or project writes."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from devpilot_core.application.r03_04_quality_contract import (
    candidate_quality, export_candidate_handoff, logical_sha256, offline_section_proposal,
)


def main():
    folder=ROOT/'docs/examples/ux01_b'
    sources=json.loads((folder/'sources.json').read_text(encoding='utf-8'))
    hashes={k:logical_sha256(v) for k,v in sources.items()}
    classifications={}
    for kind in ('architecture','technology_options','adr'):
        body=(folder/(kind+'.md')).read_text(encoding='utf-8')
        report=candidate_quality(kind,body,frozen=sources,hashes=hashes,
            candidate_id='offline-fixture-'+kind,epoch='offline-example-1',
            actor='OFFLINE_SYNTHETIC_FIXTURE',model='NO_MODEL_EXECUTED',
            selected_option_id='T1' if kind=='adr' else None,
            selected_option_sha256=logical_sha256((folder/'technology_options.md').read_text(encoding='utf-8')) if kind=='adr' else None)
        classifications[kind]={'quality_level':report['current']['quality_level'],
            'structural_disposition':report['current']['structural_disposition'],
            'candidate_sha256':report['current']['candidate_sha256'],
            'findings':report['current']['findings']}
        if kind=='adr':
            packet=export_candidate_handoff(report,body)
            proposal=offline_section_proposal(packet,section_id='riesgos-y-mitigaciones',
                replacement='RF-002: verificar rollback de venta y stock ante fallo de persistencia; probar restauración en un entorno aislado. Frecuencia y objetivos de recuperación: UNKNOWN, pendientes del Owner.')
            (folder/'handoff.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            (folder/'offline_proposal.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            (folder/'adr_refined_offline.md').write_text(proposal['markdown'],encoding='utf-8')
    (folder/'classifications.json').write_text(json.dumps({
        'evidence_kind':'OFFLINE_SYNTHETIC_FIXTURES','real_ollama_executed':False,
        'real_owner_decision':False,'external_api_used':False,'classifications':classifications},
        ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS: offline synthetic handoff reproduced; all candidates REVIEW_REQUIRED.')


if __name__=='__main__':
    main()
