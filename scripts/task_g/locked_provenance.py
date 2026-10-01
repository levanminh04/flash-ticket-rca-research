"""G33 bounded shards and complete durable verification before any truth read.

Preparation and final have different fixed host keys/domains. Neither a helper
payload nor the preparation key can issue a final seal. This is a trusted-host
boundary, not a process sandbox or independent cryptographic attestation.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import math
import os
import re
from pathlib import Path
import secrets

from scripts.task_g import final_provenance as bridge

W = Path(__file__).resolve().parents[2]
P = Path('D:/Project/flash-ticket-platform')
RUN_ID = 'g33-locked-final-campaign'
ROOT = W / 'results/task-g' / RUN_ID
CONTRACT = ROOT / 'run-contract.json'
PREP_DOMAIN = 'FlashTicketRca/TD13/G33/PREPARATION/v1'
FINAL_DOMAIN = 'FlashTicketRca/TD13/G33/FINAL/v1'
PREP_PHASE = 'G33_PREPARATION_ONLY'
FINAL_PHASE = 'G33_FINAL_CAMPAIGN'
MAX_FRAME = 4 * 1024 * 1024
MAX_INPUT = 16 * 1024 * 1024
MAX_HYDRATE = 64 * 1024 * 1024
SOURCES = tuple(f'{folder}/{prefix}locked_{name}.py'
                for folder, prefix in (('scripts/task_g', ''), ('tests/task_g', 'test_'))
                for name in ('campaign', 'provenance', 'evaluation'))
_canonical = bridge._canonical
_digest = bridge._digest
Error = bridge.FinalProvenanceError


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Error('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def decode(raw):
    try:
        value = json.loads(raw, object_pairs_hook=_pairs,
                           parse_constant=lambda value: (_ for _ in ()).throw(Error('NONFINITE_JSON')))
    except (ValueError, UnicodeDecodeError) as exc:
        raise Error('MALFORMED_JSON') from exc
    if _canonical(value) != raw:
        raise Error('NONCANONICAL_JSON')
    return value


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def exclusive(path, value):
    path = Path(path)
    bridge._require_regular_path(path, allow_missing=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = _canonical(value)
    with path.open('xb') as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    if path.read_bytes() != encoded:
        raise Error('DURABLE_READBACK_DIFFERS')
    return {'path': path.relative_to(W).as_posix(), 'sha256': hashlib.sha256(encoded).hexdigest(),
            'bytes': len(encoded)}


def key_path(final=False):
    base = os.environ.get('LOCALAPPDATA')
    if not base or not Path(base).is_absolute():
        raise Error('HOST_KEY_BASE_UNAVAILABLE')
    return Path(base) / 'FlashTicketRca/task-g-trust' / RUN_ID / ('final' if final else 'preparation') / 'issuer.key'


def anchor(final=False):
    path = key_path(final)
    bridge._require_regular_path(path)
    if path.stat().st_size != 32:
        raise Error('HOST_KEY_LENGTH_INVALID')
    return {'algorithm': 'HMAC-SHA256', 'domain': FINAL_DOMAIN if final else PREP_DOMAIN,
            'key_sha256': sha_file(path), 'trust_mode': 'HOST_TRUSTED'}


def initialize_preparation_key():
    contract = json.loads(CONTRACT.read_bytes(), object_pairs_hook=_pairs)
    if contract.get('phase') != PREP_PHASE or contract.get('permissions', {}).get('preparation_key_generation') is not True:
        raise Error('PREPARATION_KEY_PERMISSION_CLOSED')
    path = key_path()
    bridge._require_regular_path(path, allow_missing=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(secrets.token_bytes(32)); stream.flush(); os.fsync(stream.fileno())
    return anchor()


def registered_context():
    raw = CONTRACT.read_bytes()
    contract = json.loads(raw, object_pairs_hook=_pairs)
    if contract.get('schema') != 'TD13-G33-LOCKED-CONTRACT-v1' or contract.get('run_id') != RUN_ID:
        raise Error('WRONG_FIXED_G33_CONTRACT')
    phase = contract.get('phase')
    if phase not in (PREP_PHASE, FINAL_PHASE):
        raise Error('UNREGISTERED_PHASE')
    permissions = contract.get('permissions')
    if type(permissions) is not dict or any(permissions.get(name) is not False
            for name in ('final_answers', 'final_outcomes', 'new_corpus_acquisition', 'dependency_installation')):
        raise Error('CLOSED_RIGHTS_CHANGED')
    actual = ('final_predictions', 'final_campaign', 'final_root_fault', 'final_labels')
    if phase == PREP_PHASE and any(permissions.get(name) is not False for name in actual):
        raise Error('PREPARATION_CANNOT_OPEN_FINAL')
    if contract.get('source_test_snapshot') is None or set(contract['source_test_snapshot']) != set(SOURCES):
        raise Error('EXACT_SIX_REGISTERED_FILES_REQUIRED')
    for relative, expected in contract['source_test_snapshot'].items():
        if sha_file(W / relative) != expected:
            raise Error('G33_SOURCE_TEST_DRIFT')
    bridge_context, bridge_contract = bridge.registered_context()
    if bridge_context != contract.get('immutable_G32_context'):
        raise Error('IMMUTABLE_G32_CONTEXT_DRIFT')
    for relative, expected in contract.get('protected_additional_sha256', {}).items():
        root = P if relative.startswith('P/') else W if relative.startswith('W/') else None
        if root is None or '..' in Path(relative[2:]).parts or sha_file(root / relative[2:]) != expected:
            raise Error('PROTECTED_HISTORY_DRIFT')
    authorization = ROOT / 'cache/authorization-decision-snapshot.md'
    if sha_file(authorization) != contract.get('preparation_authorization_sha256'):
        raise Error('PREPARATION_AUTHORIZATION_DRIFT')
    if not (P / 'docs/research-rca/RESEARCH-DECISIONS.md').read_bytes().startswith(authorization.read_bytes()):
        raise Error('AUTHORITATIVE_AUTHORIZATION_NOT_PRESERVED')
    if contract.get('prepared_conditions') != bridge_contract['prepared_conditions']:
        raise Error('FROZEN_SCIENTIFIC_CONFIG_DRIFT')
    if anchor() != contract.get('preparation_anchor'):
        raise Error('PREPARATION_ANCHOR_DRIFT')
    resource = contract.get('resource_policy')
    if (type(resource) is not dict or resource.get('max_frame_bytes') != MAX_FRAME or resource.get('max_input_bytes') != MAX_INPUT
            or resource.get('max_hydrate_bytes') != MAX_HYDRATE or resource.get('workers_at_once') != 1):
        raise Error('REGISTERED_RESOURCE_POLICY_DRIFT')
    policy = contract.get('reproduction_policy', {})
    if (policy.get('full_durable_audit_cases') != 60 or policy.get('full_evaluator_replay_cases') != 60
            or policy.get('numeric_replay_ordinals') != [0,29,59]):
        raise Error('PREDECLARED_REPRODUCTION_COVERAGE_DRIFT')
    return {'contract_sha256': hashlib.sha256(raw).hexdigest(), 'phase': phase,
            'source_sha256': _digest(contract['source_test_snapshot']),
            'scientific_sha256': _digest(contract['prepared_conditions']),
            'resource_sha256': _digest(resource), 'permissions_sha256': _digest(permissions),
            'bridge_context_sha256': _digest(bridge_context), 'preparation_anchor': anchor(),
            'reproduction_policy_sha256': _digest(policy)}, contract


def verify_preparation_evidence(contract):
    """Exact receipts, not caller success flags, qualify preparation."""
    required = {'development_timing', 'capacity', 'unit_checks', 'independent_prequalification'}
    evidence = contract.get('preparation_evidence', {})
    if set(evidence) != required:
        raise Error('PREPARATION_EVIDENCE_INCOMPLETE')
    for ref in evidence.values():
        target = W / ref['path']
        bridge._require_regular_path(target)
        if target.resolve().parent != (ROOT / 'cache').resolve() and (ROOT / 'cache').resolve() not in target.resolve().parents:
            raise Error('PREPARATION_EVIDENCE_PATH_ESCAPE')
        if target.stat().st_size != ref['bytes'] or sha_file(target) != ref['sha256']:
            raise Error('PREPARATION_EVIDENCE_DRIFT')
    report = json.loads((W / evidence['development_timing']['path']).read_bytes())
    if (report.get('planned_cases') != 30 or report.get('successful_measured_arm_count') != 180
            or report.get('workload') != 'G33_STREAMED_C1_FROZEN_MATH_FULL_WALL'
            or report['context']['source_sha256'] != _digest(contract['source_test_snapshot'])
            or report['derived_common_timeout_seconds'] != contract['resource_policy']['common_L_O_R_timeout_seconds']):
        raise Error('MATCHING_STREAMED_DEVELOPMENT_TIMING_MISSING')
    capacity = json.loads((W / evidence['capacity']['path']).read_bytes())
    if (capacity.get('scope') != 'SYNTHETIC_CAPACITY_ONLY_UNQUALIFIED_HELPER'
            or capacity.get('passed') is not True or capacity.get('candidate_count') != 27
            or capacity.get('numeric_channels') != 12 or capacity.get('planned_C1_draws') != 256
            or capacity.get('planned_C5_detectors') != 8 or capacity.get('stream_bins') != 252
            or capacity.get('source_sha256') != _digest(contract['source_test_snapshot'])):
        raise Error('STRUCTURAL_CAPACITY_PROOF_MISSING')
    for name, status in (('unit_checks', 'PASS'), ('independent_prequalification', 'PASS_IMPLEMENTATION_ONLY')):
        report = json.loads((W / evidence[name]['path']).read_bytes())
        if (report.get('status') != status or report.get('source_sha256') != _digest(contract['source_test_snapshot'])
                or report.get('actual_predictions_or_truth') is not False):
            raise Error('STALE_OR_UNRELATED_PREPARATION_REVIEW_OR_TESTS')
        for ref in report.get('references', []):
            target = W / ref['path']
            bridge._require_regular_path(target)
            if target.stat().st_size != ref['bytes'] or sha_file(target) != ref['sha256']:
                raise Error('PREPARATION_REVIEW_OR_TEST_LOG_DRIFT')


def require_final_authorization():
    context, contract = registered_context()
    permissions = contract['permissions']
    if context['phase'] != FINAL_PHASE or any(permissions.get(name) is not True
            for name in ('final_predictions', 'final_campaign', 'final_root_fault', 'final_labels')):
        raise Error('FINAL_CAMPAIGN_NOT_AUTHORIZED')
    proof = contract.get('human_final_authorization', {})
    path = ROOT / 'cache/final-authorization-decision-snapshot.md'
    bridge._require_regular_path(path)
    raw = path.read_bytes()
    decision_id = proof.get('decision_id', '')
    if re.fullmatch(r'RCA-[0-9]{3,}', decision_id) is None:
        raise Error('EXPLICIT_ATOMIC_HUMAN_FINAL_RECORD_MISSING')
    record = (f'| {decision_id} | G33_FINAL60_PREDICTIONS_AND_POST_SEAL_ROOT_FAULT_TAU | '
              'USER_CONFIRMED | Lê Văn Minh; explicit final campaign authorization |').encode('utf-8')
    if (proof.get('sha256') != hashlib.sha256(raw).hexdigest()
            or proof.get('record_sha256') != hashlib.sha256(record).hexdigest()
            or record not in raw.splitlines()
            or not (P / 'docs/research-rca/RESEARCH-DECISIONS.md').read_bytes().startswith(raw)):
        raise Error('EXPLICIT_HUMAN_FINAL_GATE_MISSING')
    if anchor(True) != contract.get('final_anchor'):
        raise Error('SEPARATE_FINAL_ANCHOR_MISSING')
    qualification = verify_seal(final=False, current_contract=False)
    registered = qualification['commitment']['context']
    if (registered['source_sha256'] != context['source_sha256']
            or registered['scientific_sha256'] != context['scientific_sha256']
            or registered['resource_sha256'] != context['resource_sha256']
            or registered['reproduction_policy_sha256'] != context['reproduction_policy_sha256']):
        raise Error('PREPARATION_QUALIFICATION_DOES_NOT_MATCH_FINAL_ROUTE')
    return context, contract


def verify_final_telemetry_bytes():
    """Hash all180 signed telemetry objects before any root/fault projection."""
    from scripts.task_g import final_source as source
    from scripts.task_g import source_admission
    from scripts.task_g.provenance import verify_entry_receipt
    receipt = verify_entry_receipt()
    if receipt.get('receipt_sha256') != source.ENTRY_SHA:
        raise Error('PINNED_ADMISSION_RECEIPT_DRIFT')
    path = W / source.ENTRY_REL
    if sha_file(path) != source.ENTRY_SHA:
        raise Error('PINNED_ADMISSION_BYTES_DRIFT')
    admission = json.loads(path.read_bytes())['commitment']['execution']['aggregate_report']['admission']
    import pyarrow.parquet as pq
    if sha_file(W / source.METADATA_REL) != source.METADATA_SHA:
        raise Error('PINNED_METADATA_DRIFT')
    _, registry = source_admission._read_frozen_contract(W, P)
    identities = source_admission._plan_final_metadata(
        pq.read_table(W / source.METADATA_REL, columns=list(source.ROSTER_PROJECTION)).to_pylist(), registry)['final_ids']
    descriptors = []
    for ordinal, identity in enumerate(identities):
        audit = admission['case_audits'][ordinal]
        if audit['ordinal'] != ordinal:
            raise Error('RAW_ADMISSION_ORDINAL_DRIFT')
        for modality in ('metrics', 'traces', 'logs'):
            item = audit['modalities'][modality]
            descriptors.append({'path': f'{identity}/{modality}.parquet', 'bytes': item['bytes'], 'sha256': item['sha256']})
    descriptors.sort(key=lambda item: item['path'])
    if len(descriptors) != 180 or _digest(descriptors) != source.DESCRIPTOR_SHA:
        raise Error('RAW_ADMISSION_DESCRIPTOR_DRIFT')
    _verify_descriptor_bytes(W / source.RAW_REL, descriptors)
    return {'objects_verified': 180, 'descriptor_sha256': source.DESCRIPTOR_SHA, 'hash_only': True}


def _verify_descriptor_bytes(root, descriptors):
    from scripts.task_g import source_admission
    if len({item['path'] for item in descriptors}) != len(descriptors):
        raise Error('DUPLICATE_TELEMETRY_DESCRIPTOR')
    for item in descriptors:
        target = source_admission._exact_local_path(root, item['path'])
        if target.stat().st_size != item['bytes'] or sha_file(target) != item['sha256']:
            raise Error('FINAL_TELEMETRY_BYTES_DRIFT_BEFORE_TRUTH')


def _bounded_encode(value, bound):
    chunks = bytearray()
    encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':'))
    for piece in encoder.iterencode(value):
        raw = piece.encode('utf-8')
        if len(chunks) + len(raw) > bound:
            return None
        chunks.extend(raw)
    return bytes(chunks)


class ShardStore:
    """Content-addressed trees preserve large catalogs without whole JSON files."""
    def __init__(self, root=None):
        self.root = Path(root) if root is not None else ROOT / 'cache/shards'
        self.root.mkdir(parents=True, exist_ok=True)
        self.write_seconds = 0.0
        self.new_files = 0
        self.maximum_frame_bytes = 0

    def _persist(self, node):
        import time
        started = time.perf_counter()
        raw = _bounded_encode(node, MAX_FRAME)
        if raw is None:
            raise Error('SHARD_FRAME_OVERFLOW_WITHOUT_TRUNCATION')
        digest = hashlib.sha256(raw).hexdigest()
        target = self.root / (digest + '.json')
        bridge._require_regular_path(target, allow_missing=True)
        if target.exists():
            if target.stat().st_size != len(raw) or sha_file(target) != digest:
                raise Error('CONTENT_ADDRESSED_SHARD_TAMPER')
        else:
            with target.open('xb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            if sha_file(target) != digest:
                raise Error('SHARD_DURABLE_READBACK_DIFFERS')
            self.new_files += 1
        self.write_seconds += time.perf_counter() - started
        self.maximum_frame_bytes = max(self.maximum_frame_bytes, len(raw))
        return {'path': target.relative_to(W).as_posix(), 'sha256': digest, 'bytes': len(raw)}

    def put(self, value):
        if _bounded_encode({'node': 'leaf', 'value': value}, MAX_FRAME) is not None:
            return self._persist({'node': 'leaf', 'value': value})
        if type(value) is dict:
            return self._persist({'node': 'dict', 'keys': list(value), 'children': [self.put(item) for item in value.values()]})
        if type(value) is list:
            return self._persist({'node': 'list', 'children': [self.put(item) for item in value]})
        if type(value) is str:
            width = MAX_FRAME // 8
            return self._persist({'node': 'string', 'children': [self.put(value[index:index + width])
                                                               for index in range(0, len(value), width)]})
        raise Error('UNSHARDABLE_VALUE')

    def _node(self, ref):
        if type(ref) is not dict or set(ref) != {'path', 'sha256', 'bytes'}:
            raise Error('MALFORMED_SHARD_REFERENCE')
        if type(ref['bytes']) is not int or not 0 < ref['bytes'] <= MAX_FRAME:
            raise Error('SHARD_FRAME_LENGTH_INVALID')
        digest = bridge._require_digest(ref['sha256'])
        target = self.root / (digest + '.json')
        if ref['path'] != target.relative_to(W).as_posix():
            raise Error('SHARD_PATH_ESCAPE_OR_STALE_ROLE')
        bridge._require_regular_path(target)
        if target.stat().st_size != ref['bytes'] or sha_file(target) != digest:
            raise Error('SHARD_MISSING_TRUNCATED_OR_TAMPERED')
        return decode(target.read_bytes())

    def verify(self, ref, seen=None, depth=0):
        if depth > 32:
            raise Error('SHARD_TREE_DEPTH_INVALID')
        seen = set() if seen is None else seen
        if type(ref) is not dict or set(ref) != {'path', 'sha256', 'bytes'}:
            raise Error('MALFORMED_SHARD_REFERENCE')
        digest = bridge._require_digest(ref['sha256'])
        if ref['path'] != (self.root / (digest + '.json')).relative_to(W).as_posix():
            raise Error('SHARD_PATH_ESCAPE_OR_STALE_ROLE')
        if type(ref['bytes']) is not int or not 0 < ref['bytes'] <= MAX_FRAME:
            raise Error('SHARD_FRAME_LENGTH_INVALID')
        identity = (digest, ref['path'], ref['bytes'])
        if identity in seen:
            return
        node = self._node(ref)
        kind = node.get('node')
        if kind == 'leaf':
            if set(node) != {'node', 'value'}:
                raise Error('MALFORMED_SHARD_LEAF')
        elif kind in ('dict', 'list', 'string'):
            children = node.get('children')
            if type(children) is not list:
                raise Error('SHARD_CHILDREN_MISSING')
            if kind == 'dict' and (type(node.get('keys')) is not list or len(node['keys']) != len(children)
                                  or len(set(node['keys'])) != len(node['keys'])):
                raise Error('SHARD_DICTIONARY_KEYS_INVALID')
            if set(node) != ({'node', 'keys', 'children'} if kind == 'dict' else {'node', 'children'}):
                raise Error('UNKNOWN_SHARD_STRUCTURE')
            for child in children:
                self.verify(child, seen, depth + 1)
        else:
            raise Error('UNKNOWN_SHARD_ENCODING')
        seen.add(identity)

    def get(self, ref, budget=None, depth=0):
        budget = [MAX_HYDRATE] if budget is None else budget
        budget[0] -= ref['bytes']
        if budget[0] < 0 or depth > 32:
            raise Error('BOUNDED_HYDRATION_LIMIT')
        node = self._node(ref)
        kind = node['node']
        if kind == 'leaf':
            return node['value']
        values = [self.get(child, budget, depth + 1) for child in node['children']]
        if kind == 'dict':
            return dict(zip(node['keys'], values, strict=True))
        return ''.join(values) if kind == 'string' else values


def iter_case_inventories(envelope):
    store = ShardStore()
    for ref in envelope['commitment']['case_inventory_manifest']:
        yield store.get(ref)


def _verify_envelope(envelope, context, contract, final):
    if type(envelope) is not dict or set(envelope) != {'commitment', 'hmac_sha256'}:
        raise Error('EXACT_AUTHENTICATED_ENVELOPE_REQUIRED')
    commitment = envelope.get('commitment')
    if type(commitment) is not dict or commitment.get('context') != context:
        raise Error('STALE_SEAL_CONTEXT')
    domain = FINAL_DOMAIN if final else PREP_DOMAIN
    if (commitment.get('domain') != domain or commitment.get('scope') != ('ACTUAL_FINAL60' if final else 'SYNTHETIC_G33_PREPARATION')
            or commitment.get('final_prediction_qualified') is not final):
        raise Error('WRONG_SEAL_DOMAIN_OR_SCOPE')
    tag = hmac.new(key_path(final).read_bytes(), _canonical(commitment), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(tag, envelope.get('hmac_sha256', '')):
        raise Error('SEAL_AUTHENTICATION_FAILED')
    attempt = commitment['attempt_manifest']
    target = W / attempt['path']
    if (ROOT / 'cache').resolve() not in target.resolve().parents:
        raise Error('ATTEMPT_PATH_ESCAPE')
    bridge._require_regular_path(target)
    if target.stat().st_size != attempt['bytes'] or sha_file(target) != attempt['sha256']:
        raise Error('ATTEMPT_MANIFEST_DRIFT')
    attempt_value = decode(target.read_bytes())
    if attempt_value['context'] != context or attempt_value['scope'] != commitment['scope']:
        raise Error('ATTEMPT_CONTEXT_DRIFT')
    refs = commitment.get('case_inventory_manifest')
    planned = 60 if final else 3
    if type(refs) is not list or len(refs) != planned or len({ref['sha256'] for ref in refs}) != planned:
        raise Error('MISSING_DUPLICATE_OR_UNPLANNED_CASE_INVENTORY')
    from scripts.task_g.locked_campaign import validate_case_inventory
    store, seen = ShardStore(), set()
    for ordinal, ref in enumerate(refs):
        store.verify(ref, seen)
        inventory = store.get(ref)
        if inventory.get('ordinal') != ordinal or inventory.get('scope') != commitment['scope'] or inventory.get('context') != context:
            raise Error('INVENTORY_ORDINAL_OR_SCOPE_DRIFT')
        for reference in inventory['scientific_roles'].values():
            store.verify(reference, seen)
        validate_case_inventory(inventory, store, contract)
    return {'case_inventories': planned, 'unique_verified_shards': len(seen), 'domain': domain,
            'full_verification_before_truth': True}


def verify_seal(*, final=False, current_contract=True):
    if final:
        context, contract = require_final_authorization()
    elif current_contract:
        context, contract = registered_context()
    else:
        snapshot = ROOT / 'cache/preparation-registration-at-seal.json'
        raw = snapshot.read_bytes()
        snapshot_value = decode(raw)
        registered_raw = bytes.fromhex(snapshot_value['registered_raw_hex'])
        contract = json.loads(registered_raw, object_pairs_hook=_pairs)
        context = snapshot_value['context']
        if (context['contract_sha256'] != hashlib.sha256(registered_raw).hexdigest()
                or context['source_sha256'] != _digest(contract['source_test_snapshot'])
                or context['scientific_sha256'] != _digest(contract['prepared_conditions'])
                or context['resource_sha256'] != _digest(contract['resource_policy'])
                or context['permissions_sha256'] != _digest(contract['permissions'])
                or context['reproduction_policy_sha256'] != _digest(contract['reproduction_policy'])
                or contract.get('phase') != PREP_PHASE or anchor() != contract['preparation_anchor']):
            raise Error('PREPARATION_REGISTRATION_SNAPSHOT_INVALID')
    if not final:
        verify_preparation_evidence(contract)
    path = ROOT / ('predictions-seal.json' if final else 'cache/preparation-seal.json')
    bridge._require_regular_path(path)
    if path.stat().st_size > MAX_FRAME:
        raise Error('GLOBAL_SEAL_TOO_LARGE')
    envelope = decode(path.read_bytes())
    verification = _verify_envelope(envelope, context, contract, final)
    if current_contract and registered_context()[0] != context:
        raise Error('CONTEXT_DRIFT_DURING_FULL_VERIFICATION')
    if final:
        verification['actual_telemetry_hash_verification'] = verify_final_telemetry_bytes()
    envelope['_verified'] = {**verification, 'receipt_sha256': sha_file(path)}
    return envelope


def _publish_verified_envelope(envelope, context, final):
    target = ROOT / ('predictions-seal.json' if final else 'cache/preparation-seal.json')
    stage = ROOT / 'cache' / ('seal-stage-' + secrets.token_hex(16) + '.json')
    exclusive(stage, envelope)
    staged = decode(stage.read_bytes())
    fresh_context, fresh_contract = require_final_authorization() if final else registered_context()
    _verify_envelope(staged, fresh_context, fresh_contract, final)
    if fresh_context != context or registered_context()[0] != context:
        raise Error('CONTEXT_DRIFT_BEFORE_EXCLUSIVE_PUBLICATION')
    bridge._require_regular_path(target, allow_missing=True)
    os.link(str(stage), str(target))


def commit_execution(execution_handle):
    from scripts.task_g.locked_campaign import _issued_execution_for_provenance
    payload = _issued_execution_for_provenance(execution_handle)
    final = payload['scope'] == 'ACTUAL_FINAL60'
    context, contract = require_final_authorization() if final else registered_context()
    if payload['context'] != context:
        raise Error('ISSUED_EXECUTION_CONTEXT_DRIFT')
    commitment = {'schema': 'TD13-G33-GLOBAL-SEAL-v1', 'domain': FINAL_DOMAIN if final else PREP_DOMAIN,
                  'scope': payload['scope'], 'context': context,
                  'case_inventory_manifest': payload['case_inventory_manifest'],
                  'source_summary': payload['source_summary'], 'attempt_manifest': payload['attempt_manifest'],
                  'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
                  'final_prediction_qualified': final}
    if not final:
        verify_preparation_evidence(contract)
        snapshot = {'registered_raw_hex': CONTRACT.read_bytes().hex(), 'context': context}
        exclusive(ROOT / 'cache/preparation-registration-at-seal.json', snapshot)
    tag = hmac.new(key_path(final).read_bytes(), _canonical(commitment), hashlib.sha256).hexdigest()
    envelope = {'commitment': commitment, 'hmac_sha256': tag}
    target = ROOT / ('predictions-seal.json' if final else 'cache/preparation-seal.json')
    # Validate staged inventory fully before the exclusive global publication.
    store = ShardStore()
    from scripts.task_g.locked_campaign import validate_case_inventory
    for ordinal, ref in enumerate(payload['case_inventory_manifest']):
        inventory = store.get(ref)
        if inventory['ordinal'] != ordinal:
            raise Error('ISSUED_CASE_ORDER_DRIFT')
        store.verify(ref)
        for reference in inventory['scientific_roles'].values():
            store.verify(reference)
        validate_case_inventory(inventory, store, contract)
    # Failed write/fsync/readback never leaves a published, truth-opening seal.
    _publish_verified_envelope(envelope, context, final)
    return verify_seal(final=final)
