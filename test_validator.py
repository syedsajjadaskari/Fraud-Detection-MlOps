from transaction_generator import generate_transaction
from ingestion import process_transaction
from database import create_database

create_database()

#case 1: valid transaction
transaction = generate_transaction()
print("Generated transaction:", transaction)
process_transaction(transaction)

#case 2: invalid transaction (negative amount)
negative = generate_transaction()
negative["amount"] = -100.0
print("Generated transaction with negative amount:", negative)
process_transaction(negative)

#case 3 : missing required field (customer_id)
missing_field = generate_transaction()
missing_field["customer_id"] = "None"
process_transaction(missing_field)

#case 4: duplicate transaction_id
duplicate = generate_transaction()
duplicate["transaction_id"] = transaction["transaction_id"]
print("Generated transaction with duplicate transaction_id:", duplicate)
process_transaction(duplicate)