# Gate 5 response-shape key-manifest diagnostic retry proposal

**Date:** 2026-08-16  
**Status:** Local-only proposal. It authorizes implementation and review only, not credential access, a
provider request, spend, parser change, candidate handling, pilot resumption, staging, commit, or push.

## Basis

The first independently reviewed key-manifest diagnostic made its one authorized request and received HTTP
503 with Google's bounded message indicating temporary high demand. Its receipt validates, contains no key
manifest, and provides no evidence about the HTTP-200 response shape. Its package-level attempt lock is
permanently consumed, so that runner must be retired and cannot be reused.

Johnny chose to prepare a fresh attempt rather than widen the production parser from documentation inference.
This proposal defines a new one-shot diagnostic with the same request, cost, manifest, and evidence boundaries.
The only operational changes are new artifact identities, a new attestation chain, a new output directory, and
a distinct package-level attempt lock.

## Additional immutable pins

In addition to every evidence pin in the reviewed original proposal
`b361734c6fe329e96002237ea0b7babe671bd009f6b44297aa8f58f8fa3e41d5`, this retry must pin:

- consumed diagnostic receipt file SHA-256
  `4cf8be458dbc639d6336c9832a3538ad79f6423d10cb1069eb4b1612bf05711c`;
- consumed diagnostic receipt row SHA-256
  `391215e0ee809e79f59bcceb636efb47acd1c50af37ff055471c3411ca151531`;
- consumed diagnostic raw-response SHA-256
  `01f5c7d4e4d8ec06c8098777e731b3d552ba518feb02b681f6c569edcd9c6f6d`;
- consumed attempt-lock file SHA-256
  `48dc28526a2ba5b4ce310e15467e6899e36aa6521bae338f377f60dfd86c065a`;
- consumed final attestation SHA-256
  `6407098105d1b57369cb68ca3d161e162be47fc9c0146db52b1a30db85aaba31`.

The runner must re-run the retired runner's strict historical receipt verifier and confirm HTTP 503, null key
manifest, the captured high-demand message, exact request hash, full conservative reservation, and the consumed
lock before any new output or credential access.

## Unchanged frozen operation and evidence boundary

The retry may eventually make exactly one POST of frozen slot 1/M01 to
`gemini-3.7-flash:generateContent`, with request envelope
`8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4`, capped at 10,680 USD millionths
($0.01068). It has no retry, redirect, substitution, alternate endpoint, streaming, tool, caching, grounding,
URL-context, candidate retention/review, corpus mutation, or pilot-resumption path and stops after the one
transport attempt regardless of outcome.

The HTTP-200 manifest boundary is byte-for-byte in substance with the original reviewed proposal: strict
UTF-8 and duplicate-key rejection; no existing candidate parser; only regex-bounded, sorted object key names
and capped counts at the top-level/candidate/content/part/usage/modelStatus paths; never response values,
candidate text, signatures, token counts, identifiers, headers, or raw bytes. Non-200 uses only the reviewed
bounded `error.message` path. All receipt and stdout restrictions remain unchanged.

A new fixed attempt lock named for this retry must be exclusive-created before output reservation and
credential access. The consumed original lock and the original diagnostic output directory remain untouched.

## Required sequence

1. Both agents review this proposal, the retired original runner, and the new runner/gate/template/tests.
2. Johnny confirms fresh same-day facts and the unchanged in-memory/key-names-only boundary.
3. A fresh attestation initially leaves the retry authorization false and is independently reviewed.
4. Johnny separately authorizes exactly one retry request capped at $0.01068.
5. Johnny alone runs the command with the local credential.
6. Both agents verify the receipt before any parser change or pilot decision.

Nothing here authorizes the retry request, a parser change, or pilot resumption.
