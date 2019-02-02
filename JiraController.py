import json
import requests
import sys

STORY_POINTS_KEY='customfield_10005'
CUSTOMER_KEY='customfield_10400'
SPRINT_KEY='customfield_10007'
ASSIGNED_TEAM_KEY='customfield_12001'
TASK_SIZE_KEY='customfield_11900'
PEER_REVIEWERS_KEY='customfield_10700'

'''
  TODO: Get sprint ID from a sprint name. Currently sprint ID is the sprint name(e.g '#86')
  plus 122.
'''
class JiraController:
    # TODO: Get sprint ID from a sprint name. Currently sprint ID is the sprint name(e.g '#86') plus 122.
    @staticmethod
    def sprint_id_from_name(sprint_name):
        return sprint_name + 122

    @staticmethod
    def size_to_minutes(size):
        size_map = {
            'XL': 8 * 60,
            'L': 6 * 60,
            'M': 4 * 60,
            'S': 2 * 60,
            'XS': 1 * 60
        }
        if size not in size_map:
            raise RuntimeError('Unrecognised size \'%s\'' % size)
        return size_map[size]

    def __init__(self, jira_endpoint, jira_username, jira_password,
                 project, assigned_team, sprint, customer, peer_reviewers):
        self.endpoint = jira_endpoint
        self.username = jira_username
        self.password = jira_password
        self.project = project
        self.assigned_team = assigned_team

        # TODO: Find a method to get sprint ID from sprint name.
        # self.sprint_id = JiraController.sprint_id_from_name(sprint)

        self.sprint_id = sprint
        self.customer = customer
        self.peer_reviewers = peer_reviewers

    def send_jira_request(self, request_body):
        response = requests.post('%s/rest/api/2/issue/' % self.endpoint,
                                 json=request_body,
                                 headers={
                                     'Content-Type': 'application/json'
                                 },
                                 auth=(self.username, self.password))

        if response.status_code != 201:
            raise RuntimeError('User story creation failed, %s, "%s", %s' % (response.status_code, response.reason,
                                                                             response.json()))
        return response.json()

    def create_user_story(self, summary, description, acceptance_criteria, points):
        description_str = 'h6. Description:\n' + description + '\n\nh6.Acceptance Criteria:\n* ' + \
                          '\n* '.join(acceptance_criteria) + '\n'

        request_body = {
            'fields': {
                'project': {
                    'key': self.project
                },
                'issuetype': {
                    'name': 'User Story'
                },
                'summary': summary,
                'description': description_str,
                SPRINT_KEY: self.sprint_id,
                STORY_POINTS_KEY: points,
                CUSTOMER_KEY: {
                    'name': self.customer
                },
                PEER_REVIEWERS_KEY: [
                    {'name': reviewer} for reviewer in self.peer_reviewers
                ]
            }
        }

        return self.send_jira_request(request_body)

    def create_sub_task(self, parent_key, summary, size):
        request_body = {
            'fields': {
                'project': {
                    'key': self.project
                },
                'issuetype': {
                    'id': '5'
                },
                'parent': {
                    'key': parent_key
                },
                'summary': summary,
                CUSTOMER_KEY: {
                    'name': self.customer
                },
                TASK_SIZE_KEY: {
                    'value': size
                },
                ASSIGNED_TEAM_KEY: {
                    'name': self.assigned_team,
                    'self': '%s/rest/api/2/group?groupname=%s' % (self.endpoint, self.assigned_team)
                },
                PEER_REVIEWERS_KEY: [
                    {'name': reviewer} for reviewer in self.peer_reviewers
                ],
                'timetracking': {
                    'originalEstimate': JiraController.size_to_minutes(size)
                }
            }
        }
        return self.send_jira_request(request_body)


def progress_bar(text, value, end_value, bar_length=20):
    percent = float(value) / end_value
    arrow = '-' * int(round(percent * bar_length)-1) + '>'
    spaces = ' ' * (bar_length - len(arrow))

    sys.stdout.write('\r{0}: [{1}] {2}%'.format(text, arrow + spaces, int(round(percent * 100))))
    sys.stdout.flush()
