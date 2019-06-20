import sys
import yaml
import jsonschema
import csv

from JiraController import JiraController
from JiraController import progress_bar

STORY_POINTS_KEY='customfield_10005'
CUSTOMER_KEY='customfield_10400'
SPRINT_KEY='customfield_10007'
ASSIGNED_TEAM_KEY='customfield_12001'
TASK_SIZE_KEY='customfield_11900'
PEER_REVIEWERS_KEY='customfield_10700'

'''
This schema is used to validate any config yamls.
'''
CONFIG_SCHEMA = {
    'type': 'object',
    'properties': {
        'config': {
            'type': 'object',
            'properties': {
                'board_key': {
                    'type': 'string',
                    'minLength': 1,
                },
                'assigned_team': {
                    'type': 'string',
                    'minLength': 1,
                },
                'customer': {
                    'type': 'string',
                    'minLength': 1,
                },
                'peer_reviewers': {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                    },
                    'minItems': 1,
                },
            },
            'required': ['board_key', 'assigned_team', 'customer', 'peer_reviewers'],
            'additionalProperties': False,
        },
    },
    'required': ['config'],
    'additionalProperties': False,
}


def main():
    if len(sys.argv) != 6:
        print('expected: <endpoint> <jira-email> <jira-api-token> <config-path> <tasks-path>')
        return

    jira_endpoint = sys.argv[1]
    jira_username = sys.argv[2]
    jira_password = sys.argv[3]
    config_path = sys.argv[4]
    tasks_path = sys.argv[5]

    config_file = yaml.load(open(config_path, 'r'))
    jsonschema.validate(config_file, CONFIG_SCHEMA)

    config = config_file['config']

    controller = JiraController(jira_endpoint, jira_username, jira_password,
                                config['board_key'], config['assigned_team'], None,
                                config['customer'], config['peer_reviewers'])

    num_tasks = 0
    with open(tasks_path, 'r') as tasks_file:
        next(tasks_file)
        num_tasks = sum(1 for _ in tasks_file)

    with open(tasks_path, 'r') as tasks_file:
        csv_reader = csv.reader(tasks_file, delimiter=',')

        # Skip header line.
        next(csv_reader)

        task_idx = 0
        for row in csv_reader:
            assert len(row) == 3
            story_key = row[0]
            task_summary = row[1]
            hours = int(row[2])

            response = controller.create_sub_task(story_key, task_summary, hours=hours)
            controller.approve_issue(response['key'])
            progress_bar('Progress', task_idx + 1, num_tasks, bar_length=20)
            task_idx += 1
        sys.stdout.write('\n')


if __name__ == "__main__":
    main()
