"""
Utility to generate the remaining 23 E2E fixture JSON files.
Each fixture maps 1:1 to a Scribd reference GAD drawing.
Run: python tests/e2e/fixtures/_fixture_template.py
"""
from __future__ import annotations
import json
from pathlib import Path

OUT = Path(__file__).parent

# ── Fixture definitions ─────────────────────────────────────────────────────
# Keys must match BridgeProject field names / enum names exactly.
# 'expected' values are verified by run_e2e.py.

FIXTURES: list[dict] = [

    # ── 06: Shiwalay Major Bridge — 3×30m PSC box continuous ────────────────
    {
        "_meta": {
            "fixture_id":      "shiwalay_3x30m_psc_box",
            "description":     "Major PSC Box Girder bridge 3×30m continuous, Shiwalay",
            "scribd_refs":     ["all-drawing-of-shiwalay-major-bridge-1-pdf"],
            "design_standard": "IRC:112-2020 PSC continuous box",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":90.0,"span_count":3,
            "overall_width_m_min":9.0,"overall_width_m_max":14.0,
            "qa_score_min":80,"dxf_sheets":7,"dxf_total_kb_min":300,
            "boq_grand_total_inr_min":60000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"PSC_BOX_GIRDER","span_count":3,
                                  "span_configuration":"CONTINUOUS"},
            "geometry_input":   {"span_count":3,"span_lengths_m":[30.0,30.0,30.0],
                                  "carriageway_width_m":10.50,"footpath_left_m":1.5,
                                  "footpath_right_m":1.5},
            "superstructure":   {"type":"PSC_BOX_GIRDER","deck_material":"M50",
                                  "girder_depth_mm":2000,"girder_spacing_m":0.0,
                                  "girders_per_deck_count":1,"camber_mm":60},
            "calculations":     {"total_length_m":90.0,"span_count":3,
                                  "total_estimated_quantity_cost_inr":95000000},
        },
    },

    # ── 07: Chambakkara Bridge — 5×25m PSC I-Girder ──────────────────────────
    {
        "_meta": {
            "fixture_id":      "chambakkara_5x25m",
            "description":     "Chambakkara Bridge 5×25m PSC I-Girder Kerala",
            "scribd_refs":     ["01-Chambakkara-Bridge-GAD-R08-23-11-2017-Model"],
            "design_standard": "IRC:112-2020 PSC simply-supported",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":125.0,"span_count":5,
            "overall_width_m_min":9.0,"overall_width_m_max":13.0,
            "qa_score_min":80,"dxf_sheets":7,"dxf_total_kb_min":350,
            "boq_grand_total_inr_min":110000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"PSC_IGIRDER","span_count":5},
            "geometry_input":   {"span_count":5,"span_lengths_m":[25.0,25.0,25.0,25.0,25.0],
                                  "carriageway_width_m":7.50,"footpath_left_m":1.5,"footpath_right_m":1.5},
            "superstructure":   {"type":"PSC_IGIRDER","deck_material":"M45",
                                  "girder_depth_mm":1950,"camber_mm":45},
            "calculations":     {"total_length_m":125.0,"span_count":5,
                                  "total_estimated_quantity_cost_inr":145000000},
        },
    },

    # ── 08: Newaj River 165m — 3×45m PSC I-Girder ────────────────────────────
    {
        "_meta": {
            "fixture_id":      "newaj_3x45m",
            "description":     "Newaj River 3×45m PSC I-Girder major bridge",
            "scribd_refs":     ["Newaj-River-165-Final-Model-1"],
            "design_standard": "IRC:112-2020",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":135.0,"span_count":3,
            "overall_width_m_min":8.5,"overall_width_m_max":14.0,
            "qa_score_min":75,"dxf_sheets":7,"dxf_total_kb_min":300,
            "boq_grand_total_inr_min":120000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"PSC_IGIRDER","span_count":3,
                                  "loading_class":"CLASS_A"},
            "geometry_input":   {"span_count":3,"span_lengths_m":[45.0,45.0,45.0],
                                  "carriageway_width_m":7.50,"footpath_left_m":1.5,
                                  "footpath_right_m":1.5},
            "superstructure":   {"type":"PSC_IGIRDER","deck_material":"M45",
                                  "girder_depth_mm":2400,"camber_mm":55},
            "calculations":     {"total_length_m":135.0,"span_count":3,
                                  "total_estimated_quantity_cost_inr":165000000},
        },
    },

    # ── 09: ROB at CH 37+730 — 4×18m viaduct ────────────────────────────────
    {
        "_meta": {
            "fixture_id":      "rob_viaduct_ch37_730",
            "description":     "Major ROB + Viaduct at CH 37+730 4×18m PSC",
            "scribd_refs":     ["Ga-114-mjb-viaduct-r0-general-Arrangement-Drawing-of-Major-Cum-Viaduct-Bridge-at-Ch-37-730"],
            "design_standard": "IRC:112-2020 ROB + viaduct",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":72.0,"span_count":4,
            "overall_width_m_min":9.5,"overall_width_m_max":14.0,
            "qa_score_min":80,"dxf_sheets":7,"dxf_total_kb_min":300,
            "boq_grand_total_inr_min":75000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_category":"VIADUCT","bridge_type":"PSC_IGIRDER",
                                  "span_count":4},
            "geometry_input":   {"span_count":4,"span_lengths_m":[18.0,18.0,18.0,18.0],
                                  "carriageway_width_m":7.50,"footpath_left_m":1.5,
                                  "footpath_right_m":1.5},
            "calculations":     {"total_length_m":72.0,"span_count":4,
                                  "total_estimated_quantity_cost_inr":88000000},
        },
    },

    # ── 10: Binder Bridge 20×3 skew 5° ────────────────────────────────────
    {
        "_meta": {
            "fixture_id":      "binder_bridge_3x20m_skew5",
            "description":     "Binder Bridge 3×20m RCC T-Beam 5° skew",
            "scribd_refs":     ["Binder-Bridge-20-x-3-skew-5"],
            "design_standard": "IRC:21-2000 skew bridge",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":60.0,"span_count":3,
            "overall_width_m_min":8.5,"overall_width_m_max":10.5,
            "qa_score_min":75,"dxf_sheets":7,"dxf_total_kb_min":280,
            "boq_grand_total_inr_min":32000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"RCC_TBEAM","span_count":3},
            "geometry_input":   {"span_count":3,"span_lengths_m":[20.0,20.0,20.0],
                                  "skew_angle_deg":5.0,"skew_direction":"RIGHT",
                                  "carriageway_width_m":7.50},
            "superstructure":   {"type":"RCC_TBEAM","girder_depth_mm":1400},
            "calculations":     {"total_length_m":60.0,"span_count":3,
                                  "total_estimated_quantity_cost_inr":42000000},
        },
    },

    # ── 11: 2R-03 GAD Final — 2×15m RCC T-Beam ──────────────────────────────
    {
        "_meta": {
            "fixture_id":      "gad_2x15m_rcc_tbeam",
            "description":     "2R-03 GAD 2×15m RCC T-Beam standard bridge",
            "scribd_refs":     ["2-r-03-Gad-of-Bridge-Final-Gad-1"],
            "design_standard": "IRC:21-2000",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":30.0,"span_count":2,
            "overall_width_m_min":8.5,"overall_width_m_max":10.5,
            "qa_score_min":80,"dxf_sheets":7,"dxf_total_kb_min":260,
            "boq_grand_total_inr_min":18000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"RCC_TBEAM","span_count":2},
            "geometry_input":   {"span_count":2,"span_lengths_m":[15.0,15.0],
                                  "carriageway_width_m":7.50},
            "superstructure":   {"type":"RCC_TBEAM","girder_depth_mm":1100},
            "calculations":     {"total_length_m":30.0,"span_count":2,
                                  "total_estimated_quantity_cost_inr":24000000},
        },
    },

    # ── 12: 361+935 GAD — 3×18m RCC T-Beam ────────────────────────────────
    {
        "_meta": {
            "fixture_id":      "gad_361_935_3x18m",
            "description":     "361+935 GAD 3×18m RCC T-Beam state highway",
            "scribd_refs":     ["361-935-GAD"],
            "design_standard": "IRC:21-2000 / IRC:78",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":54.0,"span_count":3,
            "overall_width_m_min":8.5,"overall_width_m_max":10.5,
            "qa_score_min":80,"dxf_sheets":7,"dxf_total_kb_min":280,
            "boq_grand_total_inr_min":35000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"RCC_TBEAM","span_count":3},
            "geometry_input":   {"span_count":3,"span_lengths_m":[18.0,18.0,18.0],
                                  "carriageway_width_m":7.50},
            "superstructure":   {"type":"RCC_TBEAM","girder_depth_mm":1300},
            "calculations":     {"total_length_m":54.0,"span_count":3,
                                  "total_estimated_quantity_cost_inr":47000000},
        },
    },

    # ── 13: MNB-8+485 minor bridge ───────────────────────────────────────────
    {
        "_meta": {
            "fixture_id":      "mnb_8_485_minor_18m",
            "description":     "MNB 8+485 minor bridge 1×18m RCC T-Beam PMGSY",
            "scribd_refs":     ["MNB-8-485-101"],
            "design_standard": "IRC SP:13 PMGSY",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":18.0,"span_count":1,
            "overall_width_m_min":8.5,"overall_width_m_max":10.0,
            "qa_score_min":80,"dxf_sheets":7,"dxf_total_kb_min":220,
            "boq_grand_total_inr_min":8000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_category":"MINOR_BRIDGE","bridge_type":"RCC_TBEAM",
                                  "span_count":1},
            "geometry_input":   {"span_count":1,"span_lengths_m":[18.0],
                                  "carriageway_width_m":7.50},
            "superstructure":   {"type":"RCC_TBEAM","girder_depth_mm":1350},
            "calculations":     {"total_length_m":18.0,"span_count":1,
                                  "total_estimated_quantity_cost_inr":11500000},
        },
    },

    # ── 14: NH-353C Bridge — 4×24.75m PSC I-Girder ────────────────────────
    {
        "_meta": {
            "fixture_id":      "nh353c_4x24m_psc",
            "description":     "NH-353C 4×24.75m PSC I-Girder NHAI corridor",
            "scribd_refs":     ["5-NH-353C-67-200-to-108-539-STR-GAD-20240226"],
            "design_standard": "IRC:112-2020 NHAI",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":99.0,"span_count":4,
            "overall_width_m_min":9.0,"overall_width_m_max":14.0,
            "qa_score_min":80,"dxf_sheets":7,"dxf_total_kb_min":320,
            "boq_grand_total_inr_min":95000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_category":"MAJOR_BRIDGE","bridge_type":"PSC_IGIRDER",
                                  "span_count":4,"carriageway_config":"TWO_LANE_7M5_CLASS_A"},
            "geometry_input":   {"span_count":4,"span_lengths_m":[24.75,24.75,24.75,24.75],
                                  "carriageway_width_m":7.50,"footpath_left_m":1.5,
                                  "footpath_right_m":1.5},
            "superstructure":   {"type":"PSC_IGIRDER","deck_material":"M45",
                                  "girder_depth_mm":1800,"camber_mm":40},
            "calculations":     {"total_length_m":99.0,"span_count":4,
                                  "total_estimated_quantity_cost_inr":125000000},
        },
    },

    # ── 15: GAD-7+233.5 — 1×20m ──────────────────────────────────────────────
    {
        "_meta": {
            "fixture_id":      "gad_7_233_20m",
            "description":     "GAD at CH 7+233.5 1×20m RCC T-Beam major bridge",
            "scribd_refs":     ["GAD-7-233-5-final-pdf"],
            "design_standard": "IRC:21-2000",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":20.0,"span_count":1,
            "overall_width_m_min":8.5,"overall_width_m_max":11.0,
            "qa_score_min":80,"dxf_sheets":7,"dxf_total_kb_min":220,
            "boq_grand_total_inr_min":12000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"RCC_TBEAM","span_count":1},
            "geometry_input":   {"span_count":1,"span_lengths_m":[20.0],
                                  "carriageway_width_m":7.50,"footpath_left_m":1.0,
                                  "footpath_right_m":1.0},
            "superstructure":   {"type":"RCC_TBEAM","girder_depth_mm":1400},
            "calculations":     {"total_length_m":20.0,"span_count":1,
                                  "total_estimated_quantity_cost_inr":16500000},
        },
    },

    # ── 16: 0+600 GAD well foundation ────────────────────────────────────────
    {
        "_meta": {
            "fixture_id":      "gad_0_600_well_foundation",
            "description":     "GAD at CH 0+600 2×18m well foundation major bridge",
            "scribd_refs":     ["0-600-GAD"],
            "design_standard": "IRC:78-2014 well foundation",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":36.0,"span_count":2,
            "overall_width_m_min":8.5,"overall_width_m_max":11.0,
            "qa_score_min":75,"dxf_sheets":7,"dxf_total_kb_min":260,
            "boq_grand_total_inr_min":28000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"RCC_TBEAM","span_count":2,
                                  "foundation_type":"WELL"},
            "geometry_input":   {"span_count":2,"span_lengths_m":[18.0,18.0],
                                  "carriageway_width_m":7.50},
            "superstructure":   {"type":"RCC_TBEAM","girder_depth_mm":1300},
            "foundation_details":{"type":"WELL","pile_diameter_mm":0,
                                   "piles_per_pier":0,"pile_length_m":0.0,
                                   "pile_cutoff_level_m":105.0,"bearing_capacity_kpa":600.0},
            "calculations":     {"total_length_m":36.0,"span_count":2,
                                  "total_estimated_quantity_cost_inr":38000000},
        },
    },

    # ── 17: Modified Drawings MJB PKG-7 — 6×30m viaduct ────────────────────
    {
        "_meta": {
            "fixture_id":      "mjb_pkg7_6x30m_viaduct",
            "description":     "MJB PKG-7 viaduct 6×30m PSC I-Girder urban flyover",
            "scribd_refs":     ["ModifiedDrawings-MJB-PKG-7"],
            "design_standard": "IRC:112-2020 viaduct",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":180.0,"span_count":6,
            "overall_width_m_min":10.0,"overall_width_m_max":16.0,
            "qa_score_min":75,"dxf_sheets":7,"dxf_total_kb_min":350,
            "boq_grand_total_inr_min":200000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_category":"VIADUCT","bridge_type":"PSC_IGIRDER",
                                  "span_count":6},
            "geometry_input":   {"span_count":6,"span_lengths_m":[30.0,30.0,30.0,30.0,30.0,30.0],
                                  "carriageway_width_m":10.50,"footpath_left_m":1.5,
                                  "footpath_right_m":1.5},
            "superstructure":   {"type":"PSC_IGIRDER","deck_material":"M45",
                                  "girder_depth_mm":2000,"camber_mm":50},
            "calculations":     {"total_length_m":180.0,"span_count":6,
                                  "total_estimated_quantity_cost_inr":265000000},
        },
    },

    # ── 18: 2×8m Box Culvert multi-cell ──────────────────────────────────────
    {
        "_meta": {
            "fixture_id":      "box_culvert_2cell_8m",
            "description":     "2-cell RCC Box Culvert 2×3.0×2.5m PMGSY standard",
            "scribd_refs":     ["3-2X8M-Model"],
            "design_standard": "IRC SP:13 multi-cell box",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":8.0,"span_count":1,
            "overall_width_m_min":8.5,"overall_width_m_max":10.0,
            "qa_score_min":80,"dxf_sheets":7,"dxf_total_kb_min":200,
            "boq_grand_total_inr_min":2000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_category":"CULVERT","bridge_type":"BOX_CULVERT",
                                  "foundation_type":"OPEN"},
            "geometry_input":   {"span_count":1,"span_lengths_m":[8.0],
                                  "carriageway_width_m":7.50},
            "superstructure":   {"type":"BOX_CULVERT","deck_material":"M25",
                                  "deck_thickness_mm":300,"girder_depth_mm":0,
                                  "girder_spacing_m":0.0,"girders_per_deck_count":0},
            "calculations":     {"total_length_m":8.0,"span_count":1,
                                  "total_estimated_quantity_cost_inr":5200000},
        },
    },

    # ── 19: Viaduct BR 187 at CH 187+475 ─────────────────────────────────────
    {
        "_meta": {
            "fixture_id":      "viaduct_br187_ch187_475",
            "description":     "Viaduct BR No.187 at CH 187+475 8×25m PSC",
            "scribd_refs":     ["Gad-of-Viaduct-Br-No-187-1-at-Ch-187-475"],
            "design_standard": "IRC:112-2020 urban viaduct",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":200.0,"span_count":8,
            "overall_width_m_min":10.0,"overall_width_m_max":16.0,
            "qa_score_min":75,"dxf_sheets":7,"dxf_total_kb_min":380,
            "boq_grand_total_inr_min":220000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_category":"VIADUCT","bridge_type":"PSC_IGIRDER",
                                  "span_count":8},
            "geometry_input":   {"span_count":8,"span_lengths_m":[25.0]*8,
                                  "carriageway_width_m":10.50,"footpath_left_m":1.5,
                                  "footpath_right_m":1.5},
            "superstructure":   {"type":"PSC_IGIRDER","deck_material":"M45",
                                  "girder_depth_mm":1800,"camber_mm":40},
            "calculations":     {"total_length_m":200.0,"span_count":8,
                                  "total_estimated_quantity_cost_inr":285000000},
        },
    },

    # ── 20: GAD 24.75m RCC T-BEAM ─────────────────────────────────────────────
    {
        "_meta": {
            "fixture_id":      "gad_24_750m_rcc_tbeam",
            "description":     "GAD 24.750m RCC T-Beam standard state highway",
            "scribd_refs":     ["GAD-for-24-750m-RCC-T-BEAM-Model"],
            "design_standard": "IRC:21-2000",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":24.75,"span_count":1,
            "overall_width_m_min":8.5,"overall_width_m_max":11.0,
            "qa_score_min":80,"dxf_sheets":7,"dxf_total_kb_min":230,
            "boq_grand_total_inr_min":14000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"RCC_TBEAM","span_count":1},
            "geometry_input":   {"span_count":1,"span_lengths_m":[24.75],
                                  "carriageway_width_m":7.50,"footpath_left_m":1.0,
                                  "footpath_right_m":1.0},
            "superstructure":   {"type":"RCC_TBEAM","girder_depth_mm":1650},
            "calculations":     {"total_length_m":24.75,"span_count":1,
                                  "total_estimated_quantity_cost_inr":19500000},
        },
    },

    # ── 21: CH 2+100 Bridge ────────────────────────────────────────────────────
    {
        "_meta": {
            "fixture_id":      "bridge_ch_2_100",
            "description":     "Bridge at CH 2+100 2×12m RCC T-Beam village road",
            "scribd_refs":     ["ch-2-100"],
            "design_standard": "IRC SP:13",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":24.0,"span_count":2,
            "overall_width_m_min":8.5,"overall_width_m_max":10.0,
            "qa_score_min":80,"dxf_sheets":7,"dxf_total_kb_min":240,
            "boq_grand_total_inr_min":14000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_category":"MINOR_BRIDGE","bridge_type":"RCC_TBEAM",
                                  "span_count":2},
            "geometry_input":   {"span_count":2,"span_lengths_m":[12.0,12.0],
                                  "carriageway_width_m":7.50},
            "superstructure":   {"type":"RCC_TBEAM","girder_depth_mm":900},
            "calculations":     {"total_length_m":24.0,"span_count":2,
                                  "total_estimated_quantity_cost_inr":19000000},
        },
    },

    # ── 22: 14583-E MJB Sheet 1 — PSC Box major bridge ────────────────────────
    {
        "_meta": {
            "fixture_id":      "e_sh35_mjb_psc_box",
            "description":     "14583-E SH35 Major Bridge 4×25m PSC Box Girder",
            "scribd_refs":     ["14583-E-SH35-MJB-DD-001-Sheet-1"],
            "design_standard": "IRC:112-2020",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":100.0,"span_count":4,
            "overall_width_m_min":9.0,"overall_width_m_max":14.0,
            "qa_score_min":80,"dxf_sheets":7,"dxf_total_kb_min":320,
            "boq_grand_total_inr_min":115000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"PSC_BOX_GIRDER","span_count":4},
            "geometry_input":   {"span_count":4,"span_lengths_m":[25.0,25.0,25.0,25.0],
                                  "carriageway_width_m":7.50,"footpath_left_m":1.5,
                                  "footpath_right_m":1.5},
            "superstructure":   {"type":"PSC_BOX_GIRDER","deck_material":"M50",
                                  "girder_depth_mm":1800,"girders_per_deck_count":1,
                                  "girder_spacing_m":0.0,"camber_mm":45},
            "calculations":     {"total_length_m":100.0,"span_count":4,
                                  "total_estimated_quantity_cost_inr":148000000},
        },
    },

    # ── 23: Basantar Bridge well layout ────────────────────────────────────────
    {
        "_meta": {
            "fixture_id":      "basantar_bridge_well",
            "description":     "Basantar Bridge 3×20m well foundation RCC",
            "scribd_refs":     ["01-Basantar-Bridge-Gad-well-Layout1-pdf1-pdf"],
            "design_standard": "IRC:78-2014 well + IRC:21",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":60.0,"span_count":3,
            "overall_width_m_min":8.5,"overall_width_m_max":11.0,
            "qa_score_min":75,"dxf_sheets":7,"dxf_total_kb_min":270,
            "boq_grand_total_inr_min":42000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"RCC_TBEAM","span_count":3,
                                  "foundation_type":"WELL"},
            "geometry_input":   {"span_count":3,"span_lengths_m":[20.0,20.0,20.0],
                                  "carriageway_width_m":7.50},
            "superstructure":   {"type":"RCC_TBEAM","girder_depth_mm":1400},
            "foundation_details":{"type":"WELL","pile_diameter_mm":0,
                                   "piles_per_pier":0,"pile_length_m":0.0,
                                   "pile_cutoff_level_m":104.0,"bearing_capacity_kpa":550.0},
            "calculations":     {"total_length_m":60.0,"span_count":3,
                                  "total_estimated_quantity_cost_inr":56000000},
        },
    },

    # ── 24: PP-05 Bridge 2023 — 1×30m PSC I-Girder ────────────────────────────
    {
        "_meta": {
            "fixture_id":      "pp05_30m_psc",
            "description":     "PP-05 May 2023 1×30m PSC I-Girder major bridge",
            "scribd_refs":     ["PP-05-DATE-27-05-23"],
            "design_standard": "IRC:112-2020",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":30.0,"span_count":1,
            "overall_width_m_min":8.5,"overall_width_m_max":12.0,
            "qa_score_min":80,"dxf_sheets":7,"dxf_total_kb_min":240,
            "boq_grand_total_inr_min":22000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"PSC_IGIRDER","span_count":1},
            "geometry_input":   {"span_count":1,"span_lengths_m":[30.0],
                                  "carriageway_width_m":7.50,"footpath_left_m":1.5,
                                  "footpath_right_m":1.5},
            "superstructure":   {"type":"PSC_IGIRDER","deck_material":"M40",
                                  "girder_depth_mm":1950,"camber_mm":40},
            "calculations":     {"total_length_m":30.0,"span_count":1,
                                  "total_estimated_quantity_cost_inr":30000000},
        },
    },

    # ── 25: SRCTIP DOR Bridge — 4×20m simply supported ─────────────────────────
    {
        "_meta": {
            "fixture_id":      "srctip_4x20m",
            "description":     "SRCTIP DOR NNM 4×20m PSC I-Girder international aid",
            "scribd_refs":     ["Bridge-Drawings-Part-II-for-SRCTIP-DOR-W-NNM-ICB-3"],
            "design_standard": "IRC:112-2020 + ADB spec",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":80.0,"span_count":4,
            "overall_width_m_min":8.5,"overall_width_m_max":12.0,
            "qa_score_min":75,"dxf_sheets":7,"dxf_total_kb_min":300,
            "boq_grand_total_inr_min":65000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"PSC_IGIRDER","span_count":4},
            "geometry_input":   {"span_count":4,"span_lengths_m":[20.0,20.0,20.0,20.0],
                                  "carriageway_width_m":7.50,"footpath_left_m":1.0,
                                  "footpath_right_m":1.0},
            "superstructure":   {"type":"PSC_IGIRDER","deck_material":"M45",
                                  "girder_depth_mm":1600,"camber_mm":35},
            "calculations":     {"total_length_m":80.0,"span_count":4,
                                  "total_estimated_quantity_cost_inr":86000000},
        },
    },

    # ── 26: Launching apron 10.1m — minor bridge scour protection ─────────────
    {
        "_meta": {
            "fixture_id":      "launching_apron_10m",
            "description":     "Revised GAD with launching apron 1×10.1m minor bridge",
            "scribd_refs":     ["Revised-GAD-for-Launching-Appron-10-1m"],
            "design_standard": "IRC:78-2014 scour protection",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":10.1,"span_count":1,
            "overall_width_m_min":8.5,"overall_width_m_max":10.0,
            "qa_score_min":75,"dxf_sheets":7,"dxf_total_kb_min":200,
            "boq_grand_total_inr_min":5000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_category":"MINOR_BRIDGE","bridge_type":"RCC_TBEAM",
                                  "span_count":1},
            "geometry_input":   {"span_count":1,"span_lengths_m":[10.1],
                                  "carriageway_width_m":7.50},
            "superstructure":   {"type":"RCC_TBEAM","girder_depth_mm":800},
            "calculations":     {"total_length_m":10.1,"span_count":1,
                                  "total_estimated_quantity_cost_inr":7200000},
        },
    },

    # ── 27: MR-5-L-C-29 — 4×30m continuous PSC ────────────────────────────────
    {
        "_meta": {
            "fixture_id":      "mr5_lc29_4x30m_continuous",
            "description":     "MR-5 LC-29 4×30m PSC I-Girder continuous major bridge",
            "scribd_refs":     ["MR-5-L-C-29-120314-Model"],
            "design_standard": "IRC:112-2020 continuous",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":120.0,"span_count":4,
            "overall_width_m_min":9.0,"overall_width_m_max":14.0,
            "qa_score_min":75,"dxf_sheets":7,"dxf_total_kb_min":320,
            "boq_grand_total_inr_min":110000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"PSC_IGIRDER","span_count":4,
                                  "span_configuration":"CONTINUOUS"},
            "geometry_input":   {"span_count":4,"span_lengths_m":[30.0,30.0,30.0,30.0],
                                  "carriageway_width_m":7.50,"footpath_left_m":1.5,
                                  "footpath_right_m":1.5},
            "superstructure":   {"type":"PSC_IGIRDER","deck_material":"M45",
                                  "girder_depth_mm":2000,"camber_mm":50},
            "calculations":     {"total_length_m":120.0,"span_count":4,
                                  "total_estimated_quantity_cost_inr":148000000},
        },
    },

    # ── 28: GAD Bridge general arrangement — 3×18m skew 15° ──────────────────
    {
        "_meta": {
            "fixture_id":      "gad_3x18m_skew15",
            "description":     "GAD of Bridge 3×18m skew 15° RCC T-Beam state road",
            "scribd_refs":     ["01-Gad-of-Bridge","GAD-for-24-750m-RCC-T-BEAM-Model"],
            "design_standard": "IRC:21-2000 skew bridge",
            "expected_qa_grade":"A",
        },
        "expected": {
            "total_length_m":54.0,"span_count":3,
            "overall_width_m_min":8.5,"overall_width_m_max":11.0,
            "qa_score_min":75,"dxf_sheets":7,"dxf_total_kb_min":280,
            "boq_grand_total_inr_min":38000000,"zip_has_manifest":True,
            "zip_has_dxf":True,"zip_has_xlsx":True,
        },
        "overrides": {
            "bridge_selection": {"bridge_type":"RCC_TBEAM","span_count":3},
            "geometry_input":   {"span_count":3,"span_lengths_m":[18.0,18.0,18.0],
                                  "skew_angle_deg":15.0,"skew_direction":"RIGHT",
                                  "carriageway_width_m":7.50},
            "superstructure":   {"type":"RCC_TBEAM","girder_depth_mm":1350},
            "calculations":     {"total_length_m":54.0,"span_count":3,
                                  "total_estimated_quantity_cost_inr":52000000},
        },
    },
]

