#!/usr/bin/env python3
"""Apply Google Ads priorities 1-4 (2026-08-05). Baseline must exist first."""
from __future__ import annotations

import sys

from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2

from scripts.google_ads_client import customer_id, load_client, login_customer_id

cid = customer_id()
login = login_customer_id()
client = load_client()

ga = client.get_service("GoogleAdsService")
shared_set_service = client.get_service("SharedSetService")
shared_criterion_service = client.get_service("SharedCriterionService")
campaign_shared_set_service = client.get_service("CampaignSharedSetService")
campaign_budget_service = client.get_service("CampaignBudgetService")
ad_group_service = client.get_service("AdGroupService")
ad_group_criterion_service = client.get_service("AdGroupCriterionService")
ad_group_ad_service = client.get_service("AdGroupAdService")
asset_service = client.get_service("AssetService")
asset_group_asset_service = client.get_service("AssetGroupAssetService")
conversion_action_service = client.get_service("ConversionActionService")

MatchType = client.enums.KeywordMatchTypeEnum
AdGroupStatus = client.enums.AdGroupStatusEnum
CriterionStatus = client.enums.AdGroupCriterionStatusEnum
AdGroupAdStatus = client.enums.AdGroupAdStatusEnum
SharedSetType = client.enums.SharedSetTypeEnum
AssetFieldType = client.enums.AssetFieldTypeEnum

CAMP_SEARCH = 21018894876
CAMP_SEARCH_RN = f"customers/{cid}/campaigns/{CAMP_SEARCH}"
BUDGET_SEARCH = f"customers/{cid}/campaignBudgets/14029375105"
BUDGET_GYN_VIDEO = f"customers/{cid}/campaignBudgets/14936030535"
BUDGET_ENDOKRIN = f"customers/{cid}/campaignBudgets/13481934850"

AG_CARDIO = 159843160777
AG_NEURO = 168001575823
AG_THERAPY = 164528329630
AG_PROCTO = 162702188380
AG_ALLERG = 159565555117
AG_LOR = 164914517474
AG_SPRAVKI = 161700564858
AG_GYN = 154170402610
AG_GYN_KONS = 154170402650
AG_FLEB = 160396002193
AG_LASER = 162013236680
AG_URO_KONS = 158220197919
AG_URO = 158220197959
AG_ENDOKRIN = 159512495992

ZERO_NEG_AGS = [
    AG_CARDIO,
    AG_THERAPY,
    AG_NEURO,
    AG_PROCTO,
    AG_ALLERG,
    AG_LOR,
    AG_SPRAVKI,
    AG_FLEB,
    AG_LASER,
    AG_URO_KONS,
    AG_URO,
]

URL_UZI = "https://kravira.by/services/diagnosticheskoe-otdelenie/yzi/"
URL_UZI_HEART = "https://kravira.by/services/diagnosticheskoe-otdelenie/yzi/serdtse-i-sosudy/uzi-serdtsa/"
URL_CARDIO = None  # keep ad-level URLs

SHARED_NAME = "MRS_Search_Efficiency_2026-08"

NEGATIVES_SHARED = [
    "нордин",
    "лодэ",
    "лоде",
    "вакансия",
    "вакансии",
    "работа",
    "учеба",
    "учёба",
    "курс",
    "обучение",
    "это",
    "что такое",
    "википедия",
    "бесплатно",
    "поликлиника",
]

NEURO_EXTRA = ["ортопед", "травматолог", "ревматолог"]


def log(msg: str) -> None:
    print(msg, flush=True)


def print_err(label: str, e: GoogleAdsException) -> None:
    log(f"{label}: FAIL")
    for err in e.failure.errors:
        unpub = getattr(err.details, "unpublished_error_code", None) if err.details else None
        log(f"  {err.message} {unpub or ''}")


def mutate_criteria(ops, label: str):
    if not ops:
        log(f"{label}: nothing")
        return
    try:
        resp = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=cid, operations=ops
        )
        log(f"{label}: OK {len(resp.results)}")
    except GoogleAdsException as e:
        print_err(label, e)
        ok = 0
        for op in ops:
            try:
                ad_group_criterion_service.mutate_ad_group_criteria(
                    customer_id=cid, operations=[op]
                )
                ok += 1
            except GoogleAdsException as e2:
                log(f"  skip: {e2.failure.errors[0].message}")
        log(f"{label}: partial {ok}/{len(ops)}")


