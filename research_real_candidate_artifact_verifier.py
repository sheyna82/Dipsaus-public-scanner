"""Offline research-only verification of GitHub artifact transport.

This verifies exact outer bytes against caller-supplied GitHub metadata and the
inner archive digest. It does not verify the archive's candidate contents,
provider authenticity, prospectivity, or trade readiness.
"""
import hashlib
import io
import re
from zipfile import ZipFile, BadZipFile


def verify_real_candidate_artifact(outer_bytes, metadata, *, expected_run_id,
                                   expected_head_sha, expected_archive_sha256,
                                   expected_candidate_identity_sha256,
                                   max_bytes=8_000_000):
    if not isinstance(metadata, dict) or type(expected_run_id) is not int or expected_run_id <= 0:
        raise ValueError('invalid_metadata_or_run')
    if not isinstance(expected_head_sha, str) or not re.fullmatch('[0-9a-f]{40}', expected_head_sha):
        raise ValueError('invalid_head_sha')
    for value in (expected_archive_sha256, expected_candidate_identity_sha256):
        if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
            raise ValueError('invalid_expected_digest')
    workflow = metadata.get('workflow_run')
    if not isinstance(workflow, dict) or workflow.get('id') != expected_run_id or workflow.get('head_sha') != expected_head_sha:
        raise ValueError('github_run_identity_mismatch')
    if type(metadata.get('id')) is not int or metadata['id'] <= 0 or metadata.get('expired') is not False:
        raise ValueError('artifact_unavailable')
    digest = metadata.get('digest')
    if not isinstance(digest, str) or not re.fullmatch('sha256:[0-9a-f]{64}', digest):
        raise ValueError('missing_github_digest')
    if type(max_bytes) is not int or max_bytes <= 0 or not isinstance(outer_bytes, bytes) or len(outer_bytes) > max_bytes:
        raise ValueError('invalid_outer_bytes')
    if hashlib.sha256(outer_bytes).hexdigest() != digest[7:]:
        raise ValueError('github_artifact_digest_mismatch')
    try:
        with ZipFile(io.BytesIO(outer_bytes)) as outer:
            members = outer.infolist()
            if len(members) != 1 or members[0].filename != 'candidate-archive.zip' or members[0].is_dir():
                raise ValueError('unexpected_artifact_members')
            if members[0].file_size > max_bytes:
                raise ValueError('artifact_member_too_large')
            with outer.open(members[0]) as handle:
                archive_bytes = handle.read(max_bytes + 1)
    except (BadZipFile, OSError) as exc:
        raise ValueError('invalid_artifact_zip') from exc
    if len(archive_bytes) > max_bytes or hashlib.sha256(archive_bytes).hexdigest() != expected_archive_sha256:
        raise ValueError('candidate_archive_digest_mismatch')
    return {
        'status': 'real_candidate_artifact_transport_verified',
        'github_artifact_id': metadata['id'], 'github_run_id': expected_run_id,
        'candidate_archive_sha256': expected_archive_sha256,
        'candidate_archive_sha256_verified': True,
        'candidate_identity_sha256': expected_candidate_identity_sha256,
        'candidate_identity_in_archive_verified': False,
        'external_github_artifact_digest_verified': True,
        'synthetic_data_only': False,
        'independent_market_data_provenance': False,
        'prospective_signal_proven': False,
        'research_only': True, 'trade_ready': False,
    }
