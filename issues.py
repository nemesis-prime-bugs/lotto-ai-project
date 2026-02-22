"""
Issue & Task Management for Lotto Analytics
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'lotto.db')


def get_connection():
    return sqlite3.connect(DB_PATH)


def list_issues(phase=None, status=None):
    """List all issues, optionally filtered."""
    conn = get_connection()
    c = conn.cursor()

    query = 'SELECT issue_id, title, description, phase, priority, status FROM issues WHERE 1=1'
    params = []

    if phase:
        query += ' AND phase = ?'
        params.append(phase)
    if status:
        query += ' AND status = ?'
        params.append(status)

    query += ' ORDER BY phase, priority'

    c.execute(query, params)
    issues = c.fetchall()
    conn.close()

    return issues


def get_issue(issue_id):
    """Get single issue with its tasks."""
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT * FROM issues WHERE issue_id = ?', (issue_id,))
    issue = c.fetchone()

    c.execute('SELECT * FROM tasks WHERE issue_id = ?', (issue_id,))
    tasks = c.fetchall()

    conn.close()

    return issue, tasks


def update_issue_status(issue_id, status):
    """Update issue status."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE issues SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE issue_id = ?",
              (status, issue_id))
    conn.commit()
    conn.close()


def update_task_status(task_id, status):
    """Update task status."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET status = ? WHERE task_id = ?", (status, task_id))
    conn.commit()
    conn.close()


def show_issues():
    """Display all issues in nice format."""
    issues = list_issues()

    current_phase = None
    for issue in issues:
        issue_id, title, desc, phase, priority, status = issue

        if phase != current_phase:
            print(f'\n📦 PHASE {phase}')
            print('-' * 50)
            current_phase = phase

        print(f'  [{status}] {issue_id}: {title}')


def show_issue_detail(issue_id):
    """Show issue with its tasks."""
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT * FROM issues WHERE issue_id = ?', (issue_id,))
    issue = c.fetchone()

    c.execute('SELECT * FROM tasks WHERE issue_id = ?', (issue_id,))
    tasks = c.fetchall()

    conn.close()

    if not issue:
        print(f'Issue {issue_id} not found')
        return

    # issue is: (id, issue_id, title, description, phase, priority, status, created_at, updated_at)
    issue_id, db_id, title, desc, phase, priority, status, created, updated = issue

    print(f'\n{"="*50}')
    print(f'{issue_id}: {title}')
    print(f'{"="*50}')
    print(f'Status: {status}')
    print(f'Phase: {phase}, Priority: {priority}')
    print(f'\nDescription: {desc}')
    print(f'\nTasks:')

    for task in tasks:
        # task is: (id, task_id, issue_id, title, description, status, created_at)
        task_id, db_id, iss_id, task_title, task_desc, task_status, created = task
        print(f'  [{task_status}] {task_id}: {task_title}')


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'list':
            show_issues()
        elif sys.argv[1] == 'show' and len(sys.argv) > 2:
            show_issue_detail(sys.argv[2].upper())
        else:
            print('Usage: python issues.py [list|show ISSUE_ID]')
    else:
        show_issues()