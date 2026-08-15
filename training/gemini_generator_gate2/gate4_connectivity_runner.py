"""One-shot Gate 4 model-metadata connectivity checker.

Safe by default: without --execute-once, this verifies only the frozen proposal
hash and performs no secret-store read or network activity.  Real execution is
intentionally limited to one GET request and must be separately authorized.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import http.client
import json
import os
import re
import ssl
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable


PACKAGE = Path(__file__).resolve().parent
PROPOSAL_PATH = PACKAGE / "gate4_zero_content_connectivity_proposal.md"
EXPECTED_PROPOSAL_SHA256 = "b489df11e0d67e1ccfc99cafde0c25a71319436e4b12ab2a488be4276c97bfad"
HOST = "generativelanguage.googleapis.com"
PATH = "/v1beta/models/gemini-3.7-flash"
MODEL_NAME = "models/gemini-3.7-flash"
TIMEOUT_SECONDS = 30
MAX_RESPONSE_BYTES = 256 * 1024
COST_CAP_USD_MILLIONTHS = 1_000_000
KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z_-]{20,}")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_RESPONSE_KEYS = {
    "content", "contents", "candidate", "candidates", "usagemetadata", "prompttokencount",
    "candidatestokencount", "totaltokencount", "tooluse", "toolusetokens",
}


class Gate4Stop(RuntimeError):
    """A fail-closed Gate 4 stop with a safe machine-readable reason."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def canonical_file_sha256(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or not raw.endswith(b"\n"):
        raise Gate4Stop("proposal_canonicalization_failed")
    has_crlf = b"\r\n" in raw
    without_crlf = raw.replace(b"\r\n", b"")
    if b"\r" in without_crlf or (has_crlf and b"\n" in without_crlf):
        raise Gate4Stop("proposal_canonicalization_failed")
    try:
        canonical = raw.replace(b"\r\n", b"\n")
        canonical.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Gate4Stop("proposal_canonicalization_failed") from exc
    return sha256_bytes(canonical)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Gate4Stop("duplicate_json_key")
        result[key] = value
    return result


def contains_key_like_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(KEY_PATTERN.search(value))
    if isinstance(value, dict):
        return any(contains_key_like_value(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_key_like_value(item) for item in value)
    return False


def normalized_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def contains_forbidden_response_field(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            normalized_key(str(key)) in FORBIDDEN_RESPONSE_KEYS or contains_forbidden_response_field(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(contains_forbidden_response_field(item) for item in value)
    return False


def parse_metadata(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_RESPONSE_BYTES:
        raise Gate4Stop("response_too_large")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
    except Gate4Stop:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Gate4Stop("invalid_json") from exc
    if not isinstance(value, dict) or contains_forbidden_response_field(value):
        raise Gate4Stop("metadata_validation_failed")
    name = value.get("name")
    methods = value.get("supportedGenerationMethods")
    if name != MODEL_NAME or not isinstance(methods, list) or "generateContent" not in methods:
        raise Gate4Stop("metadata_validation_failed")
    if any(not isinstance(item, str) for item in methods):
        raise Gate4Stop("metadata_validation_failed")
    selected = {
        "name": name,
        "baseModelId": value.get("baseModelId"),
        "version": value.get("version"),
        "supportedGenerationMethods": methods,
        "validation": {
            "single_metadata_object": True,
            "name_exact": True,
            "generate_content_present": True,
            "forbidden_content_candidate_usage_tool_fields_absent": True,
            "duplicate_json_keys_absent": True,
        },
    }
    if contains_key_like_value(selected):
        raise Gate4Stop("secret_exposure")
    return selected


@dataclass(frozen=True)
class ProviderResponse:
    status: int
    headers: dict[str, str]
    body: bytes


class HTTPSMetadataTransport:
    """A direct standard-library transport with no redirect or retry behavior."""

    def get(self, headers: dict[str, str]) -> ProviderResponse:
        connection = http.client.HTTPSConnection(HOST, timeout=TIMEOUT_SECONDS, context=ssl.create_default_context())
        try:
            connection.request("GET", PATH, body=None, headers=headers)
            response = connection.getresponse()
            body = response.read(MAX_RESPONSE_BYTES + 1)
            return ProviderResponse(response.status, {key.lower(): value for key, value in response.getheaders()}, body)
        finally:
            connection.close()


def load_windows_generic_credential(target_name: str) -> str:
    """Read one generic Windows Credential Manager value without printing it."""
    if os.name != "nt" or not target_name or "\x00" in target_name:
        raise Gate4Stop("credential_unavailable")

    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", ctypes.c_ulong), ("dwHighDateTime", ctypes.c_ulong)]

    class CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags", ctypes.c_ulong), ("Type", ctypes.c_ulong), ("TargetName", ctypes.c_wchar_p),
            ("Comment", ctypes.c_wchar_p), ("LastWritten", FILETIME), ("CredentialBlobSize", ctypes.c_ulong),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)), ("Persist", ctypes.c_ulong),
            ("AttributeCount", ctypes.c_ulong), ("Attributes", ctypes.c_void_p), ("TargetAlias", ctypes.c_wchar_p),
            ("UserName", ctypes.c_wchar_p),
        ]

    credential_pointer = ctypes.POINTER(CREDENTIALW)()
    advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    cred_read = advapi32.CredReadW
    cred_read.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.POINTER(CREDENTIALW))]
    cred_read.restype = ctypes.c_bool
    cred_free = advapi32.CredFree
    cred_free.argtypes = [ctypes.c_void_p]
    cred_free.restype = None
    if not cred_read(target_name, 1, 0, ctypes.byref(credential_pointer)):
        raise Gate4Stop("credential_unavailable")
    try:
        size = int(credential_pointer.contents.CredentialBlobSize)
        blob = ctypes.string_at(credential_pointer.contents.CredentialBlob, size) if size else b""
    finally:
        cred_free(credential_pointer)
    try:
        secret = blob.decode("utf-16-le").rstrip("\x00")
    except UnicodeDecodeError as exc:
        raise Gate4Stop("credential_unavailable") from exc
    if not 20 <= len(secret) <= 512 or any(ch in secret for ch in "\r\n\x00"):
        raise Gate4Stop("credential_unavailable")
    return secret