# ---------- P1 shared negatives ----------
def p1_shared_negatives():
    log("\n=== P1 shared negatives ===")
    shared_rn = None
    for r in ga.search(
        customer_id=cid,
        query=f"""
        SELECT shared_set.id, shared_set.resource_name, shared_set.name
        FROM shared_set WHERE shared_set.name = '{SHARED_NAME}' AND shared_set.status != 'REMOVED'
        """,
    ):
        shared_rn = r.shared_set.resource_name
        log(f"existing shared set {shared_rn}")

    if not shared_rn:
        op = client.get_type("SharedSetOperation")
        ss = op.create
        ss.name = SHARED_NAME
        ss.type_ = SharedSetType.NEGATIVE_KEYWORDS
        resp = shared_set_service.mutate_shared_sets(customer_id=cid, operations=[op])
        shared_rn = resp.results[0].resource_name
        log(f"created shared set {shared_rn}")

    existing = set()
    sid = shared_rn.split("/")[-1]
    for r in ga.search(
        customer_id=cid,
        query=f"""
        SELECT shared_criterion.keyword.text FROM shared_criterion
        WHERE shared_set.id = {sid}
        """,
    ):
        existing.add(r.shared_criterion.keyword.text.lower())

    ops = []
    for text in NEGATIVES_SHARED:
        if text.lower() in existing:
            continue
        o = client.get_type("SharedCriterionOperation")
        c = o.create
        c.shared_set = shared_rn
        c.keyword.text = text
        c.keyword.match_type = MatchType.PHRASE
        ops.append(o)
    if ops:
        try:
            resp = shared_criterion_service.mutate_shared_criteria(
                customer_id=cid, operations=ops
            )
            log(f"shared members OK {len(resp.results)}")
        except GoogleAdsException as e:
            print_err("shared members", e)
            for o in ops:
                try:
                    shared_criterion_service.mutate_shared_criteria(
                        customer_id=cid, operations=[o]
                    )
                except GoogleAdsException:
                    pass
    else:
        log("shared members already present")

    # attach to Search
    linked = False
    for r in ga.search(
        customer_id=cid,
        query=f"""
        SELECT campaign_shared_set.resource_name FROM campaign_shared_set
        WHERE campaign.id = {CAMP_SEARCH} AND shared_set.id = {sid}
        """,
    ):
        linked = True
    if not linked:
        op = client.get_type("CampaignSharedSetOperation")
        css = op.create
        css.campaign = CAMP_SEARCH_RN
        css.shared_set = shared_rn
        try:
            campaign_shared_set_service.mutate_campaign_shared_sets(
                customer_id=cid, operations=[op]
            )
            log("linked shared set to Search: OK")
        except GoogleAdsException as e:
            print_err("link shared set", e)
    else:
        log("shared set already linked to Search")

    # Neuro extra AG negatives
    have = set()
    for r in ga.search(
        customer_id=cid,
        query=f"""
        SELECT ad_group_criterion.keyword.text FROM ad_group_criterion
        WHERE ad_group.id = {AG_NEURO} AND ad_group_criterion.negative = TRUE
          AND ad_group_criterion.status != 'REMOVED'
        """,
    ):
        have.add(r.ad_group_criterion.keyword.text.lower())
    ops = []
    for text in NEURO_EXTRA:
        if text in have:
            continue
        o = client.get_type("AdGroupCriterionOperation")
        c = o.create
        c.ad_group = f"customers/{cid}/adGroups/{AG_NEURO}"
        c.negative = True
        c.keyword.text = text
        c.keyword.match_type = MatchType.PHRASE
        ops.append(o)
    mutate_criteria(ops, "P1 neuro specialty negatives")

    # Pause competitor conquest positives in Gyn_wk
    ops = []
    for r in ga.search(
        customer_id=cid,
        query=f"""
        SELECT ad_group_criterion.resource_name, ad_group_criterion.keyword.text
        FROM ad_group_criterion
        WHERE ad_group.id = {AG_GYN} AND ad_group_criterion.negative = FALSE
          AND ad_group_criterion.status = 'ENABLED'
        """,
    ):
        t = r.ad_group_criterion.keyword.text.lower()
        if "нордин" in t or "лодэ" in t or "лоде" in t:
            o = client.get_type("AdGroupCriterionOperation")
            c = o.update
            c.resource_name = r.ad_group_criterion.resource_name
            c.status = CriterionStatus.PAUSED
            o.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["status"]))
            ops.append(o)
            log(f"pause gyn competitor KW: {r.ad_group_criterion.keyword.text}")
    mutate_criteria(ops, "P1 pause gyn competitor positives")


