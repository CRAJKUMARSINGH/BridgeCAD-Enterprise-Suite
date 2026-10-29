# Standards Traceability Matrix

Every drawn element class maps to a model field and a clause. A row without a
clause is a defect. Clause numbers verified in week 45.

| Element class | Layer | Model field | Standard | Clause | Sheet(s) | Verified |
|---|---|---|---|---|---|---|
| Deck outline | `SUPER-DECK` | `geometry_input.overall_width_m` | IRC:5-2015 | Cl. 104 | 1, 2, 3 | ☐ |
| Wearing course | `SUPER-WEARING` | `superstructure.wearing_coat_thickness_mm` | MORTH 2024-25 | Ch. 5 | 3 | ☐ |
| Kerb | `SUPER-KERB` | `geometry_input.kerb_width_left_m` | IRC:5-2015 | Cl. 109 | 3 | ☐ |
| Parapet / crash barrier | `SUPER-PARAPET` | `superstructure.parapet_height_mm` | IRC:6-2017 | Cl. 216 | 2, 3 | ☐ |
| Bearing pedestal | `SUB-BEARING` | `substructure.pier_pedestal_height_m` | IRC:83-2018 | Cl. 5.2 | 2, 6 | ☐ |
| Expansion joint | `SUB-EXPJOINT` | `bearings_joints.expansion_joint_schedule` | IRC:SP:69-2011 | Cl. 6 | 2, 6 | ☐ |
| Pile cap | `FOUND-CAP` | `foundation_details.pile_cap_thickness_mm` | IRC:78-2014 | Cl. 8 | 2, 4 | ☐ |
| Well steining | `FOUND-WELL` | `foundation_details` (`type=WELL`) | IRC:78-2014 | Cl. 7 | 2, 4 | ☐ |
| Soil strata | `FOUND-SOIL` | borelog input | IRC:SP:45-2014 | Cl. 4 | 2 | ☐ |
| HFL line | `CIVIL-HFL` | `hydraulic_data.hfl_m` | IRC:SP:13-2004 | Cl. 3 | 2 | ☐ |
| Launching apron | `CIVIL-SCOUR` | `hydraulic_data.design_scour_depth_m` | IRC:89-1997 | Cl. 6 | 2 | ☐ |
| Chainage axis | `CIVIL-CHAINAGE` | `geometry_input.chainage_start_km` | IRC:SP:55-2019 | Cl. 9 | 1, 2 | ☐ |
| Section marker | `SYM-SECTIONMARK` | `drawing_control` | IRC:SP:55-2019 | Cl. 11.4 | 1 | ☐ |
| Level tag | `TEXT-LEVEL` | all `*_rl_m` fields | IRC:SP:55-2019 | Cl. 12.2 | all | ☐ |
| Text heights | all text layers | `text.TextClass` | IRC:SP:55-2019 | Cl. 8.1 | all | ☐ |
| Dimension string | `DIM-LINEAR` | `dimstyles` | IRC:SP:55-2019 | Cl. 10 | all | ☐ |

Extend per element. `scripts/check_traceability.py` fails on any unlisted class.
