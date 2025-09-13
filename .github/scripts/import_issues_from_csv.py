import os
import pandas as pd
from github import Github

csv_path = '.github/issues_to_create.csv'
repo_name = os.environ['GITHUB_REPOSITORY']
token = os.environ['GITHUB_TOKEN']

g = Github(token)
repo = g.get_repo(repo_name)

df = pd.read_csv(csv_path)
for _, row in df.iterrows():
    title = row['Title']
    body = row['Body']
    labels = [l.strip() for l in str(row['Labels']).split(',') if l.strip()]
    try:
        repo.create_issue(title=title, body=body, labels=labels)
        print(f"Created: {title}")
    except Exception as e:
        print(f"Failed to create {title}: {e}")