def p1_pmax_text_strengthen():
    """Add headlines/descriptions to POOR PMax groups (Lor, Neuro). Images need manual replace."""
    log("\n=== P1 PMax text strengthen (Lor / Neuro) ===")
    targets = {
        "MRS_Lor": {
            "campaign": "MRS_Per_Max_Lor",
            "headlines": [
                "ЛОР врач в Минске",
                "Запись к отоларингологу",
                "ЛОР клиника Кравира",
                "Консультация ЛОРа — 403",
                "Лечение ЛОР заболеваний",
                "Детский и взрослый ЛОР",
                "ЛОР приём в Минске",
                "Отоларинголог Кравира",
                "Запись к ЛОРу онлайн",
                "ЛОР диагностика и лечение",
            ],
            "descriptions": [
                "Приём ЛОР-врача в медцентре Кравира. Запись по 403 или онлайн",
                "Опытные отоларингологи для взрослых и детей. Удобная запись",
                "ЛОР в Минске: консультация и лечение. Запишитесь в Кравира",
            ],
        },
        "Невролог": {
            "campaign": "MRS_Невролог_Per_Max",
            "headlines": [
                "Невролог в Минске",
                "Запись к неврологу",
                "Консультация невролога",
                "Невролог клиника Кравира",
                "Невролог — запись 403",
                "Лечение у невролога",
                "Детский невролог Минск",
                "Невролог платно в Минске",
                "Запись к неврологу онлайн",
                "Опытные неврологи Кравира",
            ],
            "descriptions": [
                "Консультация невролога в Минске. Запись онлайн или по телефону 403",
                "Невролог в медцентре Кравира. Подберём удобное время приёма",
            ],
        },
    }

    for ag_name, cfg in targets.items():
        # resolve asset group id
        ag_id = None
        for r in ga.search(
            customer_id=cid,
            query=f"""
            SELECT asset_group.id, asset_group.resource_name, asset_group.name
            FROM asset_group WHERE asset_group.name = '{ag_name}' AND asset_group.status = 'ENABLED'
            """,
        ):
            ag_id = r.asset_group.id
            ag_rn = r.asset_group.resource_name

        if not ag_id:
            log(f"asset group {ag_name} not found")
            continue

        existing_h = set()
        existing_d = set()
        h_count = d_count = 0
        for r in ga.search(
            customer_id=cid,
            query=f"""
            SELECT asset_group_asset.field_type, asset.text_asset.text, asset_group_asset.status
            FROM asset_group_asset
            WHERE asset_group.id = {ag_id} AND asset_group_asset.status != 'REMOVED'
            """,
        ):
            t = (r.asset.text_asset.text or "").strip()
            if r.asset_group_asset.field_type.name == "HEADLINE":
                h_count += 1
                existing_h.add(t.lower())
            if r.asset_group_asset.field_type.name == "DESCRIPTION":
                d_count += 1
                existing_d.add(t.lower())

        # PMax: up to 15 headlines, 5 descriptions
        to_add_h = [t for t in cfg["headlines"] if t.lower() not in existing_h][
            : max(0, 15 - h_count)
        ]
        to_add_d = [t for t in cfg["descriptions"] if t.lower() not in existing_d][
            : max(0, 5 - d_count)
        ]

        for text, field, lim in [
            *[(t, "HEADLINE", 30) for t in to_add_h],
            *[(t, "DESCRIPTION", 90) for t in to_add_d],
        ]:
            if len(text) > lim:
                log(f"skip long {field}: {text}")
                continue
            # create asset
            aop = client.get_type("AssetOperation")
            asset = aop.create
            asset.text_asset.text = text
            try:
                aresp = asset_service.mutate_assets(customer_id=cid, operations=[aop])
                asset_rn = aresp.results[0].resource_name
            except GoogleAdsException as e:
                print_err(f"create asset {text}", e)
                continue
            gap = client.get_type("AssetGroupAssetOperation")
            link = gap.create
            link.asset_group = ag_rn
            link.asset = asset_rn
            link.field_type = getattr(AssetFieldType, field)
            try:
                asset_group_asset_service.mutate_asset_group_assets(
                    customer_id=cid, operations=[gap]
                )
                log(f"{ag_name} +{field}: {text}")
            except GoogleAdsException as e:
                print_err(f"link {ag_name} {text}", e)

    log("P1 PMax NOTE: DISAPPROVED images still need clinic square/landscape replacements in UI")


