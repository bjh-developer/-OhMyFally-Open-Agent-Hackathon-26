-- Drops OUR USL only (errors ignored when it does not exist yet), so the model is rebuilt cleanly on every run.
REMOVE USL procurement_usl NAMESPACE lightning.metastore.procurement