def base_receipt(proposal_hash: str) -> dict[str, Any]:
    return {
        "artifact": "gemini_generator_gate4_connectivity_receipt",
        "proposal_sha256": proposal_hash,
        "execution_timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "authorization": "Johnny separately authorized one Gate 4 metadata request with a maximum total cost of $1.00.",
        "transport": {
            "method": "GET",
            "endpoint": f"https://{HOST}{PATH}",
            "request_body_byte_count": 0,
            "header_names": ["Accept", "x-goog-api-key"],
            "timeout_seconds": TIMEOUT_SECONDS,
            "redirects_disabled": True,
            "retries_disabled": True,
            "provider_request_count": 0,
        },
        "response": {
            "http_status": None,
            "provider_request_id": None,
            "byte_count": None,
            "sha256": None,
            "reported_usage_fields": [],
        },
        "metadata": None,
        "redaction_scan": {"key_like_value_found": False, "raw_error_persisted": False},
        "cost": {
            "authorized_cap_usd_millionths": COST_CAP_USD_MILLIONTHS,
            "pre_request_reservation_usd_millionths": COST_CAP_USD_MILLIONTHS,
            "actual_usd_millionths": None,
            "reconciliation_state": "not_requested",
        },
        "disposition": "stopped",
        "stop_reason": None,
        "prior_receipt_row_hash": None,
    }


ATTESTATION_TRUE_FIELDS = {
    "paid_tier_confirmed_that_day",
    "prepay_plan_confirmed_that_day",
    "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot",
    "no_unexpected_billing_activity_since_gate3",
    "no_other_activity_during_gate4_window",
    "exact_model_available_and_not_deprecated_that_day",
    "metadata_billing_ambiguity_reviewed",
    "one_request_execution_authorized_by_johnny",
    "key_remains_in_user_controlled_encrypted_local_secret_store",
}


