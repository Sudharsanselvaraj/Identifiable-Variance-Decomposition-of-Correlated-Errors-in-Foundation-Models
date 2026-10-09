# Config-based ancestry recovery

Models excluded from primary only for an undeclared parent: 2978

## `_name_or_path` outcomes

| outcome        |   models |
|:---------------|---------:|
| ok             |     1066 |
| local_path     |      838 |
| not_repo_id    |      353 |
| missing_field  |      293 |
| self_reference |      229 |
| not_on_hub     |      111 |
| merge_path     |       63 |
| no_config      |       19 |
| candidate      |        7 |

Recovered into the expanded roster: **574** of 2978

## Why the rest stay excluded (expanded walk)

| exclusion_expanded   |   models |
|:---------------------|---------:|
| undeclared_parent    |     1916 |
| root_is_finetune     |      447 |
| via_merge            |       32 |
| ancestor_missing     |        9 |
