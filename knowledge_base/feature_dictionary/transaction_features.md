# Transaction Feature Dictionary

transactions_prev_5min: number of transactions observed in the previous five minutes.

transactions_prev_1h: number of transactions observed in the previous hour.

transactions_prev_24h: number of transactions observed in the previous twenty-four hours.

customer_prev_count: number of previous transactions associated with the customer.

customer_prev_avg_amount: customer's historical average transaction amount.

customer_prev_median_amount: customer's historical median transaction amount.

customer_prev_std_amount: customer's historical transaction amount standard deviation.

amount_deviation_ratio: relative deviation of the current amount from historical customer behaviour.

seconds_since_prev_transaction: elapsed time since the customer's previous transaction.

is_new_merchant: indicates whether the merchant was previously unseen for the customer.

is_new_category: indicates whether the transaction category was previously unseen for the customer.

customer_merchant_distance_km: distance between the customer and merchant where available.

graph_risk_score: risk signal derived from relevant graph relationships.
