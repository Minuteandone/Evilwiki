#!/usr/bin/env python3
"""Integrity checks for the generated static Evilwiki Pages bundle."""
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'


def jsonl(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

meta = json.loads((DATA / 'meta.json').read_text(encoding='utf-8'))
pages = list(jsonl(DATA / 'pages.jsonl.gz'))
labels = list(jsonl(DATA / 'labels.jsonl.gz'))
events = list(jsonl(DATA / 'events.jsonl.gz'))
summaries = list(jsonl(DATA / 'revision-summaries.jsonl.gz'))

assert len(pages) == meta['counts']['pages']
assert len(labels) == meta['counts']['labels']
assert len(events) == meta['counts']['events']
assert len(summaries) == meta['counts']['revisions']

page_ids = {p['page_id'] for p in pages}
seen_revs = set()
by_page = defaultdict(list)
shard_counts = Counter()

for shard in range(meta['revision_shards']):
    rows = list(jsonl(DATA / 'revisions' / f'{shard:02d}.jsonl.gz'))
    shard_counts[shard] = len(rows)
    for r in rows:
        assert r['rev_id'] not in seen_revs
        seen_revs.add(r['rev_id'])
        assert r['page_id'] in page_ids
        by_page[r['page_id']].append(r)

assert len(seen_revs) == len(summaries)
summary_ids = {r['rev_id'] for r in summaries}
assert seen_revs == summary_ids

summary_shards = defaultdict(set)
for s in summaries:
    summary_shards[s['page_id']].add(s['shard'])
assert all(len(v) == 1 for v in summary_shards.values()), 'A page spans multiple body shards'

for p in pages:
    assert len(by_page[p['page_id']]) == p['n_revs'], (p['page_id'], len(by_page[p['page_id']]), p['n_revs'])

print('QA PASS')
print(f"pages={len(pages):,} labels={len(labels):,} events={len(events):,} revisions={len(summaries):,}")
print(f"shards={meta['revision_shards']} min_revisions_per_shard={min(shard_counts.values())} max={max(shard_counts.values())}")
