import requests
import sys
import datetime
import prettytable

HELP_STRING = 'expected: <endpoint> <jira-username> <jira-password> <project-label> <days> <summarise|dump>'

class JiraController:
    def __init__(self, jira_endpoint, jira_username, jira_password):
        self.endpoint = jira_endpoint
        self.username = jira_username
        self.password = jira_password

    def get_bugs(self, project_label, days):
        jql = 'jql=project=Bugs+and+"Project+Label"=%s+and+updated>-%sd' % (project_label, days)
        other_params = 'expand=changelog'
        response = requests.get('%s/rest/api/2/search/?%s&%s' % (self.endpoint, other_params, jql),
                                 headers={
                                     'Content-Type': 'application/json'
                                 },
                                 auth=(self.username, self.password))

        if response.status_code != 200:
            raise RuntimeError('Bug query failed, %s, "%s"' % (response.status_code, response.reason))
        return response.json()


def get_cleansed_bugs(days, raw_bugs):
    cleansed_bugs = {}
    current_date = datetime.datetime.now()
    for bug in raw_bugs['issues']:
        bug_key = bug['key']

        for history in bug['changelog']['histories']:

            history_date_str = history['created'].split('T')[0]
            history_date = datetime.datetime.strptime(history_date_str, '%Y-%m-%d')

            if (current_date - history_date).days <= days:
                for history_item in history['items']:
                    if 'fieldId' in history_item and history_item['fieldId'] == 'status':

                        if bug_key not in cleansed_bugs:
                            cleansed_bugs[bug_key] = []

                        cleansed_bugs[bug_key].append({
                            'from': history_item['fromString'],
                            'to': history_item['toString'],
                        })

        # Order transitions chronologically.
        if bug_key in cleansed_bugs:
            cleansed_bugs[bug_key] = list(reversed(cleansed_bugs[bug_key]))
    return cleansed_bugs


def summarise_bugs(bugs):
    summary = {}
    for key, transitions in bugs.items():
        for transition in transitions:
            transition_key = '%s -> %s' % (transition['from'], transition['to'])
            if transition_key not in summary:
                summary[transition_key] = {
                    'count': 0,
                    'to': transition['to'],
                    'from': transition['from']
                }
            summary[transition_key]['count'] += 1

    # Convert dict to list once complete as we no longer need the keys.
    return list(summary.values())


def print_bugs(bugs):
    table = prettytable.PrettyTable()
    table.field_names = ['Bug', 'From', 'To']
    for key, transitions in bugs.items():
        first_trans = transitions[0]
        table.add_row([key, first_trans['from'], first_trans['to']])
        for trans in transitions[1:]:
            table.add_row(['', trans['from'], trans['to']])
        table.add_row(['', '', ''])
    print(table)


def print_summary(bug_summary):
    table = prettytable.PrettyTable()
    table.field_names = ['From', 'To', 'Count']
    for summary in bug_summary:
        table.add_row([summary['from'], summary['to'], summary['count']])
    print(table.get_string(sortby='Count', reversesort=True))


def main():
    if len(sys.argv) != 7:
        print(HELP_STRING)
        return

    jira_endpoint = sys.argv[1]
    jira_username = sys.argv[2]
    jira_password = sys.argv[3]
    project_label = sys.argv[4]
    days = int(sys.argv[5])

    if sys.argv[6] not in ['summarise', 'dump']:
        print(HELP_STRING)
        return
    summarise = (sys.argv[6] == 'summarise')

    controller = JiraController(jira_endpoint, jira_username, jira_password)
    raw_bugs = controller.get_bugs(project_label, days)

    bugs = get_cleansed_bugs(days, raw_bugs)

    if summarise:
        bug_summary = summarise_bugs(bugs)
        print_summary(bug_summary)
    else:
        print_bugs(bugs)


if __name__ == "__main__":
    main()