#!/usr/bin/env python3
"""Upload google_ads creatives into matching PMax asset groups + Search ad groups."""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

from google.ads.googleads.errors import GoogleAdsException
from PIL import Image

from scripts.google_ads_client import customer_id, load_client, login_customer_id

ROOT = Path(__file__).resolve().parents[1]
IMG_DIR = ROOT / "image" / "google_ads"

cid = customer_id()
login = login_customer_id()
client = load_client()

ga = client.get_service("GoogleAdsService")
asset_service = client.get_service("AssetService")
aga_service = client.get_service("AssetGroupAssetService")
ca_service = client.get_service("CampaignAssetService")
adga_service = client.get_service("AdGroupAssetService")
FieldType = client.enums.AssetFieldTypeEnum

# PMax asset_group_id -> image stems (files under image/google_ads)
PMAX_MAP: dict[int, list[str]] = {
    # ФГДС / эндоскопия
    6618409161: [
        "ads_endoscopy_fgds_1x1",
        "ads_endoscopy_fgds_v2_1x1",
        "ads_colonoscopy_1x1",
        "endoscopy_happy_consult_1x1",
        "endoscopy_happy_doctor_patient_1x1",
        "endoscopy_happy_clinic_16x9",
    ],
    # Gynecology
    6492680232: ["ads_gynecology_1x1", "ads_gynecology_v2_1x1"],
    # Urology
    6491751130: ["ads_urology_1x1", "ads_urology_v2_1x1"],
    # Spravki
    6724845462: [
        "ads_spravki_school_1x1",
        "ads_spravki_school_boy_1x1",
        "ads_spravki_abiturent_1x1",
        "ads_spravki_kindergarten_1x1",
        "ads_spravki_1x1",
    ],
    # Phlebology
    6490911764: ["ads_phlebology_1x1", "ads_phlebology_v2_1x1"],
    # LOR
    6522836532: ["ads_lor_1x1", "ads_lor_v2_1x1"],
    # Laser
    6497858511: ["ads_laser_1x1", "ads_laser_v2_1x1", "ads_general_clinic_16x9"],
    # Neurology
    6525336331: ["ads_neurology_1x1", "ads_neurology_v2_1x1"],
    # Endocrinology
    6495436623: ["ads_endocrinology_1x1", "ads_endocrinology_v2_1x1"],
}

# Search ad_group_id -> stems (AD_IMAGE)
SEARCH_AG_MAP: dict[int, list[str]] = {
    163444539598: [  # Эндоскопия
        "ads_endoscopy_fgds_1x1",
        "ads_endoscopy_fgds_v2_1x1",
        "endoscopy_happy_consult_1x1",
    ],
    204146025972: ["ads_colonoscopy_1x1", "ads_colonoscopy_v2_1x1"],  # Колоноскопия
    201683003489: [
        "ads_gastroenterologist_1x1",
        "ads_gastroenterologist_v2_1x1",
    ],  # Гастроэнтеролог
    154170402610: ["ads_gynecology_1x1", "ads_gynecology_v2_1x1"],  # Гинеколог_wk
    154170402650: ["ads_gynecology_1x1", "ads_gynecology_v2_1x1"],  # konsult
    158220197919: ["ads_urology_1x1", "ads_urology_v2_1x1"],  # Уролог konsult
    158220197959: ["ads_urology_1x1", "ads_urology_v2_1x1"],
    161700564858: [  # Справки
        "ads_spravki_school_1x1",
        "ads_spravki_abiturent_1x1",
        "ads_spravki_kindergarten_1x1",
        "ads_spravki_school_boy_1x1",
    ],
    160396002193: ["ads_phlebology_1x1", "ads_phlebology_v2_1x1"],
    164914517474: ["ads_lor_1x1", "ads_lor_v2_1x1"],
    162013236680: ["ads_laser_1x1", "ads_laser_v2_1x1"],
    168001575823: ["ads_neurology_1x1", "ads_neurology_v2_1x1"],
    159512495992: ["ads_endocrinology_1x1", "ads_endocrinology_v2_1x1"],
    159843160777: ["ads_cardiology_1x1", "ads_cardiology_v2_1x1"],
    164528329630: ["ads_therapy_1x1", "ads_therapy_v2_1x1"],
    162702188380: ["ads_proctology_1x1", "ads_proctology_v2_1x1"],
    159565555117: ["ads_allergology_1x1", "ads_allergology_v2_1x1"],
    196762490817: ["ads_ultrasound_1x1", "ads_ultrasound_v2_1x1"],
}

# Also attach landscape to Search campaign-level AD_IMAGE
SEARCH_CAMP = 21018894876
SEARCH_CAMP_IMAGES = ["ads_general_clinic_16x9", "ads_demand_gen_clinic_1x1", "ads_demand_gen_v2_1x1"]


def log(msg: str) -> None:
    print(msg, flush=True)


def find_file(stem: str) -> Path | None:
    for ext in (".png", ".jpg", ".jpeg"):
        p = IMG_DIR / f"{stem}{ext}"
        if p.exists():
            return p
    return None


def to_square_jpeg(path: Path, size: int = 1200) -> bytes:
    im = Image.open(path).convert("RGB")
    # center-crop to square then resize
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    im = im.crop((left, top, left + side, top + side)).resize(
        (size, size), Image.Resampling.LANCZOS
    )
    buf = BytesIO()
    im.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def to_landscape_jpeg(path: Path, width: int = 1200, height: int = 628) -> bytes:
    """1.91:1 marketing image — cover crop."""
    im = Image.open(path).convert("RGB")
    target_ratio = width / height
    w, h = im.size
    ratio = w / h
    if ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        im = im.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        im = im.crop((0, top, w, top + new_h))
    im = im.resize((width, height), Image.Resampling.LANCZOS)
    buf = BytesIO()
    im.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def upload_image_asset(data: bytes, name: str) -> str:
    op = client.get_type("AssetOperation")
    asset = op.create
    asset.name = name[:128]
    asset.type_ = client.enums.AssetTypeEnum.IMAGE
    asset.image_asset.data = data
    resp = asset_service.mutate_assets(customer_id=cid, operations=[op])
    return resp.results[0].resource_name


