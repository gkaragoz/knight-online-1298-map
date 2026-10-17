import re, json, sys

def parse_inserts(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    out = {}
    # each statement: INSERT INTO [T] ([c1],...) VALUES\n(...),\n(...);
    for m in re.finditer(r'INSERT INTO \[(\w+)\]\s*\(([^)]*)\)\s*VALUES\s*', txt):
        table = m.group(1)
        cols = [c.strip().strip('[]') for c in m.group(2).split(',')]
        i = m.end()
        rows = out.setdefault(table, [])
        n = len(txt)
        while i < n:
            while i < n and txt[i] in ' \r\n\t,': i += 1
            if i >= n or txt[i] != '(': break
            i += 1
            vals = []
            while True:
                while txt[i] in ' \t': i += 1
                c = txt[i]
                if c == 'N' and txt[i+1] == "'" or c == "'":
                    if c == 'N': i += 1
                    i += 1; s = []
                    while True:
                        if txt[i] == "'":
                            if txt[i+1] == "'": s.append("'"); i += 2; continue
                            i += 1; break
                        s.append(txt[i]); i += 1
                    vals.append(''.join(s))
                else:
                    j = i
                    while txt[j] not in ',)': j += 1
                    tok = txt[i:j].strip(); i = j
                    if tok.upper() == 'NULL': vals.append(None)
                    else:
                        try: vals.append(int(tok))
                        except ValueError:
                            try: vals.append(float(tok))
                            except ValueError: vals.append(tok)
                while txt[i] in ' \t': i += 1
                if txt[i] == ',': i += 1; continue
                if txt[i] == ')': i += 1; break
            rows.append(dict(zip(cols, vals)))
            while i < n and txt[i] in ' \r\n\t': i += 1
            if i < n and txt[i] == ';': i += 1; break
    return out

if __name__ == '__main__':
    base = '/home/claude/open-ko/ext/OpenKO-db/ManualSetup/'
    res = {}
    for f in ['6_InsertData_K_NPCPOS.sql','6_InsertData_K_MONSTER.sql','6_InsertData_K_NPC.sql','6_InsertData_ZONE_INFO.sql']:
        r = parse_inserts(base + f)
        for k, v in r.items(): res.setdefault(k, []).extend(v)
    for k, v in res.items(): print(k, len(v))
    json.dump(res, open(sys.argv[1], 'w'))
