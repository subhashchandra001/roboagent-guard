# Threat Model

Covered adversarial cases include duplicate request IDs, reused nonce, stale timestamp, stale sensor evidence, forged or reused approval tokens, unauthorized camera access, unauthorized map saving, private-zone storage, hidden low SLAM confidence, client-supplied low risk scores, impossible numeric values, unsupported action types, and audit tampering.

The service does not accept actual image payloads. Camera use is represented by metadata flags.