def load_and_validate_attestation(path: Path) -> None:
    """Require a same-day, user-completed pre-execution attestation before sending."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Gate4Stop) as exc:
        raise Gate4Stop("pre_execution_attestation_invalid") from exc
    if not isinstance(value, dict):
        raise Gate4Stop("pre_execution_attestation_invalid")
    if value.get("artifact") != "gemini_generator_gate4_pre_execution_attestation":
        raise Gate4Stop("pre_execution_attestation_invalid")
    if value.get("execution_date") != date.today().isoformat() or value.get("attestor") != "Johnny":
        raise Gate4Stop("pre_execution_attestation_invalid")
    if any(value.get(field) is not True for field in ATTESTATION_TRUE_FIELDS):
        raise Gate4Stop("pre_execution_attestation_invalid")
    balance = value.get("positive_prepaid_balance_usd_millionths")
    if not isinstance(balance, int) or balance < COST_CAP_USD_MILLIONTHS:
        raise Gate4Stop("pre_execution_attestation_invalid")
    if value.get("one_request_cost_cap_usd_millionths") != COST_CAP_USD_MILLIONTHS:
        raise Gate4Stop("pre_execution_attestation_invalid")
    if contains_key_like_value(value):
        raise Gate4Stop("pre_execution_attestation_invalid")


def reserve_one_attempt(ledger_path: Path, proposal_hash: str) -> None:
    """Atomically reserve the only Gate 4 attempt before the transport call."""
    row = {
        "artifact": "gemini_generator_gate4_pre_request_reservation",
        "execution_timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "proposal_sha256": proposal_hash,
        "authorized_cap_usd_millionths": COST_CAP_USD_MILLIONTHS,
        "pre_request_reservation_usd_millionths": COST_CAP_USD_MILLIONTHS,
        "prior_ledger_row_hash": None,
        "reservation_state": "reserved_pre_request",
    }
    row["row_hash"] = sha256_bytes(canonical_json_bytes(row))
    if contains_key_like_value(row):
        raise Gate4Stop("secret_exposure")
    try:
        with ledger_path.open("xb") as handle:
            handle.write(canonical_json_bytes(row))
    except FileExistsError as exc:
        raise Gate4Stop("gate4_attempt_already_reserved") from exc
    except OSError as exc:
        raise Gate4Stop("reservation_ledger_unavailable") from exc


def finalize_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    if contains_key_like_value(receipt):
        receipt["redaction_scan"]["key_like_value_found"] = True
        receipt["disposition"] = "stopped"
        receipt["stop_reason"] = "secret_exposure"
    receipt["row_hash"] = sha256_bytes(canonical_json_bytes(receipt))
    return receipt


def verify_receipt(receipt: dict[str, Any]) -> None:
    required = {
        "artifact", "proposal_sha256", "execution_timestamp_utc", "authorization", "transport", "response",
        "metadata", "redaction_scan", "cost", "disposition", "stop_reason", "prior_receipt_row_hash", "row_hash",
    }
    if set(receipt) != required or receipt["artifact"] != "gemini_generator_gate4_connectivity_receipt":
        raise Gate4Stop("receipt_invalid")
    if receipt["proposal_sha256"] != EXPECTED_PROPOSAL_SHA256 or not HEX64.fullmatch(receipt["row_hash"]):
        raise Gate4Stop("receipt_invalid")
    payload = {key: value for key, value in receipt.items() if key != "row_hash"}
    if receipt["row_hash"] != sha256_bytes(canonical_json_bytes(payload)) or contains_key_like_value(receipt):
        raise Gate4Stop("receipt_invalid")
    transport = receipt["transport"]
    response = receipt["response"]
    cost = receipt["cost"]
    if set(transport) != {"method", "endpoint", "request_body_byte_count", "header_names", "timeout_seconds", "redirects_disabled", "retries_disabled", "provider_request_count"}:
        raise Gate4Stop("receipt_invalid")
    if transport != {
        **transport,
        "method": "GET",
        "endpoint": f"https://{HOST}{PATH}",
        "request_body_byte_count": 0,
        "header_names": ["Accept", "x-goog-api-key"],
        "timeout_seconds": TIMEOUT_SECONDS,
        "redirects_disabled": True,
        "retries_disabled": True,
    } or transport["provider_request_count"] not in {0, 1}:
        raise Gate4Stop("receipt_invalid")
    if set(response) != {"http_status", "provider_request_id", "byte_count", "sha256", "reported_usage_fields"} or response["reported_usage_fields"] != []:
        raise Gate4Stop("receipt_invalid")
    if set(cost) != {"authorized_cap_usd_millionths", "pre_request_reservation_usd_millionths", "actual_usd_millionths", "reconciliation_state"}:
        raise Gate4Stop("receipt_invalid")
    if cost["authorized_cap_usd_millionths"] != COST_CAP_USD_MILLIONTHS or cost["pre_request_reservation_usd_millionths"] != COST_CAP_USD_MILLIONTHS:
        raise Gate4Stop("receipt_invalid")


def execute_once(
    credential_loader: Callable[[str], str],
    credential_target: str,
    transport: Any,
    attestation_path: Path,
    ledger_path: Path,
) -> dict[str, Any]:
    proposal_hash = canonical_file_sha256(PROPOSAL_PATH)
    receipt = base_receipt(proposal_hash)
    if proposal_hash != EXPECTED_PROPOSAL_SHA256:
        receipt["stop_reason"] = "proposal_hash_mismatch"
        return finalize_receipt(receipt)
    try:
        load_and_validate_attestation(attestation_path)
        secret = credential_loader(credential_target)
        if not isinstance(secret, str) or not secret or any(ch in secret for ch in "\r\n\x00"):
            raise Gate4Stop("credential_unavailable")
        headers = {"Accept": "application/json", "x-goog-api-key": secret}
        reserve_one_attempt(ledger_path, proposal_hash)
        receipt["transport"]["provider_request_count"] = 1
        response = transport.get(headers)
        receipt["cost"]["reconciliation_state"] = "unknown_pending_billing"
        receipt["response"]["http_status"] = response.status
        receipt["response"]["byte_count"] = len(response.body)
        receipt["response"]["sha256"] = sha256_bytes(response.body)
        request_id = response.headers.get("x-request-id") or response.headers.get("x-goog-request-id")
        if request_id and re.fullmatch(r"[A-Za-z0-9._-]{1,200}", request_id) and not KEY_PATTERN.search(request_id):
            receipt["response"]["provider_request_id"] = request_id
        if response.status != 200:
            raise Gate4Stop("unexpected_http_status")
        receipt["metadata"] = parse_metadata(response.body)
        receipt["disposition"] = "passed"
        receipt["stop_reason"] = None
    except Gate4Stop as exc:
        receipt["stop_reason"] = exc.code
    except (OSError, http.client.HTTPException, ssl.SSLError):
        receipt["stop_reason"] = "transport_error"
        if receipt["transport"]["provider_request_count"]:
            receipt["cost"]["reconciliation_state"] = "unknown_pending_billing"
    finally:
        # Do not persist the credential. This merely shortens the local reference lifetime.
        secret = None
    return finalize_receipt(receipt)


def write_new_receipt(path: Path, receipt: dict[str, Any]) -> None:
    verify_receipt(receipt)
    try:
        with path.open("xb") as handle:
            handle.write(canonical_json_bytes(receipt))
    except FileExistsError as exc:
        raise Gate4Stop("receipt_path_already_exists") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="verify the frozen proposal hash without key or network access")
    parser.add_argument("--execute-once", action="store_true", help="perform the separately authorized single metadata request")
    parser.add_argument("--credential-target", help="Windows Credential Manager generic-credential label; never recorded")
    parser.add_argument("--attestation", type=Path, help="same-day Gate 4 attestation file; never recorded")
    parser.add_argument("--ledger", type=Path, default=PACKAGE / "gate4_connectivity_ledger.jsonl", help="new reservation ledger path")
    parser.add_argument("--receipt", type=Path, default=PACKAGE / "gate4_connectivity_receipt.json")
    args = parser.parse_args()
    if args.verify_only == args.execute_once:
        parser.error("choose exactly one of --verify-only or --execute-once")
    proposal_hash = canonical_file_sha256(PROPOSAL_PATH)
    if args.verify_only:
        result = {"proposal_sha256": proposal_hash, "matches_frozen_proposal": proposal_hash == EXPECTED_PROPOSAL_SHA256, "network_used": False, "secret_store_read": False}
        print(json.dumps(result, sort_keys=True))
        return 0 if result["matches_frozen_proposal"] else 2
    if not args.credential_target or not args.attestation:
        parser.error("--credential-target and --attestation are required with --execute-once")
    receipt = execute_once(load_windows_generic_credential, args.credential_target, HTTPSMetadataTransport(), args.attestation, args.ledger)
    write_new_receipt(args.receipt, receipt)
    print(json.dumps({"disposition": receipt["disposition"], "stop_reason": receipt["stop_reason"], "receipt": str(args.receipt)}, sort_keys=True))
    return 0 if receipt["disposition"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
