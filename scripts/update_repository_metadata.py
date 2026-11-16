"""Preview or apply the reviewed GitHub About description and topics.

Defaults to a local preview. --apply uses existing Git credentials and verifies
the stored values; credentials are never printed or written to the receipt.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

ROOT = Path(__file__).resolve().parents[1]


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def credential():
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        return token
    result = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                            text=True, capture_output=True, cwd=ROOT)
    fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    if result.returncode or not fields.get('password'):
        raise RuntimeError('GitHub credentials unavailable; metadata has not been updated')
    return fields['password']


def update(config, token):
    base = 'https://api.github.com/repos/' + config['repository']
    opener = build_opener(NoRedirect())

    def request(method, suffix='', payload=None):
        req = Request(base + suffix, method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                     'Content-Type': 'application/json', 'User-Agent': 'SafetyFrame-presentation-update'})
        try:
            with opener.open(req, timeout=30) as response:
                return json.load(response)
        except HTTPError as exc:
            raise RuntimeError(f'GitHub {method} {suffix or "repository"} returned HTTP {exc.code}') from None
        except URLError:
            raise RuntimeError('GitHub connection failed; inspect remote state before retrying') from None

    before = request('GET')
    if before.get('full_name', '').casefold() != config['repository'].casefold():
        raise RuntimeError('Remote repository identity differs from the reviewed target')
    request('PATCH', payload={'description': config['description']})
    request('PUT', '/topics', {'names': config['topics']})
    after = request('GET')
    topics = request('GET', '/topics')['names']
    if after['description'] != config['description'] or set(topics) != set(config['topics']):
        raise RuntimeError('GitHub did not retain the requested metadata')
    receipt = dict(repository=after['full_name'], url=after['html_url'],
        verified_at_utc=datetime.now(timezone.utc).isoformat(),
        before={'description': before.get('description'), 'topics': before.get('topics', [])},
        after={'description': after['description'], 'topics': topics}, verified=True)
    destination = ROOT/'presentation/github_metadata_receipt.json'
    destination.write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    config = json.loads((ROOT/'presentation/github_metadata.json').read_text(encoding='utf-8'))
    if args.apply:
        receipt = update(config, credential())
        print(f"Verified GitHub description and {len(receipt['after']['topics'])} topics for {receipt['repository']}")
    else:
        print(json.dumps(config, indent=2))


if __name__ == '__main__':
    main()
