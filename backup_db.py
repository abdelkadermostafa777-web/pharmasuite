"""Copy the PharmaSuite database into a 'backups' folder with today's date and time."""
import os
import shutil
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "data", "pharmasuite.db")
BACKUP_DIR = os.path.join(HERE, "backups")


def main():
    if not os.path.exists(SOURCE):
        print("No database found yet. Register an account in the web app first.")
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    target = os.path.join(BACKUP_DIR, f"pharmasuite_{stamp}.db")
    shutil.copy2(SOURCE, target)
    print(f"Backup saved: {target}")


if __name__ == "__main__":
    main()
