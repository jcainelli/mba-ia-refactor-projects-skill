VALID_TASK_STATUSES = ("pending", "in_progress", "done", "cancelled")
TERMINAL_TASK_STATUSES = ("done", "cancelled")
VALID_USER_ROLES = ("user", "admin", "manager")

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}

MIN_PASSWORD_LENGTH = 4
BCRYPT_ROUNDS = 12

DEFAULT_CATEGORY_COLOR = "#000000"

RECENT_ACTIVITY_DAYS = 7
