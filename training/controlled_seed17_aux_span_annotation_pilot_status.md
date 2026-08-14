# Auxiliary structural-supervision ten-record annotation pilot status

**Date:** 2026-08-13  
**Status:** ChatGPT annotation pass complete; Claude independent annotation pending  
**Compute:** None; tokenizer-offset validation only  

## Frozen scope

Comparator records 007, 040, 042, 048, 053, 054, 056, 069, 074, and 075. The annotation guide was frozen
before Claude's pass. No protected/acceptance record and none of the remaining 68 comparator records was
annotated.

## ChatGPT pass

- 10 records;
- 47 propositions;
- maximum 8 propositions in one record;
- 108 valid earlier-pair duplicate candidates;
- 1 positive duplicate link (0.926% positive rate);
- exact character spans validated against committed raw source;
- all non-task/action and backward-duplicate schema gates pass;
- every span mapped to at least one pinned-tokenizer prompt token without truncation.

The 1/108 duplicate prevalence confirms Claude's forward-looking imbalance concern. No class weighting is
introduced here. A future loss-shape proposal must report the rate and either retain the already-frozen
unweighted pair mean or separately justify any change before compute.

## Capacity shape

The pilot maximum gives `m=8`. Under the reviewed formula:

```text
P_added(8) = 1,205,788 + 768*8 = 1,211,932
```

This is approximately 0.54% of the independently reviewed ~223M base. A later implementation package must
recompute the exact base trainable parameter count without loading weights and publish the exact ratio.

## Known annotation-policy stress points exposed for independent review

- comparator:040 has source facts/questions that the committed target also turns into follow-up/check
  actions; overlapping question/fact and task propositions preserve this conflict rather than hiding it.
- comparator:069 contains two explicit restatement spans linked by `duplicate_of`, with only the first
  proposition carrying the single bullet/action obligation.
- comparator:074 has eight task propositions, seven bullet obligations, and eight action obligations.
- comparator:048 separates resolved earlier coreference from a later unresolved candidate set.

## Required next evidence

Claude must annotate all ten records independently, without reading ChatGPT's row-level annotations until
his pass is sealed. Then compare proposition counts, states, spans under the frozen equivalence rule, roles,
qualifiers, coreference, duplicate links, and fields. Every disagreement must be adjudicated and recorded.

This status does not authorize implementation, full-78 annotation, model or benchmark execution, corpus
mutation, checkpoint action, seed 73, commit, or push.
