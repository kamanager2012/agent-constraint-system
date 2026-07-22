#!/usr/bin/env python3
import json

# Fix bash_dangerous.json: history clear and HISTFILE unset are anti-forensic, should be block
with open('bash_dangerous.json') as f:
    data = json.load(f)
for s in data['scenarios']:
    if s['id'] in ('bash-028', 'bash-029'):
        s['expected'] = 'block'
with open('bash_dangerous.json', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')

# Fix bypass_attempts.json: xxd, openssl, nc are now caught by new patterns
with open('bypass_attempts.json') as f:
    data = json.load(f)
for s in data['scenarios']:
    if s['id'] in ('bypass-013', 'bypass-014', 'bypass-019'):
        s['expected'] = 'block'
with open('bypass_attempts.json', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')

print("Fixed scenario expectations")
