#!/usr/bin/env python3
import click
import json
import requests
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

def get_db_structure(pgcli):
    """Get database structure including tables, columns, and indexes."""
    structure = {}
    try:
        # Get tables and their columns
        table_query = """
        SELECT 
            t.table_name,
            array_agg(DISTINCT c.column_name) as columns
        FROM information_schema.tables t
        JOIN information_schema.columns c ON c.table_name = t.table_name
        WHERE t.table_schema = 'public'
        GROUP BY t.table_name;
        """
        # Get indexes
        index_query = """
        SELECT 
            tablename as table_name,
            indexname as index_name,
            indexdef as index_definition
        FROM pg_indexes
        WHERE schemaname = 'public';
        """
        
        for title, rows, headers, status, sql, success, is_special in pgcli.pgexecute.run(table_query):
            if rows:
                for row in rows:
                    structure[row[0]] = {
                        'columns': row[1],
                        'indexes': []
                    }
                    
        for title, rows, headers, status, sql, success, is_special in pgcli.pgexecute.run(index_query):
            if rows:
                for row in rows:
                    if row[0] in structure:
                        structure[row[0]]['indexes'].append({
                            'name': row[1],
                            'definition': row[2]
                        })
                        
        return structure
    except Exception as e:
        print(f"Error getting database structure: {e}")
        return {}

def get_llm_recommendation(query, db_structure):
    """Get query optimization recommendations from Gemma LLM."""
    try:
        context = f"""You are a PostgreSQL query optimization expert. You have access to the following database structure:

{json.dumps(db_structure, indent=2)}

Keep this structure in mind when analyzing queries. Focus only on practical suggestions specific to this schema."""
        
        prompt = f"""{context}

Analyze this query for performance improvements:
{query}

Provide a concise response with:
1. Specific indexes that would help this query
2. Query rewrites that would improve performance
3. Brief explanation of why each change helps

Be brief and focus only on the most impactful changes."""


        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'gemma3:4b',
                'prompt': prompt,
                'stream': False
            }
        )
        if response.status_code == 200:
            return response.json()['response']
        return "Could not get LLM recommendations. Is Ollama running?"
    except Exception as e:
        return f"Error getting LLM recommendations: {e}"

def analyze_query(query, pgcli):
    """Analyze query execution plan for inefficient patterns."""
    # Skip processing for backslash commands and special commands
    if query.startswith('\\') or query.startswith('show'):
        return True

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
            
            print("\nWould you like AI recommendations to improve this query? [y/N]: ", end='')
            if input().lower() == 'y':
                db_structure = get_db_structure(pgcli)
                recommendations = get_llm_recommendation(query, db_structure)
                print("\n🤖 AI Recommendations:")
                print(recommendations)
                
            print("\nDo you want to proceed with the query? [y/N]: ", end='')
            return input().lower() == 'y'

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
