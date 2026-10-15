from __future__ import annotations
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import replace
from unittest.mock import patch
import os
import pytest
from devpilot_core.docs_governance.markdown_publication import GovernedMarkdownPublisher, MarkdownPublication
from devpilot_core.docs_governance.authority import DerivedMetadataProjection


def fixture(tmp):
    (tmp/'.devpilot/docs_governance').mkdir(parents=True)
    (tmp/'tests').mkdir()
    (tmp/'tests/test_document.py').write_text('pass\n')
    registry={'documents':[], 'summary':{}, 'registry_id':'test', 'schema_id':'DocumentationSourceRegistry'}
    graph={'nodes':[], 'graph_id':'test'}
    (tmp/'.devpilot/docs_governance/source_registry.json').write_text(json.dumps(registry))
    (tmp/'.devpilot/docs_governance/documentation_authority_graph.json').write_text(json.dumps(graph))
    (tmp/'.devpilot/docs_governance/rebaseline_p0_overlay.json').write_text(json.dumps({'authority':{'mp_registry_state':'PROGRAM_132_PUBLISHED/0_ENTRIES'}}))
    raw=(tmp/'.devpilot/docs_governance/source_registry.json').read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    req=MarkdownPublication('docs/published/architecture/sample.md','DOC-001','Owner',
           '---\ndoc_id: DOC-001\nstatus: approved\nowner: Owner\n---\n# Approved\nReal meaningful content.\n',('tests/test_document.py',),True)
    return req,digest


def test_preview_readonly(tmp_path):
    req,digest=fixture(tmp_path);p=GovernedMarkdownPublisher(tmp_path)
    before=(tmp_path/'.devpilot/docs_governance/source_registry.json').read_bytes()
    out=p.publish(req, expected_registry_sha256=digest)
    assert out['status']=='PREVIEW_APPROVED' and out['registry_documents']==1
    assert not (tmp_path/req.relative_path).exists()
    assert (tmp_path/'.devpilot/docs_governance/source_registry.json').read_bytes()==before


def test_published_and_reopened_all_three(tmp_path):
    req,digest=fixture(tmp_path);pub=GovernedMarkdownPublisher(tmp_path)
    assert pub.publish(req, expected_registry_sha256=digest, execute=True)['status']=='PUBLISHED'
    assert (tmp_path/req.relative_path).read_text().endswith('Real meaningful content.\n')
    registry=json.loads((tmp_path/'.devpilot/docs_governance/source_registry.json').read_text())
    graph=json.loads((tmp_path/'.devpilot/docs_governance/documentation_authority_graph.json').read_text())
    assert registry['documents'][0]['doc_id']==graph['nodes'][0]['doc_id']==req.doc_id
    assert registry['summary']['documents_total']==1
    assert json.loads((tmp_path/'.devpilot/docs_governance/rebaseline_p0_overlay.json').read_text())['authority']['mp_registry_state']=='PROGRAM_132_PUBLISHED/1_ENTRIES'
    assert not DerivedMetadataProjection.source_registry_mismatches(registry)
    newhash=hashlib.sha256((tmp_path/'.devpilot/docs_governance/source_registry.json').read_bytes()).hexdigest()
    assert pub.publish(req, expected_registry_sha256=newhash, execute=True)['status']=='NO_OP_ACCEPTED'


def test_unapproved_cannot_execute(tmp_path):
    req,digest=fixture(tmp_path);req=replace(req,approved=False)
    with pytest.raises(ValueError,match='APPROVAL_REQUIRED'):
        GovernedMarkdownPublisher(tmp_path).publish(req,expected_registry_sha256=digest,execute=True)
    assert not (tmp_path/req.relative_path).exists()

@pytest.mark.parametrize('path', ['docs/published/../other.md','docs/published/../../x.md',
      'docs/published/sub\\x.md','docs/published/x.txt','D:/docs/published/x.md',
      'docs/published/.git/x.md','docs/published//x.md','docs/published/x.md/'])
def test_path_denied(tmp_path,path):
    req,digest=fixture(tmp_path)
    with pytest.raises(ValueError):
        GovernedMarkdownPublisher(tmp_path).publish(replace(req,relative_path=path),expected_registry_sha256=digest)


