#!/usr/bin/env python3
"""Build the static data bundle used by the Evilwiki GitHub Pages viewer."""
from __future__ import annotations

import argparse
import gzip
import json
import shutil
import zlib
from collections import Counter, defaultdict
from pathlib import Path

SUMMARY_KEYS = (
    'rev_id','page_id','wiki','name','seq','rcs_rev','body_len','lines','diff_base','diff_base_reason',
    'label','ip16','time','time_grade','winning_clock','request_action','change_summary','body_encoding'
)
EVENT_SUMMARY_KEYS = (
    'event_id','event_type','time','time_grade','wiki','page','page_key','revision_ref','related_event_id',
    'relation_type','ip16','request_action','param_family','success_observed','change_summary','actor_label','page_held'
)


def read_json_gz(path: Path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def read_jsonl_gz(path: Path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')


def write_jsonl_gz(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, 'wt', encoding='utf-8', compresslevel=9, newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')))
            f.write('\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source', nargs='?', default='../../evilwiki_viewer/data', help='source data folder from the local viewer')
    ap.add_argument('--out', default='../data', help='output data folder')
    ap.add_argument('--shards', type=int, default=16)
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    source = (here / args.source).resolve()
    out = (here / args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / 'revisions').mkdir(exist_ok=True)

    manifest = read_json_gz(source / 'manifest.json.gz')
    pages = list(read_jsonl_gz(source / 'pages.jsonl.gz'))
    labels = list(read_jsonl_gz(source / 'labels.jsonl.gz'))
    events = list(read_jsonl_gz(source / 'events.jsonl.gz'))

    shard_rows = [[] for _ in range(args.shards)]
    summaries = []
    rev_times = []
    wiki_rev_counts = Counter()

    for rev in read_jsonl_gz(source / 'revisions.jsonl.gz'):
        shard = zlib.crc32(rev['page_id'].encode('utf-8')) % args.shards
        summary = {k: rev.get(k) for k in SUMMARY_KEYS}
        summary['shard'] = shard
        summaries.append(summary)
        shard_rows[shard].append(rev)
        wiki_rev_counts[rev.get('wiki')] += 1
        if rev.get('time'):
            rev_times.append(rev['time'])

    wiki_page_counts = Counter(p.get('wiki') for p in pages)
    event_type_counts = Counter(e.get('event_type') for e in events)
    page_family_counts = Counter(p.get('page_family') or 'unknown' for p in pages)

    meta = {
        'format_version': 1,
        'viewer_mode': 'github-pages-static',
        'generated_at': manifest.get('generated_at'),
        'cut': manifest.get('cut'),
        'counts': {
            'pages': len(pages),
            'revisions': len(summaries),
            'labels': len(labels),
            'events': len(events),
        },
        'wikis': [
            {'wiki': w, 'pages': wiki_page_counts[w], 'revisions': wiki_rev_counts[w]}
            for w in sorted(wiki_page_counts, key=lambda w: (-wiki_page_counts[w], w or ''))
        ],
        'event_types': dict(event_type_counts),
        'page_families': page_family_counts.most_common(20),
        'body_bytes': manifest.get('body_bytes', {}).get('total', {}).get('value'),
        'date_range': {'first': min(rev_times) if rev_times else None, 'last': max(rev_times) if rev_times else None},
        'human_handles': [l.get('label') for l in labels if l.get('is_human_handle')],
        'facts': manifest.get('facts', {}),
        'revision_shards': args.shards,
    }

    write_json(out / 'meta.json', meta)
    shutil.copy2(source / 'pages.jsonl.gz', out / 'pages.jsonl.gz')
    shutil.copy2(source / 'labels.jsonl.gz', out / 'labels.jsonl.gz')
    shutil.copy2(source / 'events.jsonl.gz', out / 'events.jsonl.gz')
    shutil.copy2(source / 'manifest.json.gz', out / 'manifest.json.gz')
    write_jsonl_gz(out / 'revision-summaries.jsonl.gz', summaries)
    for i, rows in enumerate(shard_rows):
        write_jsonl_gz(out / 'revisions' / f'{i:02d}.jsonl.gz', rows)

    index = {
        'revision_shards': args.shards,
        'shard_counts': [len(x) for x in shard_rows],
        'files': {
            'pages': 'pages.jsonl.gz',
            'labels': 'labels.jsonl.gz',
            'events': 'events.jsonl.gz',
            'revision_summaries': 'revision-summaries.jsonl.gz',
            'revision_shard_pattern': 'revisions/{shard}.jsonl.gz',
        },
    }
    write_json(out / 'index.json', index)
    print(f'Built {len(pages):,} pages, {len(summaries):,} revisions, {len(events):,} events into {args.shards} shards.')


if __name__ == '__main__':
    main()
