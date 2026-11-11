import random
import uuid
from datetime import datetime, timezone
import time 
customer = ["CUST101", "CUST102", "CUST103", "CUST104" ]
merchants = ["Flipkart", "amazon", "Zepto","Swiggy"]
cities = ["Bangalore", "Hyderabad", "Chennai", "Mumbai"]
devices = ["Phone", "Laptop", "Tablet"]
def generate_transaction():
    return {
        "transaction_id": str(uuid.uuid4())[:8],
        "customer_id": random.choice(customer),
        "amount": round(random.uniform(500, 50000), 2),
        "merchant": random.choice(merchants),
        "city": random.choice(cities),
        "device": random.choice(devices),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    transaction = generate_transaction()
    time.sleep(2)  # Sleep for 1 second before generating the next transaction