# AURA Data Dictionary

## Primary Dataset

Sparkov simulated credit-card transaction dataset.

The dataset is used as the primary development and demonstration
dataset for AURA.

## Dataset Summary

- Transactions: 1,296,675
- Customers: 983
- Merchants: 693
- Categories: 14
- Cities: 894
- States: 51
- Time span: 537 days
- Fraud transactions: 7,506
- Fraud rate: approximately 0.58%
- Duplicate rows: 0
- Duplicate transaction IDs: 0

---

## Observed Fields

These fields are directly available in the source dataset.

| AURA Field | Source Field | Description |
|---|---|---|
| transaction_id | trans_num | Unique transaction identifier |
| customer_id | cc_num | Customer/card identifier |
| timestamp | trans_date_trans_time | Transaction date and time |
| merchant_id | merchant | Merchant identifier/name |
| merchant_category | category | Merchant transaction category |
| amount | amt | Transaction amount |
| customer_first_name | first | Customer first name |
| customer_last_name | last | Customer last name |
| gender | gender | Customer gender |
| customer_street | street | Customer street |
| customer_city | city | Customer city |
| customer_state | state | Customer state |
| customer_zip | zip | Customer ZIP code |
| customer_lat | lat | Customer latitude |
| customer_long | long | Customer longitude |
| city_population | city_pop | Customer city population |
| job | job | Customer occupation |
| date_of_birth | dob | Customer date of birth |
| transaction_unix_time | unix_time | Unix transaction timestamp |
| merchant_lat | merch_lat | Merchant latitude |
| merchant_long | merch_long | Merchant longitude |
| fraud_label | is_fraud | Fraud target label |

---

## Derived Fields

These will be created during feature engineering.

Examples include:

- transaction_hour
- day_of_week
- customer_avg_amount
- customer_median_amount
- customer_std_amount
- amount_deviation
- transactions_last_1h
- transactions_last_24h
- time_since_previous_transaction
- customer_merchant_distance
- merchant_frequency
- category_frequency
- new_merchant_indicator
- behavioural_anomaly_score

---

## Synthetic Fields

These are not present in the primary Sparkov dataset and will be
generated explicitly by AURA for graph and investigation experiments.

Examples:

- device_id
- ip_address
- login_event
- device_customer_relationship
- ip_customer_relationship
- related_account_relationship
- synthetic fraud-ring scenarios
- account-takeover scenarios
- transaction-splitting scenarios

Synthetic fields will always be documented as synthetic and will not
be represented as original source data.

---

## Data Handling Principles

1. Raw source files are kept unchanged.
2. Derived features are created separately.
3. Synthetic entities are clearly identified.
4. Sensitive real-world financial data is not used.
5. The project uses public and/or synthetic data only.