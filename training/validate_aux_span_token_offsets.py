"""Tokenizer-only exact offset validation for the ten-record annotation pilot."""
import hashlib, json
from pathlib import Path
from transformers import AutoTokenizer
from prompt_contract_v2_candidate import build_prompt, sanitize_marker_like_text

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'controlled_seed17_aux_span_annotations_chatgpt.jsonl'
OUT=ROOT/'controlled_seed17_aux_span_token_offsets_chatgpt.jsonl'
RECEIPT=ROOT/'controlled_seed17_aux_span_token_offset_receipt.json'
REV='7bcac572ce56db69c1ea7c8af255c5d7c9672fc2'

def main():
    tok=AutoTokenizer.from_pretrained('google/flan-t5-base',revision=REV,local_files_only=True,use_fast=True)
    rows=[json.loads(x) for x in SOURCE.read_text(encoding='utf-8').splitlines()]; out=[]; mapped=0
    for row in rows:
        raw=row['source_input']; sanitized=sanitize_marker_like_text(raw); prompt=build_prompt(raw)
        base=prompt.index(sanitized); enc=tok(prompt,return_offsets_mapping=True,truncation=False)
        offsets=enc['offset_mapping']; props=[]
        for prop in row['propositions']:
            spans=[]
            for span in prop['source_character_spans']:
                start,end=base+span['start'],base+span['end']
                ids=[i for i,(a,b) in enumerate(offsets) if b>start and a<end and b>a]
                if not ids: raise ValueError(f"{row['record_locator']} {prop['proposition_id']} unmapped")
                covered_start=min(offsets[i][0] for i in ids); covered_end=max(offsets[i][1] for i in ids)
                if covered_start>start or covered_end<end: raise ValueError('incomplete token coverage')
                spans.append({**span,'prompt_start':start,'prompt_end':end,'token_indices':ids,
                              'token_coverage_start':covered_start,'token_coverage_end':covered_end})
                mapped+=1
            props.append({'proposition_id':prop['proposition_id'],'mapped_spans':spans})
        out.append({'record_locator':row['record_locator'],'prompt_token_count':len(enc['input_ids']),
                    'propositions':props})
    OUT.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in out),encoding='utf-8',newline='\n')
    receipt={'status':'PASS','record_count':len(rows),'mapped_span_count':mapped,'tokenizer_revision':REV,
             'offsets_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'model_loaded':False,'compute_authorized':False}
    RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n'); print(json.dumps(receipt,indent=2))
if __name__=='__main__': main()
