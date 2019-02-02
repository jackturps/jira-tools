# JIRA Sprint Creators

## Summary

These tool exists to reduce the overhead of manually creating stories and
sub tasks in JIRA by pulling the data from a yaml file and using REST
requests to create the required issues.

## Requirements

```
pip3 install pyyaml jsonschema
```

## Tools

### Regular Sprint Creator

#### Summary

The regular sprint creator is the most generic and flexible of the sprint creator tools
and gives you fine tuned control over task descriptions and sizes. The yaml is also
very readable.

#### Usage

The regular sprint creator can be used as follows.
```
python3 sprint-creator.py <endpoint> <jira-username> <jira-password> <sprint-yaml>
```

For example.
```
python3 sprint-creator.py https://priapus.atlassian.net myusername mypassword ./sprint.yaml
```

### Micro Sprint Creator

#### Summary

The micro sprint creator focuses on reducing the required input yaml to it's bare minimum.
It does this by compressing the tasks into two values and shortening all input keys.

#### Usage

The regular sprint creator can be used as follows.
```
python3 micro-sprint-creator.py <endpoint> <jira-username> <jira-password> <sprint-yaml>
```

For example.
```
python3 micro-sprint-creator.py https://priapus.atlassian.net myusername mypassword ./micro-sprint.yaml
```
