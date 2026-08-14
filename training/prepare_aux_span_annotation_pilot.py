"""Materialize ChatGPT's ten-record auxiliary span annotations and validate exact source spans."""

from __future__ import annotations

import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CORPUS=ROOT/'gold_v1.2.2_phase2_derived_candidate.jsonl'
OUT=ROOT/'controlled_seed17_aux_span_annotations_chatgpt.jsonl'
RECEIPT=ROOT/'controlled_seed17_aux_span_annotation_receipt.json'
IDS=(7,40,42,48,53,54,56,69,74,75)
STATES={'fact','question','fragment','tentative_idea','task'}
ROLES={'speaker','actor','recipient','object','possessor','experiencer','candidate_set'}
QUALS={'time','deadline','destination','trigger','condition','quantity','purpose','object_modifier'}
FIELDS=('narrative','bullet','action')

def p(quotes,state,fields,roles=(),quals=(),coref='none',dup=None):
    return {'quotes':quotes if isinstance(quotes,list) else [quotes], 'state':state,'fields':list(fields),
            'roles':list(roles),'qualifiers':list(quals),'coreference':coref,'duplicate_of':dup}

A={
7:[
p('sunset chasers api integration weather.gov or openweather? openweather cheaper','task','nba',('actor','object')),
p('wait what if we add cloud cover percentage on the main UI?','tentative_idea','nb',('object',),('destination',)),
p('color palette should be orange/purple','fact','nb',('object',)),
p(['need to move backend to free tier for vacation testing','free tier azure? heroku?'],'task','nba',('actor','object'),('destination','purpose')),
p('look up heroku pricing','task','na',('actor','object'))],
40:[
p('the client call got pushed to 3, need new talking points','task','nba',('actor','object'),('time',)),
p(['i never heard back from the plumber about the leak','plumber never called back'],'task','nba',('actor','object')),
p('still stressed about that','fact','nb',('experiencer',)),
p("remember to grab the mail it's probably piling up",'task','na',('actor','object')),
p("it's probably piling up",'fact','nb',('object',)),
p('is thursday the trash day or is it friday','question','nb',(),('time',), 'unresolved'),
p('is thursday the trash day or is it friday','task','na',('actor','object'),('time',))],
42:[
p('The planning meeting felt more focused this time','fact','nb'),
p('the shorter agenda probably helped','tentative_idea','nb'),
p('send Nora the updated attendance sheet','task','nba',('actor','recipient','object')),
p('the last ten minutes still wandered','fact','nb',(),('quantity','time'))],
48:[
p('Rina told Marcus the draft was approved after he asked about it','fact','nb',('speaker','recipient','actor','object'),(), 'resolved'),
p('he asked about it','fact','nb',('actor','object'),(), 'resolved'),
p("He still needs the signed copy, but I can't tell whether 'he' means Marcus or the client",'question','nb',('candidate_set','object'),(), 'unresolved'),
p('Ask Rina who needs it','task','nba',('actor','recipient','object'),(), 'unresolved')],
53:[
p(['Submit the mileage form','mileage form before Friday',"don't let the mileage form disappear under everything else"],'task','nba',('actor','object'),('deadline',)),
p('the kitchen sink is dripping again','fact','nb',('object',)),
p('which is exhausting','fact','nb',('experiencer',)),
p("text Bea that I'll be ten minutes late",'task','nba',('actor','recipient','object'),('quantity','time'))],
54:[
p('The demo ran long and I lost the thread around the permissions screen','fact','nb',('experiencer','object')),
p('maybe the examples need labels','tentative_idea','nb',('object',)),
p(['did Chris ever send Dana the access list','access list question still open'],'question','nb',('actor','recipient','object'),(), 'unresolved'),
p('call the dentist','task','nba',('actor','object')),
p('the room was freezing','fact','nb',('object',)),
p('before I close this: replace the porch bulb','task','nba',('actor','object'),('trigger',))],
56:[p('Remember to ask her about the earlier version','task','nba',('actor','recipient','object'),(), 'dangling')],
69:[
p("Send the cracked display's warranty paperwork before Friday",'task','nba',('actor','object'),('deadline','object_modifier')),
p('Need to get that damage claim filed by Friday','task','n',('actor','object'),('deadline',),'none',1)],
74:[
p('inventory the display easels','task','nba',('actor','object')),
p('replenish packing paper','task','nba',('actor','object')),
p('document the repaired frames','task','nba',('actor','object'),('object_modifier',)),
p('take the loan agreement to the archive','task','na',('actor','object'),('destination',)),
p('rinse the watercolor cups','task','nba',('actor','object')),
p('pair the translation headsets','task','nba',('actor','object')),
p('portion the soup into freezer containers','task','nba',('actor','object'),('destination',)),
p('secure the mailbox flag before pickup','task','nba',('actor','object'),('trigger',))],
75:[
p('Before the open house doors unlock, upload the revised floor plan','task','nba',('actor','object'),('trigger',)),
p(['Before the open house doors unlock','call the lighting supplier'],'task','nba',('actor','object'),('trigger',)),
p("I still don't know whether the west window was measured or only photographed",'question','nb',('object',),(), 'unresolved'),
p('The folding screens looked uneven after setup','fact','nb',('object',),('time',)),
p('Maybe place the visitor cards near the exit','tentative_idea','nb',('object',),('destination',)),
p('Ren said Salma handed the spare clips to the installation lead','fact','nb',('speaker','actor','recipient','object'))]
}

