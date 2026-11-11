from datetime import datetime
import math

REQUIRED_FIELDS = ["transaction_id",
                    "customer_id", 
                    "amount", 
                    "merchant", 
                    "city", 
                    "device", 
                    "timestamp"]
def validate_transaction(transaction):
    errors = []
    if not isinstance(transaction, dict):
        return False, ["Transaction must be a dictionary"]

    # check required feilds
    for field in REQUIRED_FIELDS:
        value = transaction.get(field)
        if value is None or value == "":
            errors.append(f"{field} is required")
        elif isinstance(value, str) and not value.strip():
            errors.append(f"{field} cannot be empty or whitespace")

        #validate id and desciption fields
        for field in [
            "transaction_id","customer_id",  
            "merchant", "city", "device"]:
            value = transaction.get(field)
            if value is not None and not isinstance(value, str):
                errors.append(f"{field} must be a string")
        #valuate amount field
        amount = transaction.get("amount")
        if (isinstance(amount, bool) or not isinstance(amount, (int, float))
            or not math.isinfinite(amount) and amount < 0):
            errors.append("amount must be in finite number")
        #validate timestamp field
        timestamp = transaction.get("timestamp")
        if not isinstance(timestamp, str):
            errors.append("timestamp must be a ISO datetime text")
        else:
            try:
                parsed = datetime.fromisoformat(timestamp)
                if parsed.tzinfo is None:
                    errors.append("timestamp must be ISO timestamp ")
            except ValueError:
                errors.append("timestamp have invalid format")
        return len(errors) == 0, errors