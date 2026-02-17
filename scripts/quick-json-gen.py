#!/usr/bin/env python3
import os, sys
sys.path.insert(0, "/home/gkarolak/projects/financial-monitor/backend")

os.environ.update({"AWS_REGION": "eu-central-1", "STAGE": "box"})

from features.bond_spreads.services.json_generator import BondSpreadJsonGenerator
from features.bond_spreads.services.spread_calculator import SpreadCalculator
from features.bond_spreads.services.config import COUNTRIES
from shared.dynamo_service import DynamoService
from shared.s3_publisher import S3Publisher

dynamo = DynamoService("fm-box-data")
s3 = S3Publisher("fm-box-frontend-363210543697", "E3R20M4LFTHYMG")
calc = SpreadCalculator()
gen = BondSpreadJsonGenerator(dynamo, calc)

PREFIX = "data/bond-spreads"

print("Generating JSON files...")
s3.publish_json(f"{PREFIX}/spreads-latest.json", gen.generate_latest())
s3.publish_json(f"{PREFIX}/spreads-history.json", gen.generate_history(COUNTRIES))
s3.publish_json(f"{PREFIX}/spreads-summary.json", gen.generate_summary())
s3.invalidate_paths([f"/{PREFIX}/*"])
print("✅ Done!")