def p1_gyn_video_pause_disapproved():
    log("\n=== P1 Gyn Video disapproved ad ===")
    # already paused disapproved; ensure ENABLED limited stays; budget cut in P2
    for r in ga.search(
        customer_id=cid,
        query="""
        SELECT ad_group_ad.resource_name, ad_group_ad.ad.id, ad_group_ad.status,
          ad_group_ad.policy_summary.approval_status
        FROM ad_group_ad
        WHERE campaign.id = 23023557776 AND ad_group_ad.status != 'REMOVED'
        """,
    ):
        log(
            f"ad {r.ad_group_ad.ad.id} {r.ad_group_ad.status.name} {r.ad_group_ad.policy_summary.approval_status.name}"
        )


# ---------- P2 budgets ----------
def p2_reallocate_budgets():
    log("\n=== P2 budget reallocation (total constant) ===")
    # Gyn Video 10 -> 5; Search 130 -> 135
    changes = [
        (BUDGET_GYN_VIDEO, 5_000_000, "Gyn Video $10→$5"),
        (BUDGET_SEARCH, 135_000_000, "Search $130→$135"),
    ]
    for rn, amount, label in changes:
        op = client.get_type("CampaignBudgetOperation")
        b = op.update
        b.resource_name = rn
        b.amount_micros = amount
        op.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["amount_micros"]))
        try:
            campaign_budget_service.mutate_campaign_budgets(
                customer_id=cid, operations=[op]
            )
            log(f"{label}: OK")
        except GoogleAdsException as e:
            print_err(label, e)


