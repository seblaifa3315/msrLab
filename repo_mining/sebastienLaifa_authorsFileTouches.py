import json
import requests
import csv
import os
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()

# ----------------------------
# Config
# ----------------------------
repo_name = 'scottyab/rootbeer'
lstTokens = [os.getenv("GITHUB_TOKEN")]
source_files_csv = 'data/file_rootbeer.csv'  # output from CollectFiles.py
output_csv = 'data/authors_file_touches.csv'

# Creates a data directory if it doesn’t exist
if not os.path.exists("data"):
    os.makedirs("data")

# ----------------------------
# GitHub authentication
# ----------------------------
def github_auth(url, lsttoken, ct):
    jsonData = None
    try:
        ct = ct % len(lsttoken)
        headers = {'Authorization': 'Bearer {}'.format(lsttoken[ct])}
        request = requests.get(url, headers=headers)
        jsonData = json.loads(request.content)
        ct += 1
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return jsonData, ct

# ----------------------------
# Read source files from CSV
# ----------------------------
def read_source_files(file_path):
    files = []
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            filename = row[0]
            files.append(filename)
    return files

# ----------------------------
# Collect authors and dates for each file
# ----------------------------
def collect_authors_dates(files, lsttokens, repo):
    result = defaultdict(list)
    ct = 0  # token counter

    for filename in files:
        print(f"Processing file: {filename}")
        ipage = 1
        while True:
            commits_url = f'https://api.github.com/repos/{repo}/commits?path={filename}&page={ipage}&per_page=100'
            json_commits, ct = github_auth(commits_url, lsttokens, ct)

            if not json_commits or len(json_commits) == 0:
                break

            # iterate through commits
            for commit_obj in json_commits:
                if not isinstance(commit_obj, dict) or 'sha' not in commit_obj:
                    continue  # skip invalid objects
                sha = commit_obj['sha']
                sha_url = f'https://api.github.com/repos/{repo}/commits/{sha}'
                sha_details, ct = github_auth(sha_url, lsttokens, ct)

                if not sha_details or 'commit' not in sha_details or 'author' not in sha_details['commit']:
                    continue

                author_name = sha_details['commit']['author']['name']
                commit_date = sha_details['commit']['author']['date']
                result[filename].append((author_name, commit_date))
            ipage += 1
    return result

# ----------------------------
# Write results to CSV
# ----------------------------
def save_to_csv(result, output_file):
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "Author", "Date"])
        for filename, touches in result.items():
            for author, date in touches:
                writer.writerow([filename, author, date])

# ----------------------------
# Main
# ----------------------------
source_files = read_source_files(source_files_csv)
authors_dates = collect_authors_dates(source_files, lstTokens, repo_name)
save_to_csv(authors_dates, output_csv)
print(f"Saved authors and dates to {output_csv}")