# cache stem -> {square_rn, landscape_rn}
_cache: dict[str, dict[str, str]] = {}


def assets_for(stem: str) -> dict[str, str]:
    if stem in _cache:
        return _cache[stem]
    path = find_file(stem)
    if not path:
        raise FileNotFoundError(stem)
    out = {}
    try:
        sq = to_square_jpeg(path)
        out["square"] = upload_image_asset(sq, f"{stem}_sq")
        log(f"  uploaded square {stem}")
    except GoogleAdsException as e:
        log(f"  square FAIL {stem}: {e.failure.errors[0].message}")
    try:
        ls = to_landscape_jpeg(path)
        out["landscape"] = upload_image_asset(ls, f"{stem}_ls")
        log(f"  uploaded landscape {stem}")
    except GoogleAdsException as e:
        log(f"  landscape FAIL {stem}: {e.failure.errors[0].message}")
    _cache[stem] = out
    return out


def link_pmax(ag_rn: str, asset_rn: str, field: str) -> bool:
    op = client.get_type("AssetGroupAssetOperation")
    row = op.create
    row.asset_group = ag_rn
    row.asset = asset_rn
    row.field_type = getattr(FieldType, field)
    try:
        aga_service.mutate_asset_group_assets(customer_id=cid, operations=[op])
        return True
    except GoogleAdsException as e:
        msg = e.failure.errors[0].message
        # duplicate / already exists — ok
        if "already" in msg.lower() or "duplicate" in msg.lower():
            return True
        log(f"    link PMax {field} FAIL: {msg}")
        return False


def link_search_ag(ag_id: int, asset_rn: str) -> bool:
    op = client.get_type("AdGroupAssetOperation")
    row = op.create
    row.ad_group = f"customers/{cid}/adGroups/{ag_id}"
    row.asset = asset_rn
    row.field_type = FieldType.AD_IMAGE
    try:
        adga_service.mutate_ad_group_assets(customer_id=cid, operations=[op])
        return True
    except GoogleAdsException as e:
        msg = e.failure.errors[0].message
        if "already" in msg.lower() or "duplicate" in msg.lower():
            return True
        log(f"    link Search AG {ag_id} FAIL: {msg}")
        return False


def link_campaign_ad_image(camp_id: int, asset_rn: str) -> bool:
    op = client.get_type("CampaignAssetOperation")
    row = op.create
    row.campaign = f"customers/{cid}/campaigns/{camp_id}"
    row.asset = asset_rn
    row.field_type = FieldType.AD_IMAGE
    try:
        ca_service.mutate_campaign_assets(customer_id=cid, operations=[op])
        return True
    except GoogleAdsException as e:
        msg = e.failure.errors[0].message
        if "already" in msg.lower() or "duplicate" in msg.lower():
            return True
        log(f"    link Camp AD_IMAGE FAIL: {msg}")
        return False


def main() -> int:
    # resolve asset group resource names
    ag_rn = {}
    for r in ga.search(
        customer_id=cid,
        query="""
        SELECT asset_group.id, asset_group.resource_name
        FROM asset_group WHERE asset_group.status = 'ENABLED'
        """,
    ):
        ag_rn[r.asset_group.id] = r.asset_group.resource_name

    log("=== PMax uploads ===")
    for ag_id, stems in PMAX_MAP.items():
        rn = ag_rn.get(ag_id)
        if not rn:
            log(f"skip missing AG {ag_id}")
            continue
        log(f"\nPMax AG {ag_id}")
        ok_sq = ok_ls = 0
        for stem in stems:
            try:
                assets = assets_for(stem)
            except FileNotFoundError:
                log(f"  missing file {stem}")
                continue
            if "square" in assets and link_pmax(rn, assets["square"], "SQUARE_MARKETING_IMAGE"):
                ok_sq += 1
                log(f"  +SQUARE {stem}")
            if "landscape" in assets and link_pmax(rn, assets["landscape"], "MARKETING_IMAGE"):
                ok_ls += 1
                log(f"  +MARKETING {stem}")
        log(f"  done squares={ok_sq} landscapes={ok_ls}")

    log("\n=== Search ad group AD_IMAGE ===")
    for ag_id, stems in SEARCH_AG_MAP.items():
        log(f"\nSearch AG {ag_id}")
        n = 0
        for stem in stems:
            try:
                assets = assets_for(stem)
            except FileNotFoundError:
                log(f"  missing {stem}")
                continue
            # prefer square for AD_IMAGE
            asset_rn = assets.get("square") or assets.get("landscape")
            if asset_rn and link_search_ag(ag_id, asset_rn):
                n += 1
                log(f"  +AD_IMAGE {stem}")
        log(f"  linked {n}")

    log("\n=== Search campaign-level images ===")
    for stem in SEARCH_CAMP_IMAGES:
        try:
            assets = assets_for(stem)
        except FileNotFoundError:
            continue
        for key in ("landscape", "square"):
            if key in assets and link_campaign_ad_image(SEARCH_CAMP, assets[key]):
                log(f"  +camp {stem} {key}")

    log("\n=== DONE ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
