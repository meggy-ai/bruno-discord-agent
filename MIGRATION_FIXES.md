# Database Migration Fixes - December 28, 2025

## Issues Identified and Fixed

### 1. Model Relationship Ordering Issues ✅
**Problem:** In SQLAlchemy models, relationships were defined before their corresponding foreign key columns, which can cause issues with model introspection and migrations.

**Files Fixed:**
- [app/db/models/note.py](app/db/models/note.py)
  - Moved `user` relationship after `user_id` foreign key
  - Moved `entries` relationship after note columns
  - Added `cascade="all, delete-orphan"` to Note->NoteEntry relationship
  - Added `ondelete="CASCADE"` to NoteEntry foreign key
  
- [app/db/models/timer.py](app/db/models/timer.py)
  - Moved `user` relationship to the end of the class
  - Consolidated imports into a single line
  
**Best Practice:** Always define columns (including foreign keys) before relationships in SQLAlchemy models.

### 2. Alembic Configuration Issues ✅
**Problem:** The [alembic.ini](alembic.ini) file had a placeholder database URL instead of a comment.

**Fix:** Commented out the placeholder URL since the actual database URL is loaded from `.env` file in [migrations/env.py](migrations/env.py).

### 3. Empty/Broken Migrations ✅
**Problem:** All existing migrations had empty `upgrade()` and `downgrade()` functions:
- `07db68f9803f_create_user_table.py` - Didn't actually create the users table
- `af109d812c49_added_note.py` - Empty migration
- `1f6c1342779b_update_note_and_timer.py` - Empty migration
- `33e1135a0789_sync_model_relationships.py` - Only had notes/timers, missing users table

**Fix:** Deleted all old migrations and created a single comprehensive initial migration:
- [migrations/versions/666ce7e3c0ea_initial_schema.py](migrations/versions/666ce7e3c0ea_initial_schema.py)

### 4. Database Schema Successfully Created ✅
Applied the new migration successfully. Current database structure:

```
Tables:
- users (id, name, email)
- notes (id, user_id, name, created_at, updated_at)
- timers (id, user_id, conversation_id, name, duration_seconds, end_time, status, paused_at, remaining_seconds, three_minute_warning_sent, completion_notification_sent, created_at, updated_at)
- note_entries (id, note_id, content, position, created_at, updated_at)
- alembic_version (tracking table)
```

## Commands Used

### To apply migrations:
```bash
# Activate virtual environment
source venv/bin/activate

# Apply migrations
alembic upgrade head

# Check current migration version
alembic current

# Generate new migration (after model changes)
alembic revision --autogenerate -m "description_of_changes"
```

### To verify database:
```bash
# List all tables
PGPASSWORD='Test@123' psql -U postgres -h localhost -d bruno_discord_pa -c "\dt"

# Check table structure
PGPASSWORD='Test@123' psql -U postgres -h localhost -d bruno_discord_pa -c "\d table_name"
```

## Recommendations

1. **Always use virtual environment:** A `venv` directory has been created. Always activate it before running migrations.

2. **Model changes workflow:**
   - Make changes to models in `app/db/models/`
   - Generate migration: `alembic revision --autogenerate -m "description"`
   - Review the generated migration file
   - Apply migration: `alembic upgrade head`

3. **Cascade deletes:** The Note->NoteEntry relationship now has proper cascade deletes, so deleting a note will automatically delete all its entries.

4. **Foreign key ordering:** All foreign key columns are now defined before their relationships.

5. **Future migrations:** Now that you have a clean baseline, all future migrations will be incremental and should work correctly with autogenerate.
