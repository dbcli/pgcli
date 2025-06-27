#!/usr/bin/env python3
import click
import ollama
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

def analyze_query(query, pgcli):
    """Analyze query execution plan for inefficient patterns."""
    try:
        # Get the execution plan
        warnings = []
        cost = 0
        rows = 0
        has_seq_scan = False
        has_nested_loop = False

        for title, rows_data, headers, status, sql, success, is_special in pgcli.pgexecute.run(f"explain {query}"):
            if not rows_data:
                continue
                
            for row in rows_data:
                plan_line = row[0].lower()
                
                # Extract cost and rows if present
                if 'cost=' in plan_line:
                    cost = float(plan_line.split('cost=')[1].split('..')[1].split()[0])
                if 'rows=' in plan_line:
                    rows = int(plan_line.split('rows=')[1].split()[0])
                
                # Check for inefficient patterns
                if 'seq scan' in plan_line and rows > 1000:
                    has_seq_scan = True
                    warnings.append(f"⚠️  Large Sequential Scan on {rows:,} rows")
                
                if 'nested loop' in plan_line and rows > 1000:
                    has_nested_loop = True
                    warnings.append("⚠️  Expensive Nested Loop Join detected")

        # Add warnings for high-cost operations
        if cost > 50000:
            warnings.append(f"⚠️  High cost operation: {cost:,.0f}")

        if warnings:
            print("\nPerformance Warnings:")
            for warning in warnings:
                print(warning)
            if has_seq_scan:
                print("\nTip: Consider adding an index to avoid sequential scans")
            if has_nested_loop:
                print("\nTip: Add appropriate JOIN conditions or indexes")
            
            response = input("\nDo you want to proceed? [y/N]: ")
            return response.lower() == 'y'

        return True

    except Exception as e:
        print(f"\nError analyzing plan: {str(e)}")
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
        return analyze_query(query, pgcli)
    
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
