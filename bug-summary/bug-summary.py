import requests
import sys
import datetime
import prettytable
import json

SEVERITY_KEY = 'customfield_12010'
PRIORITY_KEY = 'customfield_12009'

HELP_STRING = 'expected: <endpoint> <jira-username> <jira-password> ' \
              '<project-label> <start-date> <end-date> <summarise|dump>'

class JiraController:
    def __init__(self, jira_endpoint, jira_username, jira_password):
        self.endpoint = jira_endpoint
        self.username = jira_username
        self.password = jira_password

    def get_bugs(self, project_label, start_days, end_days):
        jql = 'jql=project=Bugs+and+"Project+Label"=%s+and+updated>-%sd+and+updated<-%sd' % \
              (project_label, start_days, end_days)
        other_params = 'expand=changelog'
        response = requests.get('%s/rest/api/2/search/?%s&%s' % (self.endpoint, other_params, jql),
                                 headers={
                                     'Content-Type': 'application/json'
                                 },
                                 auth=(self.username, self.password))

        if response.status_code != 200:
            raise RuntimeError('Bug query failed, %s, "%s"' % (response.status_code, response.reason))
        return response.json()


def get_cleansed_bugs(start_days, end_days, raw_bugs):
    cleansed_bugs = {}
    current_date = datetime.datetime.now()
    for bug in raw_bugs['issues']:
        bug_key = bug['key']
        get_bug_level(bug)

        for history in bug['changelog']['histories']:

            history_date_str = history['created'].split('T')[0]
            history_date = datetime.datetime.strptime(history_date_str, '%Y-%m-%d')

            issue_days = (current_date - history_date).days
            if start_days >= issue_days >= end_days:
                for history_item in history['items']:
                    if 'fieldId' in history_item and history_item['fieldId'] == 'status':

                        if bug_key not in cleansed_bugs:
                            cleansed_bugs[bug_key] = {
                                'level': get_bug_level(bug),
                                'transitions': []
                            }
                            # cleansed_bugs[bug_key] = []

                        cleansed_bugs[bug_key]['transitions'].append({
                            'from': history_item['fromString'],
                            'to': history_item['toString'],
                        })

        # Order transitions chronologically.
        if bug_key in cleansed_bugs:
            cleansed_bugs[bug_key]['transitions'] = list(reversed(cleansed_bugs[bug_key]['transitions']))
    return cleansed_bugs


def get_bug_level(bug):
    if bug['fields'][SEVERITY_KEY] is None or bug['fields'][PRIORITY_KEY] is None:
        return 'NA'

    severity = int(bug['fields'][SEVERITY_KEY]['value'][1])
    priority = int(bug['fields'][PRIORITY_KEY]['value'][1])
    normalised_pri = (priority - 1) // 2
    normalised_sev = (severity - 1) // 2
    level = (normalised_pri * 2 + normalised_sev) + 1

    return level


def summarise_bugs(bugs):
    summary = {}
    for key, bug in bugs.items():
        for transition in bug['transitions']:
            level = bug['level']
            if level != 'NA':
                transition_key = '%s -> %s' % (transition['from'], transition['to'])
                if level not in summary:
                    summary[level] = {}
                if transition_key not in summary[level]:
                    summary[level][transition_key] = {
                        'count': 0,
                        'to': transition['to'],
                        'from': transition['from']
                    }
                summary[level][transition_key]['count'] += 1

    cleansed_summary = {}
    for level, transitions in summary.items():
        cleansed_summary[level] = list(transitions.values())

    return cleansed_summary


def print_bugs(bugs):
    table = prettytable.PrettyTable()
    table.field_names = ['Bug', 'Level', 'From', 'To']
    for key, bug in bugs.items():
        first_trans = bug['transitions'][0]
        table.add_row([key, bug['level'], first_trans['from'], first_trans['to']])
        for trans in bug['transitions'][1:]:
            table.add_row(['', '', trans['from'], trans['to']])
        table.add_row(['', '', '', ''])
    print(table)


def print_summary(bug_summary):
    table = prettytable.PrettyTable()
    table.field_names = ['Level', 'From', 'To', 'Count']

    first_level = True
    for level, transitions in sorted(bug_summary.items()):
        if not first_level:
            table.add_row(['', '', '', ''])
        first_level = False

        table.add_row([str(level), transitions[0]['from'], transitions[0]['to'], transitions[0]['count']])
        for transition in transitions[1:]:
            table.add_row(['', transition['from'], transition['to'], transition['count']])

    print(table.get_string())


def get_date_from_str(date_str):
    return datetime.datetime.strptime(date_str, '%d-%m-%Y').date()


def get_days_since_date(date):
    todays_date = datetime.date.today()
    if date > todays_date:
        raise RuntimeError('Given date was invalid')
    return (todays_date - date).days


def main():
    if len(sys.argv) != 8:
        print(HELP_STRING)
        return

    jira_endpoint = sys.argv[1]
    jira_username = sys.argv[2]
    jira_password = sys.argv[3]
    project_label = sys.argv[4]
    start_days = get_days_since_date(get_date_from_str(sys.argv[5]))
    end_days = get_days_since_date(get_date_from_str(sys.argv[6]))

    if sys.argv[7] not in ['summarise', 'dump']:
        print(HELP_STRING)
        return
    summarise = (sys.argv[7] == 'summarise')

    controller = JiraController(jira_endpoint, jira_username, jira_password)
    raw_bugs = controller.get_bugs(project_label, start_days, end_days)

    bugs = get_cleansed_bugs(start_days, end_days, raw_bugs)

    if summarise:
        bug_summary = summarise_bugs(bugs)
        print_summary(bug_summary)
    else:
        print_bugs(bugs)


if __name__ == "__main__":
    main()