def test_registry_drift_denied(tmp_path):
    req,digest=fixture(tmp_path)
    with pytest.raises(ValueError,match='REGISTRY_DRIFT'):
        GovernedMarkdownPublisher(tmp_path).publish(req,expected_registry_sha256='a'*64,execute=True)


def test_existing_different_never_overwritten(tmp_path):
    req,digest=fixture(tmp_path);destination=tmp_path/req.relative_path;destination.parent.mkdir(parents=True);destination.write_text('FROZEN')
    with pytest.raises(ValueError,match='EXISTING_PATH'):
        GovernedMarkdownPublisher(tmp_path).publish(req,expected_registry_sha256=digest,execute=True)
    assert destination.read_text()=='FROZEN'


def test_same_doc_id_other_path_denied(tmp_path):
    req,digest=fixture(tmp_path);pub=GovernedMarkdownPublisher(tmp_path)
    pub.publish(req,expected_registry_sha256=digest,execute=True)
    digest=hashlib.sha256((tmp_path/'.devpilot/docs_governance/source_registry.json').read_bytes()).hexdigest()
    with pytest.raises(ValueError,match='EXISTING_PATH'):
        pub.publish(replace(req,relative_path='docs/published/architecture/other.md'),expected_registry_sha256=digest,execute=True)


def test_missing_test_denied(tmp_path):
    req,digest=fixture(tmp_path)
    with pytest.raises(ValueError,match='REQUIRED_TEST_MISSING'):
        GovernedMarkdownPublisher(tmp_path).publish(replace(req,required_tests=('tests/missing.py',)), expected_registry_sha256=digest)


def test_frontmatter_mismatch_denied(tmp_path):
    req,digest=fixture(tmp_path)
    with pytest.raises(ValueError,match='METADATA_MISMATCH'):
        GovernedMarkdownPublisher(tmp_path).publish(replace(req,content=req.content.replace('status: approved','status: draft')),expected_registry_sha256=digest)


def test_symlink_denied(tmp_path):
    req,digest=fixture(tmp_path)
    (tmp_path/'docs/published').mkdir(parents=True)
    link = tmp_path/'docs/published/architecture'
    try:
        link.symlink_to(tmp_path, target_is_directory=True)
    except OSError as exc:
        # Windows without Developer Mode or SeCreateSymbolicLinkPrivilege:
        # exercise the same guard deterministically; do not drop security coverage.
        if os.name != 'nt' or getattr(exc, 'winerror', None) != 1314:
            raise
        original = Path.is_symlink
        with patch.object(Path, 'is_symlink', autospec=True,
                          side_effect=lambda self: self == link or original(self)):
            with pytest.raises(ValueError, match='SYMLINK'):
                GovernedMarkdownPublisher(tmp_path).publish(req, expected_registry_sha256=digest)
    else:
        with pytest.raises(ValueError, match='SYMLINK'):
            GovernedMarkdownPublisher(tmp_path).publish(req, expected_registry_sha256=digest)


def test_windows_junction_guard_without_admin_privileges(tmp_path):
    # Pure unit test for the reparse/junction check; no mklink or Windows privilege.
    req, digest = fixture(tmp_path)
    junction = tmp_path/'docs/published/architecture'
    original = Path.is_junction
    with patch.object(Path, 'is_junction', autospec=True,
                      side_effect=lambda self: self == junction or original(self)):
        with pytest.raises(ValueError, match='SYMLINK'):
            GovernedMarkdownPublisher(tmp_path).publish(req, expected_registry_sha256=digest)


def test_concurrent_lock_denied(tmp_path):
    req,digest=fixture(tmp_path)
    lock=tmp_path/'.devpilot/docs_governance/.r01_07_publication.lock';lock.write_text('other process')
    with pytest.raises(ValueError,match='CONCURRENT_LOCK'):
        GovernedMarkdownPublisher(tmp_path).publish(req,expected_registry_sha256=digest,execute=True)
    assert lock.read_text()=='other process'


def test_crlf_content_canonical(tmp_path):
    req,digest=fixture(tmp_path)
    req=replace(req,content=req.content.replace('\n','\r\n'))
    result=GovernedMarkdownPublisher(tmp_path).publish(req, expected_registry_sha256=digest,execute=True)
    assert result['status']=='PUBLISHED'
    assert b'\r\n' not in (tmp_path/req.relative_path).read_bytes()
