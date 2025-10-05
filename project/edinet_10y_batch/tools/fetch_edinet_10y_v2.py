#!/usr/bin/env python3
# fetch_edinet_10y_v2.py (compat stub)
# NOTE: You already downloaded EDINET zips separately.
# This stub just prints guidance so existing calls don't break.
import sys, textwrap
msg = '''
[INFO] fetch_edinet_10y_v2.py (compat stub)
This project now expects pre-downloaded EDINET S*.zip files.
Put them under:
  /mnt/storage/project/edinet_10y_batch/work/zip

Then run:
  bash tools/bulk_ixds_to_facts.sh /mnt/storage/project/edinet_10y_batch/work/zip \\
                                   /mnt/storage/project/edinet_10y_batch/work/oim_out

(If you really need automated fetching again, tell me and I’ll provide a dedicated fetcher.)
'''.strip()
print(msg)