def spans(text,quotes):
    out=[]; cursor=0
    for q in quotes:
        i=text.find(q,cursor)
        if i<0: i=text.find(q)
        if i<0: raise ValueError(f'quote not found: {q!r}')
        out.append({'start':i,'end':i+len(q),'text':q}); cursor=i+len(q)
    return out

def main():
    records=[json.loads(x) for x in CORPUS.read_text(encoding='utf-8').splitlines()]
    rows=[]; total=0; positive_dup=0; pairs=0
    for rid in IDS:
        text=records[rid-1]['input']; props=[]
        for i,x in enumerate(A[rid],1):
            if x['state'] not in STATES or not set(x['roles'])<=ROLES or not set(x['qualifiers'])<=QUALS: raise ValueError(rid)
            fields=[{'n':'narrative','b':'bullet','a':'action'}[c] for c in x['fields']]
            if fields != [f for f in FIELDS if f in fields]: raise ValueError(f'{rid}:{i} fields')
            if x['state']!='task' and 'action' in fields: raise ValueError(f'{rid}:{i} non-task action')
            if x['duplicate_of'] is not None and not (1<=x['duplicate_of']<i): raise ValueError(f'{rid}:{i} duplicate')
            props.append({'proposition_id':f'p{i:02d}','source_character_spans':spans(text,x['quotes']),
                          'state':x['state'],'roles':x['roles'],'qualifiers':x['qualifiers'],
                          'coreference_status':x['coreference'],'duplicate_of':None if x['duplicate_of'] is None else f"p{x['duplicate_of']:02d}",
                          'required_output_fields':fields})
        n=len(props); total+=n; pairs+=n*(n-1)//2; positive_dup+=sum(p['duplicate_of'] is not None for p in props)
        rows.append({'record_locator':f'comparator:{rid:03d}','source_input':text,'propositions':props,
                     'reviewer':'ChatGPT','review_status':'pending_claude_independent_annotation'})
    OUT.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8',newline='\n')
    receipt={'status':'chatgpt_pass_pending_independent_annotation','record_count':len(rows),'proposition_count':total,
             'ordered_duplicate_pair_count':pairs,'positive_duplicate_count':positive_dup,
             'positive_duplicate_rate':positive_dup/pairs,'annotation_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
             'max_propositions_per_record':max(len(r['propositions']) for r in rows),'compute_authorized':False}
    RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n'); print(json.dumps(receipt,indent=2))

if __name__=='__main__': main()
