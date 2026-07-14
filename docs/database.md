# Database

GovGuideAI uses local SQLite for this version. The database file is created at:

```text
govguideai.sqlite3
```

## Tables

`users`

- `id`
- `email`
- `password_hash`
- `created_date`
- `last_login_date`

`profiles`

- `id`
- `user_id`
- `full_name`
- `age`
- `state`
- `district`
- `occupation`
- `occupation_custom`
- `location_type`
- `preferred_language`
- `gender`
- `annual_household_income_range`
- `disability_status`
- `marital_status`
- `social_category`
- `updated_date`

`profiles.user_id` is unique, so each user has one profile. The foreign key points to `users.id`.

## Legacy Columns

Older databases may still contain these unused columns:

- `student_status`
- `farmer_status`
- `employment_status`

They are preserved so existing databases and accounts are not deleted. The app no longer uses them in forms, validation, agent context, backend requests, or Scheme Search parameters.

Later, after backing up the database, these columns can be removed with a manual SQLite table rebuild migration.

## Compatibility Updates

On startup, `init_db()` ensures `occupation_custom` exists. It also maps old values to the new `occupation` field only when doing so is safe:

- old student status true -> `student`, only if occupation is missing
- old farmer status true -> `farmer`, only if occupation is missing
- old employment status unemployed -> `unemployed`, only if occupation is missing

Existing occupation values are not overwritten except for simple normalization such as `Student` -> `student`.
