import datetime
import glob
import os

print("=== CHECKING T2 FILES MODIFICATION TIMES ===")
for f in glob.glob("working/redeia_v3/T2/*"):
    print(f"{f:<60} | {datetime.datetime.fromtimestamp(os.path.getmtime(f))}")