# ---------- P3 structure ----------
def p3_uzi_split_and_gyn_neuro():
    log("\n=== P3 Cardio/УЗИ split + Gyn dedupe + Neuro ===")
    # Create MRS УЗИ_wk
    ag_name = "MRS УЗИ_wk"
    ag_rn = None
    ag_id = None
    for r in ga.search(
        customer_id=cid,
        query=f"""
        SELECT ad_group.id, ad_group.resource_name, ad_group.name, ad_group.status
        FROM ad_group WHERE campaign.id = {CAMP_SEARCH} AND ad_group.name = '{ag_name}'
        """,
    ):
        ag_rn = r.ad_group.resource_name
        ag_id = r.ad_group.id
        if r.ad_group.status.name == "PAUSED":
            op = client.get_type("AdGroupOperation")
            ag = op.update
            ag.resource_name = ag_rn
            ag.status = AdGroupStatus.ENABLED
            op.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["status"]))
            ad_group_service.mutate_ad_groups(customer_id=cid, operations=[op])
            log("re-enabled MRS УЗИ_wk")

    if not ag_rn:
        op = client.get_type("AdGroupOperation")
        ag = op.create
        ag.name = ag_name
        ag.campaign = CAMP_SEARCH_RN
        ag.status = AdGroupStatus.ENABLED
        ag.cpc_bid_micros = 10000
        resp = ad_group_service.mutate_ad_groups(customer_id=cid, operations=[op])
        ag_rn = resp.results[0].resource_name
        ag_id = int(ag_rn.split("/")[-1])
        log(f"created {ag_name} {ag_id}")

    # Negate УЗИ from cardio
    have = set()
    for r in ga.search(
        customer_id=cid,
        query=f"""
        SELECT ad_group_criterion.keyword.text FROM ad_group_criterion
        WHERE ad_group.id = {AG_CARDIO} AND ad_group_criterion.negative = TRUE
          AND ad_group_criterion.status != 'REMOVED'
        """,
    ):
        have.add(r.ad_group_criterion.keyword.text.lower())
    ops = []
    for text in ["узи", "ультразвук", "эхокг", "эхокардиографи"]:
        if text in have:
            continue
        o = client.get_type("AdGroupCriterionOperation")
        c = o.create
        c.ad_group = f"customers/{cid}/adGroups/{AG_CARDIO}"
        c.negative = True
        c.keyword.text = text
        c.keyword.match_type = MatchType.PHRASE
        ops.append(o)
    mutate_criteria(ops, "P3 cardio УЗИ negatives")

    # Pause cardio KW that is explicit UZI combo
    ops = []
    for r in ga.search(
        customer_id=cid,
        query=f"""
        SELECT ad_group_criterion.resource_name, ad_group_criterion.keyword.text
        FROM ad_group_criterion
        WHERE ad_group.id = {AG_CARDIO} AND ad_group_criterion.negative = FALSE
          AND ad_group_criterion.status = 'ENABLED'
        """,
    ):
        t = r.ad_group_criterion.keyword.text.lower()
        if "узи" in t:
            o = client.get_type("AdGroupCriterionOperation")
            c = o.update
            c.resource_name = r.ad_group_criterion.resource_name
            c.status = CriterionStatus.PAUSED
            o.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["status"]))
            ops.append(o)
    mutate_criteria(ops, "P3 pause cardio explicit UZI kws")

    # UZI keywords
    have = set()
    for r in ga.search(
        customer_id=cid,
        query=f"""
        SELECT ad_group_criterion.keyword.text FROM ad_group_criterion
        WHERE ad_group.id = {ag_id} AND ad_group_criterion.negative = FALSE
          AND ad_group_criterion.status != 'REMOVED'
        """,
    ):
        have.add(r.ad_group_criterion.keyword.text.lower())

    uzi_kws = [
        ("узи минск", URL_UZI),
        ("узи сердца минск", URL_UZI_HEART),
        ("узи сердца", URL_UZI_HEART),
        ("узи сердца ребенку минск", "https://kravira.by/services/diagnosticheskoe-otdelenie/uzi-detey/uzi-serdtsa-detskoe/"),
        ("узи бца минск", "https://kravira.by/services/diagnosticheskoe-otdelenie/yzi/serdtse-i-sosudy/"),
        ("узи брюшной полости минск", URL_UZI),
        ("узи молочных желез минск", URL_UZI),
        ("узи вен нижних конечностей минск", URL_UZI),
        ("узи щитовидной железы минск", URL_UZI),
        ("сделать узи сердца минск", URL_UZI_HEART),
        ("узи органов малого таза", URL_UZI),
        ("эхокг минск", URL_UZI_HEART),
    ]
    ops = []
    for text, url in uzi_kws:
        if text.lower() in have:
            continue
        o = client.get_type("AdGroupCriterionOperation")
        c = o.create
        c.ad_group = ag_rn
        c.status = CriterionStatus.ENABLED
        c.keyword.text = text
        c.keyword.match_type = MatchType.BROAD
        c.final_urls.append(url)
        ops.append(o)
    mutate_criteria(ops, "P3 UZI keywords")

    # RSA for UZI if none
    has_ad = False
    for r in ga.search(
        customer_id=cid,
        query=f"""
        SELECT ad_group_ad.ad.id FROM ad_group_ad
        WHERE ad_group.id = {ag_id} AND ad_group_ad.status = 'ENABLED'
        """,
    ):
        has_ad = True
    if not has_ad:
        headlines = [
            "УЗИ в Минске",
            "УЗИ сердца в Кравира",
            "Запись на УЗИ — 403",
            "УЗИ брюшной полости",
            "УЗИ щитовидной железы",
            "УЗИ молочных желез",
            "УЗИ сосудов и вен",
            "Сделать УЗИ в Минске",
            "УЗИ детям и взрослым",
            "Диагностика УЗИ Кравира",
            "ЭхоКГ в Минске",
            "УЗИ БЦА в Минске",
            "Современное УЗИ",
            "Запись на УЗИ онлайн",
            "УЗИ платно в Минске",
        ]
        descriptions = [
            "УЗИ в медцентре Кравира. Запись онлайн или по единому номеру 403",
            "УЗИ сердца, сосудов, ОБП и других органов. Удобная запись в Минске",
            "Точная ультразвуковая диагностика. Опытные специалисты Кравира",
            "Сделайте УЗИ в Минске без очередей. Запишитесь по телефону 403",
        ]
        o = client.get_type("AdGroupAdOperation")
        aga = o.create
        aga.ad_group = ag_rn
        aga.status = AdGroupAdStatus.ENABLED
        ad = aga.ad
        ad.final_urls.append(URL_UZI)
        rsa = ad.responsive_search_ad
        rsa.path1 = "УЗИ"
        rsa.path2 = "в Минске"
        for t in headlines:
            h = client.get_type("AdTextAsset")
            h.text = t
            rsa.headlines.append(h)
        for t in descriptions:
            d = client.get_type("AdTextAsset")
            d.text = t
            rsa.descriptions.append(d)
        try:
            resp = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=cid, operations=[o]
            )
            log(f"P3 UZI RSA OK {resp.results[0].resource_name}")
        except GoogleAdsException as e:
            print_err("P3 UZI RSA", e)

    # Gyn dedupe: clinic group — neg consultation intent to konsult AG; konsult — keep
    have = set()
    for r in ga.search(
        customer_id=cid,
        query=f"""
        SELECT ad_group_criterion.keyword.text FROM ad_group_criterion
        WHERE ad_group.id = {AG_GYN} AND ad_group_criterion.negative = TRUE
          AND ad_group_criterion.status != 'REMOVED'
        """,
    ):
        have.add(r.ad_group_criterion.keyword.text.lower())
    ops = []
    for text in ["консультация", "записаться к гинекологу", "запись к гинекологу"]:
        if text in have:
            continue
        o = client.get_type("AdGroupCriterionOperation")
        c = o.create
        c.ad_group = f"customers/{cid}/adGroups/{AG_GYN}"
        c.negative = True
        c.keyword.text = text
        c.keyword.match_type = MatchType.PHRASE
        ops.append(o)
    mutate_criteria(ops, "P3 gyn clinic → leave konsult to konsult AG")

    # Therapy: pause waste УЗИ ОБП from therapy if keyword exists; add узи neg? Therapy may need uzi for gp - add only competitor already in shared. Optional: neg "узи обп" specific - skip, UZI group will compete.

    # Pause детская эндоскопия if still enabled? User didn't confirm service - check left alone.

    log("P3 done")


