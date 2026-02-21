import os, json, urllib.request
API = os.environ.get('MATON_API_KEY')
if not API:
    raise SystemExit('MATON_API_KEY not set')

def get(url):
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {API}')
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

base = 'https://gateway.maton.ai/google-mail/gmail/v1/users/me'
listing = get(base + '/messages?q=is:unread&maxResults=10')
msgs = listing.get('messages', []) or []
print('UNREAD_COUNT', len(msgs))
out = []
for m in msgs:
    mid = m['id']
    data = get(base + f'/messages/{mid}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date')
    headers = {h['name']: h['value'] for h in data.get('payload', {}).get('headers', [])}
    out.append({
        'id': mid,
        'threadId': data.get('threadId'),
        'from': headers.get('From'),
        'subject': headers.get('Subject'),
        'date': headers.get('Date'),
        'snippet': data.get('snippet'),
    })
print(json.dumps(out, ensure_ascii=False, indent=2))
