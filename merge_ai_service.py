"""
Merge script: Combine threading-based AiWorker with all prompts/helpers from backup.
"""

# Read the backup file
with open('app/core/ai_service_backup.py', 'r', encoding='utf-8') as f:
    backup_lines = f.readlines()

# Read the threading version
with open('app/core/ai_service_threading.py', 'r', encoding='utf-8') as f:
    threading_lines = f.readlines()

# Find where the shared rules start in backup (line 81: "# ── 共享规则")
shared_rules_start = None
for i, line in enumerate(backup_lines):
    if '# ── 共享规则' in line:
        shared_rules_start = i
        break

if shared_rules_start is None:
    print("ERROR: Could not find shared rules section")
    exit(1)

# Find where AiWorker class starts in threading version
aiworker_start = None
for i, line in enumerate(threading_lines):
    if line.startswith('class AiWorker(QThread):'):
        aiworker_start = i
        break

if aiworker_start is None:
    print("ERROR: Could not find AiWorker class")
    exit(1)

# Find where the import statement starts in threading version (we want to exclude it)
import_start = None
for i in range(aiworker_start + 1, len(threading_lines)):
    if '# Import all the prompt' in threading_lines[i]:
        import_start = i
        break

if import_start is None:
    print("ERROR: Could not find import statement")
    exit(1)

# Build the new file
new_lines = []

# Header and imports from threading version (lines 0 to just before AiWorker class)
new_lines.extend(threading_lines[0:aiworker_start])

# AiWorker class from threading version (excluding the import statement at the end)
new_lines.extend(threading_lines[aiworker_start:import_start])
new_lines.append('\n')

# All prompts and helpers from backup (from shared rules to end)
new_lines.extend(backup_lines[shared_rules_start:])

# Write the merged file
with open('app/core/ai_service.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Successfully merged ai_service.py ({len(new_lines)} lines)")
