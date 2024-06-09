# Command Line Interface (CLI) Commands

## DB Extraction

1. DB users extraction:

Extract all users from specified `date_from` using lang optional argument. Default is to use EN.

**Options:**
- `date_from` /Required/ The date from to extract users
- `--lang` (default=EN) /Optional/ Possible values: EN, FR. Default is EN.

**Examples**:
```
# extract all users from '2020-08-18' for lang 'EN'
python manage.py extract_users 2020-08-18 --lang EN

# extract all users from '2020-08-18' for lang 'EN'
python manage.py extract_users 2020-08-18 --lang FR
```

2. DB venues extraction:

Extract all venues with/without `subscription` and for specified `status`. Default is to use `status=20` (PUBLISHED)

**Options:**
- `-status` /Optional/ The venue status. Possible values: 10, 15, 18, 20, 35. Default is 20.
- `--subscription` /Optional/ Whether to extract venues with/without subscription. Default is false. 

```
# extract all 'DRAFT' venues with no subscription
python manage.py extract_venues -status 10

# extract all 'DRAFT' venues with subscription
python manage.py extract_venues -status 10 --subscription

# extract all 'PUBLISHED' venues with no subscription
python manage.py extract_venues

# extract all 'PUBLISHED' venues with subscription
extract_venues --subscription

```
