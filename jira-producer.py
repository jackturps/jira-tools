import json
import os
import requests
import time
import sys
import yaml

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
    def _sprint_id_from_name(sprint_name):
        return sprint_name + 122

    @staticmethod
    def _size_to_minutes(size):
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
        self.sprint_id = JiraController._sprint_id_from_name(sprint)
        self.customer = customer
        self.peer_reviewers = peer_reviewers


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

        response = requests.post('%s/rest/api/2/issue/' % (self.endpoint),
                                 json=request_body,
                                 headers={
                                     'Content-Type': 'application/json'
                                 },
                                 auth=(self.username, self.password))

        if response.status_code != 201:
            raise RuntimeError('User story creation failed, %s, "%s", %s' % (response.status_code, response.reason, response.json()))
        return response.json()


    def create_sub_task(self, parent_key, summary):
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
                    'name': 'jack.turpitt'
                },
                TASK_SIZE_KEY: {
                    'value': 'XL'
                },
                ASSIGNED_TEAM_KEY: {
                    'name': 'rapid'
                },
                PEER_REVIEWERS_KEY: [
                    {
                        'name': 'jack.turpitt'
                    }
                ],
                'timetracking': {
                    'originalEstimate': '10'
                }
            }
        }

        response = requests.post('%s/rest/api/2/issue/' % (self.endpoint),
                                 json=request_body,
                                 headers={
                                     'Content-Type': 'application/json'
                                 },
                                 auth=(self.username, self.password))

        if response.status_code != 201:
            print(json.dumps(response.json(), indent=2))
            print('\n\n')
            raise RuntimeError('User story creation failed, %s, "%s", %s' % (response.status_code, response.reason, response.json()))
        return response.json()



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

    config_file = yaml.load(open(config_path, 'r'))
    config = config_file['config']
    stories = config_file['stories']

    controller = JiraController(jira_endpoint, jira_username, jira_password,
                                config['board_key'], config['assigned_team'], config['sprint'],
                                config['customer'], config['peer_reviewers'])

    for story_idx, story in enumerate(stories):

        total_minute = sum( [ JiraController._size_to_minutes(task['size']) for task in story['tasks'] ] )
        print(total_minute)
        story_json = controller.create_user_story(story['summary'], story['description'],
                                                  story['acceptance_criteria'], total_minute // 60)


        for task in story['tasks']:





        # story_id = controller.create_user_story(story['title'], story['acceptance-criteria'], story['points'])
        # for task_idx, task in enumerate(story['tasks']):
        #     progressBar('Story %d Progress' % story_idx, task_idx, len(story['tasks']) - 1, bar_length=20)
        #     controller.create_task(task['title'], task['size'], story_id)
        # sys.stdout.write('\n')


if __name__ == "__main__":
    main()
