"""IFC 4.3 (IFC4X3) export — the openBIM hand-off (W08).

Writes the *physical* skeleton of the bridge — site, facility, deck slab,
girders, piers, abutments, piles — so a reviewer can open the model in any
BIM tool and measure it. It deliberately does **not** carry design-analysis
parameters (hydraulic data, load classes, BOQ rates): those are BridgeCAD
concerns, and the loss is stated in ``docs/interop.md``.

``ifcopenshell`` is an optional dependency (``pip install .[ifc]``). Import is
lazy so ``import bridgecad_export`` never fails; :func:`ifc_available` and the
``ImportError`` from :func:`export_ifc` say what to install.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

IFC_SCHEMA = "IFC4X3"
"""IFC 4.3's schema identifier. 4.3 renamed the schema string from IFC4 to IFC4X3."""

_DEFAULT_DECK_THICKNESS_MM = 200.0
_DEFAULT_GIRDER_DEPTH_MM = 900.0


def ifc_available() -> bool:
    """True when ``ifcopenshell`` can be imported in this interpreter."""
    try:
        import ifcopenshell  # noqa: F401
    except ImportError:
        return False
    return True


def _require_ifcopenshell() -> Any:
    try:
        import ifcopenshell
    except ImportError as exc:  # pragma: no cover - exercised via ifc_available()
        raise ImportError(
            "IFC export needs ifcopenshell: pip install 'bridgecad-enterprise-suite[ifc]'"
        ) from exc
    return ifcopenshell


def _new_guid() -> str:
    """A fresh IFC GlobalId (22-char base64). ``ifcopenshell.guid`` is a module."""
    import ifcopenshell.guid

    return str(ifcopenshell.guid.new())


def _point(ifc: Any, x: float, y: float, z: float) -> Any:
    return ifc.createIfcCartesianPoint((float(x), float(y), float(z)))


