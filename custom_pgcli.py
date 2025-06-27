#!/usr/bin/env python3
import click
from pgcli.main import PGCli

def prevent_drops(query):
    """Prevent execution of DROP statements."""
    if query.strip().upper().startswith('DROP'):
        print("DROP statements are not allowed!")
        return False
    return True

def prevent_inefficient_queries(query, pgcli):
    """Analyze query execution plan and ask user if they want to proceed."""
    if not query.strip().upper().startswith('SELECT'):
        return True

    try:
        # Get estimated plan
        print("\nEstimated Execution Plan:\n")
        for title, rows, headers, status, sql, success, is_special in pgcli.pgexecute.run(f"explain {query}"):
            if rows:
                for row in rows:
                    print(row[0])

        # Ask user if they want to see actual execution plan
        response = input("\nDo you want to see the actual execution plan? [y/N]: ")
        if response.lower() == 'y':
            print("\nActual Execution Plan:\n")
            for title, rows, headers, status, sql, success, is_special in pgcli.pgexecute.run(f"explain analyze {query}"):
                if rows:
                    for row in rows:
                        print(row[0])

        # Ask if they want to proceed with the actual query
        response = input("\nDo you want to execute this query? [y/N]: ")
        return response.lower() == 'y'

    except Exception as e:
        print(f"\nError getting execution plan: {str(e)}")
        response = input("\nDo you want to execute this query anyway? [y/N]: ")
        return response.lower() == 'y'

    return True

@click.command()
@click.argument('database', default='')
@click.option('-h', '--host', default='', help='Database server host')
@click.option('-p', '--port', default=5432, help='Database server port')
@click.option('-U', '--username', default='', help='Database user name')
def main(database, host, port, username):
    """Run pgcli with custom hooks.
    
    DATABASE: Name of the database to connect to (optional)
    """
    # Create pgcli instance and set the hook
    pgcli = PGCli()
    # Create a closure that can access pgcli instance
    def query_hook(query):
        if not prevent_drops(query):
            return False
        return prevent_inefficient_queries(query, pgcli)
    
    pgcli.set_pre_execute_hook(query_hook)

    # Run pgcli with connection parameters
    pgcli.connect(
        database=database,
        host=host,
        port=port,
        user=username
    )
    pgcli.run_cli()

if __name__ == '__main__':
    main()
