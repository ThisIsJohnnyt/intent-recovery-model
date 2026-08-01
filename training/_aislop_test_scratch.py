"""Throwaway file to verify the aislop CI workflow actually runs and
detects something. Not part of the training pipeline -- delete before
merge, this PR is test-only and will be closed, not merged."""


def process_records(records):
    # This function processes the records
    results = []
    for r in records:
        try:
            results.append(r["value"] * 2)
        except Exception:
            pass
    print("done processing")
    return results


def unused_helper():
    return 42
