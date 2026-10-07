# 049 独立固定期待と実結果

コードSHA `99e9d03d4e095b4627b510efd4806f82276617c9`。112ケース/723条件/失敗0。期待は手書きexpectations.json、結果は完成別checkoutの原codec.json。input_sha256は各実物を参照。

| ケースID | 固定期待 | 実結果 | 操作 |
| --- | --- | --- | --- |
| M09-legacy-plain | ok | ok | decode |
| M09-legacy-typed | ok | ok | decode |
| M09-legacy-untyped-metrics | ok | ok | decode |
| M09-new-no-aux | ok | ok | decode |
| M09-new-typed | ok | ok | encode |
| M09-new-gzip-10000 | ok | ok | encode |
| M09-new-untyped | ok | ok | decode |
| M10-region-valid | ok | ok | validate |
| M10-prepare-region | ok | ok | prepare |
| M10-format1-migrated | ok | ok | encode |
| M10-progressed-new | ok | ok | encode |
| M10-caps-raise | ok | ok | prepare |
| M10-caps-lower | ok | ok | prepare |
| M10-unknown-root | unknown_field | unknown_field | validate |
| M10-unknown-actor | unknown_field | unknown_field | validate |
| M10-unknown-reserve | unknown_field | unknown_field | validate |
| M10-unknown-integrated | unknown_field | unknown_field | validate |
| M10-unknown-world | unknown_field | unknown_field | validate |
| M10-unknown-metrics | unknown_field | unknown_field | validate |
| M10-position-relocation | position_relocation_required | position_relocation_required | decode |
| M10-reserve-hp | invalid_reserve | invalid_reserve | validate |
| M10-reserve-mp | invalid_reserve | invalid_reserve | validate |
| M10-reserve-mastery | invalid_reserve | invalid_reserve | validate |
| M10-reserve-jp | invalid_reserve | invalid_reserve | validate |
| M10-reserve-ability | unknown_ability | unknown_ability | validate |
| M10-reserve-duplicate | duplicate_actor | duplicate_actor | validate |
| M11-version | unsupported_version | unsupported_version | validate |
| M11-missing-version | unsupported_version | unsupported_version | validate |
| M11-mixed-world | unknown_field | unknown_field | validate |
| M11-mixed-actor | unknown_field | unknown_field | validate |
| M11-orphan | orphan_instance | orphan_instance | validate |
| M11-duplicate-owner | duplicate_owner | duplicate_owner | validate |
| M11-float-bag | invalid_instance_type | invalid_instance_type | validate |
| M11-null-bag | invalid_instance_type | invalid_instance_type | validate |
| M11-policy | invalid_audit | invalid_audit | validate |
| M11-audit | invalid_audit | invalid_audit | validate |
| M11-grants | invalid_grants | invalid_grants | validate |
| M11-grant-pending | invalid_grants | invalid_grants | validate |
| M11-grant-missing | invalid_shape | invalid_shape | validate |
| M11-support | invalid_grants | invalid_grants | validate |
| M11-catalog-missing | unknown_ability | unknown_ability | encode |
| M11-catalog-invalid | invalid_catalog | invalid_catalog | encode |
| M11-catalog-overwrite | invalid_catalog | invalid_catalog | encode |
| M12-envelope-_storage_format | invalid_envelope | invalid_envelope | decode |
| M12-envelope-decoded_bytes | invalid_envelope | invalid_envelope | decode |
| M12-envelope-sha256 | invalid_envelope | invalid_envelope | decode |
| M12-envelope-payload_sha256 | invalid_envelope | invalid_envelope | decode |
| M12-envelope-payload | invalid_envelope | invalid_envelope | decode |
| M12-envelope-extra | invalid_envelope | invalid_envelope | decode |
| M12-types-missing | invalid_types | invalid_types | decode |
| M12-types-duplicate | invalid_types | invalid_types | decode |
| M12-types-builtin | invalid_types | invalid_types | decode |
| M12-types-extra | invalid_types | invalid_types | decode |
| M12-types-version | invalid_types | invalid_types | decode |
| M12-precision-loss | serialization_mismatch | serialization_mismatch | encode |
| M12-nan | unsupported_value | unsupported_value | encode |
| M12-inf | unsupported_value | unsupported_value | encode |
| M12-typed-dictionary | unsupported_value | unsupported_value | encode |
| M12-builtin-value | unsupported_value | unsupported_value | encode |
| M12-invalid-utf8 | invalid_encoding | invalid_encoding | decode |
| M12-invalid-json | invalid_json | invalid_json | decode |
| M12-json-array | invalid_json | invalid_json | decode |
| M12-unknown-legacy-version | unsupported_version | unsupported_version | decode |
| M12-elapsed | invalid_metrics | invalid_metrics | decode |
| M12-chapter | invalid_metrics | invalid_metrics | decode |
| M12-counter | invalid_metrics | invalid_metrics | decode |
| M12-event | invalid_metrics | invalid_metrics | decode |
| M12-trial-empty | invalid_record_id | invalid_record_id | decode |
| M12-trial-length | invalid_record_id | invalid_record_id | decode |
| M12-trial-type | invalid_record_id | invalid_record_id | decode |
| M10-party-shape | invalid_state | invalid_state | validate |
| M10-inventory-shape | invalid_state | invalid_state | validate |
| M10-negative-coins | invalid_state | invalid_state | validate |
| M10-invalid-world | invalid_state | invalid_state | validate |
| M10-invalid-progress | invalid_state | invalid_state | validate |
| M10-invalid-expedition | invalid_state | invalid_state | validate |
| M10-invalid-knowledge | invalid_state | invalid_state | validate |
| M10-invalid-outcome | invalid_state | invalid_state | validate |
| M10-actor-field-missing | invalid_state | invalid_state | prepare |
| M10-invalid-forgotten | invalid_reserve | invalid_reserve | validate |
| M10-invalid-relearn | invalid_reserve | invalid_reserve | validate |
| M10-invalid-focus | invalid_reserve | invalid_reserve | validate |
| M10-invalid-level | invalid_reserve | invalid_reserve | validate |
| M10-reserve-field-missing | invalid_reserve | invalid_reserve | prepare |
| M10-expedition-shape | invalid_shape | invalid_shape | validate |
| M10-unknown-stock | unknown_field | unknown_field | validate |
| M10-unknown-travel | unknown_field | unknown_field | validate |
| M10-unknown-resident | unknown_field | unknown_field | validate |
| M11-legacy-jp | invalid_audit | invalid_audit | validate |
| M11-legacy-world | invalid_audit | invalid_audit | validate |
| M11-slot-index | invalid_audit | invalid_audit | validate |
| M11-slot-instance | invalid_audit | invalid_audit | validate |
| M11-audit-missing | invalid_audit | invalid_audit | validate |
| M11-returned-index | invalid_audit | invalid_audit | validate |
| M11-learned-reason | invalid_audit | invalid_audit | validate |
| M11-legacy-nested | unknown_field | unknown_field | validate |
| M11-slot-extra | unknown_field | unknown_field | validate |
| M11-audit-extra | unknown_field | unknown_field | validate |
| M11-generated-extra | unknown_field | unknown_field | validate |
| M11-support-reason | invalid_grants | invalid_grants | validate |
| M11-common-duplicate | invalid_grants | invalid_grants | validate |
| M10-two-handed-master | ok | ok | encode |
| M10-two-handed-unearned | invalid_actor | invalid_actor | validate |
| M12-duplicate-json-key | invalid_json | invalid_json | decode |
| M12-gzip-invalid-utf8 | invalid_encoding | invalid_encoding | decode |
| M12-metrics-overflow | numeric_overflow | numeric_overflow | validate |
| M09-new-existing-metadata | ok | ok | encode |
| M12-encode-types-missing | invalid_types | invalid_types | encode |
| M12-encode-types-duplicate | invalid_types | invalid_types | encode |
| M12-encode-types-builtin | invalid_types | invalid_types | encode |
| M12-encode-types-extra | invalid_types | invalid_types | encode |
| M12-encode-types-version | invalid_types | invalid_types | encode |

全ケースは原入力/native型表現、state/metrics/history/catalog不変を検査。拒否ケースは成功値なしとパス付きerrorsも検査。能力catalog実注入4件、全人物stats4件、正確な配列順/浮動小数型/死亡維持等の追加条件を含めて723。

| 全人物stats固定 | HP | MP | attack | defense |
| --- | --- | --- | --- |
| 0 | 140 | 24 | 20 | 17 |
| 1 | 125 | 24 | 23 | 9 |
| 2 | 105 | 40 | 8 | 10 |
| 3 | 90 | 44 | 6 | 7 |
