from fastapi.testclient import TestClient
import main as m

c = TestClient(m.app)

print('=== SAME-DOMAIN Reply-To (should be mailbox divergence, NOT domain mismatch) ===')
r = c.post('/api/classify-email', json={
    'emailBody': 'Hello',
    'sender': 'security@example.net',
    'subject': 'test',
    'headers': [
        {'name': 'From', 'value': 'Security <security@example.net>'},
        {'name': 'Reply-To', 'value': 'support@example.net'}
    ],
    'attachments': []
})
res = r.json()
print('SCORE:', res['score'], 'SAFETY:', res['safety'])
for f in res['indicators']:
    print('  INDICATOR:', f['description'], '| type:', f.get('type'))
print('RISK_FACTORS:')
for f in res['risk_factors']:
    print('  FACTOR:', f['factor'], 'score:', f['score'])

print()
print('=== DIFFERENT-DOMAIN Reply-To (should get domain mismatch penalty) ===')
r2 = c.post('/api/classify-email', json={
    'emailBody': 'Hello',
    'sender': 'security@example.net',
    'subject': 'test',
    'headers': [
        {'name': 'From', 'value': 'Security <security@example.net>'},
        {'name': 'Reply-To', 'value': 'support@other.net'}
    ],
    'attachments': []
})
res2 = r2.json()
print('SCORE:', res2['score'], 'SAFETY:', res2['safety'])
for f in res2['indicators']:
    print('  INDICATOR:', f['description'], '| type:', f.get('type'))
print('RISK_FACTORS:')
for f in res2['risk_factors']:
    print('  FACTOR:', f['factor'], 'score:', f['score'])

print()
print('=== SAME Full Address (no Reply-To finding expected) ===')
r3 = c.post('/api/classify-email', json={
    'emailBody': 'Hello',
    'sender': 'security@example.net',
    'subject': 'test',
    'headers': [
        {'name': 'From', 'value': 'Security <security@example.net>'},
        {'name': 'Reply-To', 'value': 'security@example.net'}
    ],
    'attachments': []
})
res3 = r3.json()
print('SCORE:', res3['score'], 'SAFETY:', res3['safety'])
for f in res3['indicators']:
    if 'Reply-To' in f['description']:
        print('  INDICATOR:', f['description'])
print('(no reply-to indicator above = correct)')
