# JIRA Sprint Creator

This tool exists to reduce the overhead of manually creating stories and
sub tasks in JIRA by pulling the data from a yaml file and using REST
requests to create the required issues.

## Requirements

```
pip3 install pyyaml jsonschema
```

## Usage

The sprint creator can be used as follows.
```
python3 sprint-creator.py <endpoint> <jira-username> <jira-password> <sprint-yaml>
```

For example.
```
python3 sprint-creator.py https://priapus.atlassian.net myusername mypassword ./sprint.yaml
```
