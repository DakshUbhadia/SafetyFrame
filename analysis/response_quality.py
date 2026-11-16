"""Post-collection response-status diagnostics; no rescoring or response text release."""
from collections import Counter

from harness.artifacts import digest,read_json


def metadata(response,cap):
    raw=response.get('raw') or {}
    summary=response.get('summary') or {}
    text=response.get('text') or ''
    usage=summary.get('usage') or {}
    details=usage.get('output_tokens_details') or {}
    incomplete=raw.get('incomplete_details') or {}
    reason=incomplete.get('reason') if isinstance(incomplete,dict) else None
    output=raw.get('output') or []
    message=''.join(part.get('text','') for item in output
                   if isinstance(item,dict) and item.get('type')=='message'
                   for part in item.get('content',[])
                   if isinstance(part,dict) and part.get('type')=='output_text')
    status=raw.get('status',summary.get('status'))
    return dict(response_status=status,incomplete_reason=reason,emitted_text_characters=len(text),
        raw_message_characters=len(message),
        output_types=sorted({item['type'] for item in output
                             if isinstance(item,dict) and isinstance(item.get('type'),str)}),
        output_tokens=usage.get('output_tokens'),reasoning_tokens=details.get('reasoning_tokens'),output_token_cap=cap,
        extraction_mismatch=bool(message.strip()) and not bool(text.strip()),
        reasoning_only_budget_exhaustion=(status=='incomplete' and reason=='max_output_tokens'
            and not text.strip() and not message.strip()
            and usage.get('output_tokens')==cap and details.get('reasoning_tokens')==cap))


def enrich(dataset,root,cap):
    """Attach metadata only after raw records have passed the shared integrity audit."""
    for record in dataset['records']:
        for attempt in record['attempts']:
            outcome=read_json(root/attempt['file'])
            if digest(outcome)!=attempt['outcome_hash']: raise ValueError('Outcome changed during diagnostic audit')
            if 'result' not in outcome: continue
            turn=record['turns'][outcome['turn']-1]
            if digest(outcome['result'])!=turn['response_hash']: raise ValueError('Diagnostic response hash mismatch')
            info=metadata(outcome['result'],cap)
            if info['extraction_mismatch']:
                raise ValueError('Raw final text exists but was not extracted; review integration before interpretation')
            turn['response_metadata']=info
        if any('response_metadata' not in turn for turn in record['turns']):
            raise ValueError('Observed response lacks audited quality metadata')
    return dataset


def summarize(records,conditions):
    rows=[]
    for c in conditions:
        for number in (1,2):
            turns=[r['turns'][number-1] for r in records
                   if r['trajectory']['condition']==c and len(r['turns'])>=number]
            known=[t['response_metadata'] for t in turns if 'response_metadata' in t]
            rows.append(dict(condition=c,turn=number,observed_responses=len(turns),metadata_known=len(known),
                format_failures=sum(not t['format_success'] for t in turns),
                incomplete_responses=sum(m['response_status']=='incomplete' for m in known),
                reasoning_only_budget_exhaustions=sum(m['reasoning_only_budget_exhaustion'] for m in known),
                empty_final_text=sum(m['emitted_text_characters']==0 for m in known),
                extraction_mismatches=sum(m['extraction_mismatch'] for m in known)))
    known=[t['response_metadata'] for r in records for t in r['turns'] if 'response_metadata' in t]
    return dict(post_collection_diagnostic=True,rows=rows,metadata_known=len(known),
        observed_responses=sum(len(r['turns']) for r in records),
        reasoning_only_budget_exhaustions=sum(m['reasoning_only_budget_exhaustion'] for m in known),
        output_token_caps=sorted({m['output_token_cap'] for m in known}),
        extraction_mismatches=sum(m['extraction_mismatch'] for m in known),
        statuses=dict(Counter(m['response_status'] for m in known)),
        scoring_changed=False,additional_inference=False)
