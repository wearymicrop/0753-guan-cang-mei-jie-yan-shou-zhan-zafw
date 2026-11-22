from .modules.m1_batches.service import resolve
from .modules.m2_manifest.service import ingest
from .modules.m3_mapping.service import map_targets
from .modules.m4_fixity.service import scan
from .modules.m5_drift.service import compare_copies
from .modules.m6_reconcile.service import reconcile

TABLES = ('catalogs','objects','routes','replicas')
STAGES = (('batches',resolve),('manifest',ingest),('mapping',map_targets),
          ('fixity',scan),('drift',compare_copies),('reconcile',reconcile))
