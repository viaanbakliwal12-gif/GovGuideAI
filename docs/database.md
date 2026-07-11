# Database

GovGuideAI uses local SQLite for the first version. The database file is created at:

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
- `location_type`
- `preferred_language`
- `gender`
- `student_status`
- `farmer_status`
- `annual_household_income_range`
- `disability_status`
- `employment_status`
- `marital_status`
- `social_category`
- `updated_date`

`profiles.user_id` is unique, so each user has one profile. The foreign key points to `users.id`.
