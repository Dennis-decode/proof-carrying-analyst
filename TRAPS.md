# Traps planted in the data (for the README and the demo)

| Trap | Where | What the system must do |
|---|---|---|
| Exact duplicate rows | orders O003, O009 | Remove them, log it |
| Same order_id, different amount | orders O015 (95 vs 105) | Keep first, log the conflict |
| Mixed currencies | orders (USD/EUR) | Convert with monthly rate |
| Missing exchange rate | EUR order O014 in April | Leave unconverted, log, never guess |
| Missing amount | orders O010 | Exclude from sums, log |
| Ambiguous date | orders O013 (03/04/2025) | Do not guess; exclude from date totals, log |
| Unambiguous slash date | orders O012 (15/03/2025) | Parse correctly as 15 March |
| Customer missing from table | C07 in orders | Log; country unknown |
| Refund bigger than order | refunds O004 | Mark invalid |
| Refund on cancelled order | refunds O006 | Mark invalid |
| Refund for non-existent order | refunds O999 | Mark invalid |
| Unanswerable question | "profit margin" (no cost column) | Refuse |
| Out-of-range question | "revenue in 2026" | Refuse |
| Non-existent entity | customer C99 | Refuse |
| Vague question | "best customer" | Ask for clarification |
