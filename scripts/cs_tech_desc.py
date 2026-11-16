#!/usr/bin/env python3 -I
"""Print truncated descriptions for given course indexes: cs_tech_desc.py <school_id> <idx> [<idx> ...]"""
import json, sys
sid, idxs = sys.argv[1], [int(x) for x in sys.argv[2:]]
cs = json.load(open(f"phase2/courses/{sid}.json"))["courses"]
for i in idxs:
    c = cs[i]
    print(f"{i}\t{c['course_name']}\t{(c.get('description') or '(no description)')[:450]}\t{(c.get('prerequisites') or '')[:100]}")
