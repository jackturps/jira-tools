import json
import os
import requests
import time
import sys
import yaml

class JiraController:
    def __init__(self, jira_endpoint, jira_username, jira_password):
        self.endpoint = jira_endpoint
        self.username = jira_username
        self.password = jira_password


    def create_issue(project, issue_type, summary, descrition='', **kwargs):
        request_body = {
            'fields': {
                'project': {
                    'key': 'AETH'
                },
                'issuetype': {
                    'name': issue_type
                },
                'summary': summary,
                'description': descrition,
                **kwargs
            }
        }
        response = requests.post('%s/rest/api/2/issue/' % (self.endpoint),
                                 json=request_body,
                                 headers={'Content-Type': 'application/json'},
                                 auth=(self.username, self.password))

        if response.status_code != 201:
            raise RuntimeError('issue creation failed, %s, "%s"' % (response.status_code, response.reason))
        return response.json()


    def link_issues(key1, key2):
        request_body = {
            "type": {
                "name": "Relates"
            },
            "inwardIssue": {
                "key": key1
            },
            "outwardIssue": {
                "key": key2
            }
        }

        response = requests.post('%s/rest/api/2/issueLink/' % (self.endpoint),
                                 json=request_body,
                                 headers={'Content-Type': 'application/json'},
                                 auth=(self.username, self.password))

        if response.status_code != 201:
            raise RuntimeError('issue linking failed, %s, "%s"' % (response.status_code, response.reason))


    def create_user_story(title, criterias, points):
        print('creating "%s" with criteria:' % title)

        # Create the JIRA formatted string for acceptance criteria.
        criteria_str = 'h6. Acceptance Criteria:\n'
        for criteria in criterias:
            criteria_str += '* %s\n' % criteria

        response_body = create_issue('AETH', 'User Story', title, criteria_str, customfield_10005=points)
        return response_body['key']


    def create_task(task, size, story_id):
        response_body = create_issue('AETH', 'Scrum Task', task, customfield_11900={'value': size})
        link_issues(story_id, response_body['key'])

def progressBar(text, value, endvalue, bar_length=20):
    percent = float(value) / endvalue
    arrow = '-' * int(round(percent * bar_length)-1) + '>'
    spaces = ' ' * (bar_length - len(arrow))

    sys.stdout.write('\r{0}: [{1}] {2}%'.format(text, arrow + spaces, int(round(percent * 100))))
    sys.stdout.flush()


def main():
    if len(sys.argv) != 5:
        print('expected: <endpoint> <jira-username> <jira-password> <config-path>')
        return

    jira_endpoint = sys.argv[1]
    jira_username = sys.argv[2]
    jira_password = sys.argv[3]
    config_path = sys.argv[4]

    config = yaml.load(open(config_path, 'r'))
    controller = JiraController(jira_endpoint, jira_username, jira_password)

    for story_idx, story in enumerate(config['user-stories']):
        story_id = controller.create_user_story(story['title'], story['acceptance-criteria'], story['points'])
        for task_idx, task in enumerate(story['tasks']):
            progressBar('Story %d Progress' % story_idx, task_idx, len(story['tasks']) - 1, bar_length=20)
            controller.create_task(task['title'], task['size'], story_id)
        sys.stdout.write('\n')


if __name__ == "__main__":
    main()