# ---------- P4 conversion values ----------
def p4_conversion_values():
    log("\n=== P4 conversion values / include booking ===")
    # name -> (default_value, include, primary)
    plan = {
        "GTM_click_tel": (2.0, True, True),
        "MRS_try_Aibolit": (25.0, True, True),
        "MRS_onlineBooking": (20.0, True, True),
        "GTM_clicl_zapis": (15.0, True, True),
        "MRS_headerZapisButton": (12.0, True, True),
        "Test_MRS_Call_Back_Sent": (8.0, True, True),
    }
    by_name = {}
    for r in ga.search(
        customer_id=cid,
        query="""
        SELECT conversion_action.resource_name, conversion_action.name,
          conversion_action.value_settings.default_value,
          conversion_action.primary_for_goal,
          conversion_action.include_in_conversions_metric
        FROM conversion_action WHERE conversion_action.status != 'REMOVED'
        """,
    ):
        by_name[r.conversion_action.name] = r.conversion_action.resource_name

    ops = []
    for name, (val, include, primary) in plan.items():
        rn = by_name.get(name)
        if not rn:
            log(f"missing conversion action {name}")
            continue
        op = client.get_type("ConversionActionOperation")
        ca = op.update
        ca.resource_name = rn
        ca.value_settings.default_value = val
        ca.value_settings.always_use_default_value = True
        ca.include_in_conversions_metric = include
        ca.primary_for_goal = primary
        op.update_mask.CopyFrom(
            field_mask_pb2.FieldMask(
                paths=[
                    "value_settings.default_value",
                    "value_settings.always_use_default_value",
                    "include_in_conversions_metric",
                    "primary_for_goal",
                ]
            )
        )
        ops.append(op)
        log(f"plan {name}: value={val} include={include} primary={primary}")

    if ops:
        try:
            resp = conversion_action_service.mutate_conversion_actions(
                customer_id=cid, operations=ops
            )
            log(f"P4 conversion updates OK {len(resp.results)}")
        except GoogleAdsException as e:
            print_err("P4 batch", e)
            for op in ops:
                try:
                    conversion_action_service.mutate_conversion_actions(
                        customer_id=cid, operations=[op]
                    )
                    log(f"  OK {op.update.resource_name}")
                except GoogleAdsException as e2:
                    print_err(f"  fail {op.update.resource_name}", e2)


def main():
    p1_shared_negatives()
    p1_pmax_text_strengthen()
    p1_gyn_video_pause_disapproved()
    p2_reallocate_budgets()
    p3_uzi_split_and_gyn_neuro()
    p4_conversion_values()
    log("\n=== ALL PRIORITIES APPLIED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
