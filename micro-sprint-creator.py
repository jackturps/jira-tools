import sys
import yaml
import jsonschema

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
                'sprint': {
                    'type': 'number',
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
            'required': ['board_key', 'assigned_team', 'sprint', 'customer', 'peer_reviewers'],
            'additionalProperties': False,
        },
        'stories': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'sum': {
                        'type': 'string',
                        'minLength': 1,
                    },
                    'desc': {
                        'type': 'string',
                        'minLength': 1,
                    },
                    'acc_cri': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                            'minLength': 1,
                        },
                        'minItems': 1,
                    },
                    'tasks': {
                        'type': 'integer',
                        'minimum': 1,
                    },
                    'sizes': {
                        'type': 'string',
                        'enum': ['XS', 'S', 'M', 'L', 'XL'],
                    },
                },
                'required': ['sum', 'acc_cri', 'tasks', 'sizes'],
                'additionalProperties': False,
            },
            'minItems': 1,
        }
    },
    'required': ['config', 'stories'],
    'additionalProperties': False,
}


def main():
    if len(sys.argv) != 5:
        print('expected: <endpoint> <jira-username> <jira-password> <config-path>')
        return

    jira_endpoint = sys.argv[1]
    jira_username = sys.argv[2]
    jira_password = sys.argv[3]
    config_path = sys.argv[4]

    config_file = yaml.load(open(config_path, 'r'))
    jsonschema.validate(config_file, CONFIG_SCHEMA)

    config = config_file['config']
    stories = config_file['stories']

    controller = JiraController(jira_endpoint, jira_username, jira_password,
                                config['board_key'], config['assigned_team'], config['sprint'],
                                config['customer'], config['peer_reviewers'])

    for story_idx, story in enumerate(stories):
        # Expand repeated tasks.
        expanded_tasks = []

        # for task in story['tasks']:
        repeat_count = story['tasks']
        for repeat_idx in range(repeat_count):
            tmp_task = {
                'summary': '%s pt. %s' % (story['sum'], repeat_idx + 1),
                'size': story['sizes']
            }
            expanded_tasks.append(tmp_task)

        # Default description to summary if it is not given.
        description_str = story['desc'] if 'desc' in story else story['sum']

        # Get the total number of time for a user story from it's tasks.
        total_minute = sum([JiraController.size_to_minutes(task['size']) for task in expanded_tasks])
        story_json = controller.create_user_story(story['sum'], description_str,
                                                  story['acc_cri'], total_minute // 60)

        # Create subtasks and attach them to the user story.
        task_parent = story_json['key']

        # Create all tasks for this story.
        for task_idx, task in enumerate(expanded_tasks):
            controller.create_sub_task(task_parent, task['summary'], task['size'])
            progress_bar('Story %d Progress' % story_idx, task_idx + 1, len(expanded_tasks), bar_length=20)
        sys.stdout.write('\n')


if __name__ == "__main__":
    main()