# ── Base fixture template ────────────────────────────────────────────────────
BASE = json.loads((OUT / "simple_12m.json").read_text())

def generate_fixture(spec: dict) -> dict:
    """Merge *spec* overrides onto the simple_12m base fixture."""
    import copy
    f = copy.deepcopy(BASE)
    # Replace _meta and expected entirely
    f["_meta"]    = spec["_meta"]
    f["expected"] = spec["expected"]
    # Apply project overrides (shallow merge per sub-model)
    for section, vals in spec.get("overrides", {}).items():
        if section in f["project"]:
            f["project"][section].update(vals)
        else:
            f["project"][section] = vals
    # Ensure span_count / span_lengths_m consistency
    gi = f["project"]["geometry_input"]
    gi["span_count"] = len(gi["span_lengths_m"])
    f["project"]["calculations"]["span_count"] = gi["span_count"]
    f["project"]["calculations"]["total_length_m"] = sum(gi["span_lengths_m"])
    # Fix bridge_selection span_count
    f["project"]["bridge_selection"]["span_count"] = gi["span_count"]
    return f

if __name__ == "__main__":
    generated = 0
    for spec in FIXTURES:
        fid  = spec["_meta"]["fixture_id"]
        path = OUT / f"{fid}.json"
        if path.exists():
            print(f"  [skip] {fid}.json  (already exists)")
            continue
        data = generate_fixture(spec)
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        print(f"  [OK]   {fid}.json  ({path.stat().st_size} bytes)")
        generated += 1
    total = len(list(OUT.glob("*.json"))) - 1  # exclude this script
    print(f"\n  Generated {generated} new fixtures. Total: {total}/28")
