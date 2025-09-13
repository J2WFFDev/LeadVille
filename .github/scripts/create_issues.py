import os
from github import Github

issues_file = os.environ.get('INPUT_ISSUES_FILE', '.github/ISSUES_TO_CREATE.md')
repo = os.environ['GITHUB_REPOSITORY']
token = os.environ['GITHUB_TOKEN']
g = Github(token)
r = g.get_repo(repo)

with open(issues_file, encoding='utf-8') as f:
    content = f.read()

# Simple parser: split by '## Issue' (customize as needed)
issues = [i for i in content.split('## Issue') if i.strip()]
for idx, issue in enumerate(issues, 1):
    lines = issue.splitlines()
    title = next((l for l in lines if l.startswith('[')), f'Imported Issue {idx}')
    body = '\n'.join(lines)
    try:
        r.create_issue(title=title, body=body)
        print(f'Created: {title}')
    except Exception as e:
        print(f'Failed to create {title}: {e}')
