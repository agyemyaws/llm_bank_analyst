import pandas as pd
import mysql.connector
from mysql.connector import Error
from pathlib import Path
import os
import sys

# Get the absolute path to the project root
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Now we can import from src directly
from src.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

def get_db_connection():
    """Establish MySQL database connection"""
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            port=MYSQL_PORT,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        if connection.is_connected():
            print("Successfully connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise

def format_value(value):
    """Format values properly for MySQL insertion"""
    if pd.isna(value):
        return 'NULL'
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        # Escape single quotes and wrap in single quotes for MySQL
        return f"'{str(value).replace("'", "''")}'"

def insert_customer_data(conn, data):
    cursor = conn.cursor()
    
    # Define columns explicitly to match your table structure
    columns = [
        'CustomerID', 'FirstName', 'LastName', 'Gender', 'Email', 'Phone', 'Age',
        'City', 'Country', 'CurrentBalance', 'Currency', 'TotalTransactions',
        'TotalDeposits', 'TotalWithdrawals', 'AverageTransactionAmount',
        'TotalCashback', 'LastTransactionDate', 'PreferredContactMethod',
        'AverageMonthlySpending', 'HighestTransactionAmount', 'LowestTransactionAmount',
        'TotalNumberOfAccounts', 'AccountStatus', 'RiskProfile', 'DepositStatus',
        'LoanStatus', 'InternationalTransactionIndicator', 'VATUserStatus',
        'TotalVATRefundAmount', 'DeviceModel', 'AppVersion', 'RecentActivityFlag',
        'PreferredLanguage', 'Delivery', 'PlasticCard'
    ]
    
    base_sql = f"""
    INSERT INTO Customers ({', '.join(columns)})
    VALUES """
    
    # Process in batches to avoid memory issues with large datasets
    batch_size = 1000
    total_rows = len(data)
    
    for i in range(0, total_rows, batch_size):
        batch = data.iloc[i:i + batch_size]
        values_list = []
        
        for _, row in batch.iterrows():
            # Ensure we're getting values in the correct order
            values = [format_value(row[col]) for col in columns]
            values_list.append(f"({', '.join(values)})")
        
        sql = base_sql + ',\n'.join(values_list)
        
        try:
            cursor.execute(sql)
            conn.commit()
            print(f"Inserted batch {i//batch_size + 1} ({len(batch)} records) successfully")
        except Error as e:
            conn.rollback()
            print(f"Error inserting batch: {e}")
            print("First row of failed batch:", values_list[0] if values_list else "No values")
            if i == 0:  # Print full SQL for first batch only if it fails
                print("SQL Query:", sql[:1000] + "...")
            raise

def main():
    # Load the CSV file
    csv_file_path = project_root / 'data/customer_profile_data.csv'
    
    try:
        customer_data = pd.read_csv(csv_file_path)
    except FileNotFoundError:
        print(f"Error: Could not find CSV file at {csv_file_path}")
        sys.exit(1)

    conn = None
    try:
        print(f"Current working directory: {os.getcwd()}")
        print(f"Project root path: {project_root}")
        
        conn = get_db_connection()
        print("Connected to MySQL database")
        insert_customer_data(conn, customer_data)
        print("All data inserted successfully")
    except Error as e:
        print(f"Error: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    main()