def _placement3d(ifc: Any, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Any:
    return ifc.createIfcAxis2Placement3D(_point(ifc, x, y, z), None, None)


def _entity(
    ifc: Any,
    *,
    profile_xy: tuple[float, float],
    depth_m: float,
    origin: tuple[float, float, float],
    context: Any,
    relative_to: Any,
    element_cls: str,
    name: str,
    predefined: str | None = None,
) -> Any:
    """Build one extruded rectangular product and return the IFC entity."""
    profile = ifc.createIfcRectangleProfileDef(
        "AREA", None, None, float(profile_xy[0]), float(profile_xy[1])
    )
    solid = ifc.createIfcExtrudedAreaSolid(
        profile,
        _placement3d(ifc),
        ifc.createIfcDirection((0.0, 0.0, 1.0)),
        float(depth_m),
    )
    shape = ifc.createIfcProductDefinitionShape(
        None, None, [ifc.createIfcShapeRepresentation(context, "Body", "SweptSolid", [solid])]
    )
    kwargs: dict[str, Any] = {
        "GlobalId": _new_guid(),
        "OwnerHistory": None,
        "Name": name,
        "Description": None,
        "ObjectType": None,
        "ObjectPlacement": ifc.createIfcLocalPlacement(relative_to, _placement3d(ifc, *origin)),
        "Representation": shape,
        "Tag": None,
    }
    if predefined is not None:
        kwargs["PredefinedType"] = predefined
    return getattr(ifc, "create" + element_cls)(**kwargs)


def export_ifc(project: Any, output_path: str | Path) -> Path:
    """Write *project* to an IFC4X3 STEP file and return the path.

    Raises ``ImportError`` when ifcopenshell is not installed.
    """
    ifc = _require_ifcopenshell()

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    gi = project.geometry_input
    ss = project.superstructure
    sub = project.substructure
    master = project.project_master

    length_m = float(gi.total_length_m)
    width_m = float(gi.overall_width_m)
    deck_t_m = (
        float(getattr(ss, "total_deck_thickness_mm", 0) or _DEFAULT_DECK_THICKNESS_MM) / 1000.0
    )
    girder_depth_m = float(getattr(ss, "girder_depth_mm", 0) or _DEFAULT_GIRDER_DEPTH_MM) / 1000.0
    n_girders = int(getattr(ss, "girders_per_deck_count", 0) or 0)
    girder_spacing_m = float(getattr(ss, "girder_spacing_m", 0) or 0.0)
    n_spans = int(getattr(gi, "span_count", 0) or 1)
    pier_h_m = float(getattr(sub, "pier_height_typical_m", 0) or 0.0)
    pier_w_m = float(getattr(sub, "pier_shaft_width_m", 0) or 0.0)
    pier_l_m = float(getattr(sub, "pier_shaft_length_m", 0) or 0.0)
    pile_d_m = float(getattr(project.foundation_details, "pile_diameter_mm", 0) or 0.0) / 1000.0
    pile_l_m = float(getattr(project.foundation_details, "pile_length_m", 0) or 0.0)

    f = ifc.file(schema=IFC_SCHEMA)

    context = f.createIfcGeometricRepresentationContext(
        None, "Model", 3, 1.0e-5, _placement3d(f), None
    )
    units = f.createIfcUnitAssignment([f.createIfcSIUnit(None, "LENGTHUNIT", None, "METRE")])

    name = str(getattr(master, "bridge_name", "") or "BRIDGE")
    project_ent = f.createIfcProject(
        _new_guid(), None, name, None, None, None, None, [context], units
    )

    site = f.createIfcSite(
        GlobalId=_new_guid(),
        OwnerHistory=None,
        Name="Site",
        Description=None,
        ObjectType=None,
        ObjectPlacement=None,
        Representation=None,
        LongName=None,
        CompositionType="ELEMENT",
    )
    root_placement = f.createIfcLocalPlacement(None, _placement3d(f))
    bridge = f.createIfcBridge(
        GlobalId=_new_guid(),
        OwnerHistory=None,
        Name=name,
        Description=str(getattr(master, "project_title", "") or "") or None,
        ObjectType=None,
        ObjectPlacement=root_placement,
        Representation=None,
        LongName=str(getattr(master, "revision", "") or "") or None,
        CompositionType="ELEMENT",
    )

    f.createIfcRelAggregates(_new_guid(), None, None, None, project_ent, [site])
    f.createIfcRelAggregates(_new_guid(), None, None, None, site, [bridge])

    elements: list[Any] = []

    # Deck slab: x = width, y = length, extruded by the deck thickness.
    elements.append(
        _entity(
            f,
            profile_xy=(width_m, length_m),
            depth_m=deck_t_m,
            origin=(0.0, 0.0, 0.0),
            context=context,
            relative_to=root_placement,
            element_cls="IfcSlab",
            name="DECK",
            predefined="FLOOR",
        )
    )

    # Girder lines, evenly spaced across the width.
    if n_girders > 0 and girder_spacing_m > 0:
        total_girder_width = girder_spacing_m * (n_girders - 1)
        for i in range(n_girders):
            y = -total_girder_width / 2.0 + i * girder_spacing_m
            elements.append(
                _entity(
                    f,
                    profile_xy=(0.3, length_m),
                    depth_m=girder_depth_m,
                    origin=(0.0, y, -girder_depth_m),
                    context=context,
                    relative_to=root_placement,
                    element_cls="IfcBeam",
                    name=f"GIRDER-{i + 1}",
                    predefined="BEAM",
                )
            )

    # Intermediate piers.
    for i in range(max(n_spans - 1, 0)):
        elements.append(
            _entity(
                f,
                profile_xy=(pier_w_m or 1.2, pier_l_m or width_m),
                depth_m=pier_h_m,
                origin=(0.0, 0.0, -pier_h_m - deck_t_m),
                context=context,
                relative_to=root_placement,
                element_cls="IfcColumn",
                name=f"PIER-{i + 1}",
                predefined="COLUMN",
            )
        )

    # Two abutments (IfcWall).
    for side in ("A1", "A2"):
        elements.append(
            _entity(
                f,
                profile_xy=(pier_w_m or 1.0, pier_l_m or width_m),
                depth_m=pier_h_m or 3.0,
                origin=(0.0, 0.0, -pier_h_m - deck_t_m),
                context=context,
                relative_to=root_placement,
                element_cls="IfcWall",
                name=f"ABUTMENT-{side}",
                predefined="SOLIDWALL",
            )
        )

    # Pile group under each pier/abutment footprint.
    if pile_d_m > 0 and pile_l_m > 0:
        for i in range(4):
            elements.append(
                _entity(
                    f,
                    profile_xy=(pile_d_m, pile_d_m),
                    depth_m=pile_l_m,
                    origin=(0.0, 0.0, -pier_h_m - deck_t_m - pile_l_m),
                    context=context,
                    relative_to=root_placement,
                    element_cls="IfcPile",
                    name=f"PILE-{i + 1}",
                    predefined="BORED",
                )
            )

    if elements:
        f.createIfcRelContainedInSpatialStructure(_new_guid(), None, None, None, elements, bridge)

    f.header.file_name.name = out.name
    # Fixed timestamp keeps the STEP header stable across runs.
    f.header.file_name.time_stamp = "1970-01-01T00:00:00"
    f.write(str(out))
    return out


def read_ifc_summary(path: str | Path) -> dict:
    """Re-open *path* and summarise what the IFC file actually contains.

    This is the "import" half of the IFC round-trip: it reads the geometry back
    out of the written file rather than trusting the exporter's inputs.
    """
    ifc = _require_ifcopenshell()
    src = Path(path)
    model = ifc.open(str(src))

    projects = model.by_type("IfcProject")
    summary: dict = {
        "schema": model.schema,
        "name": getattr(projects[0], "Name", None) if projects else None,
        "products": len(model.by_type("IfcProduct")),
        "counts": {
            t: len(model.by_type(t))
            for t in ("IfcSlab", "IfcBeam", "IfcColumn", "IfcWall", "IfcPile")
        },
        "byte_size": src.stat().st_size,
    }
    slabs = model.by_type("IfcSlab")
    if slabs:
        try:
            solid = slabs[0].Representation.Representations[0].Items[0]
            profile = solid.SweptArea
            summary["deck_width_m"] = float(profile.XDim)
            summary["deck_length_m"] = float(profile.YDim)
            summary["deck_thickness_m"] = float(solid.Depth)
        except (AttributeError, IndexError, TypeError):  # pragma: no cover - defensive
            pass
    return summary


__all__ = [
    "IFC_SCHEMA",
    "export_ifc",
    "ifc_available",
    "read_ifc_summary",
]
