#!/usr/bin/env python3
"""Phone-first $300/day plan: MRS_Phone Search + budget shifts. 2026-09-15."""
from __future__ import annotations

import sys

from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2

from scripts.google_ads_client import customer_id, load_client

cid = customer_id()
client = load_client()
ga = client.get_service("GoogleAdsService")

TEL_ACTION = f"customers/{cid}/conversionActions/6522469634"
SHARED_NEG = f"customers/{cid}/sharedSets/12181664314"
MINSK = "geoTargetConstants/1001493"
RU = "languageConstants/1031"
GOAL_NAME = "MRS_Phone_only"
CAMP_NAME = "MRS_Phone"

BUDGET_UPDATES = {
    "MRS-Google_Search": 40,
    "MRS_ФГДС_Max": 35,
    "MRS_Per_Max_Spravki": 20,
    "MRS_Per_Max_Lor": 12,
    "MRS_Невролог_Per_Max": 8,
    "MRS_Per_Max_Laser": 5,
    "MRS-Per_Max_Urolog": 16,
    "MRS-Per_Max_Gynecolog": 12,
    "MRS-Per_Max_Flebolog": 12,
    "MRS-Per_Max_Endokrinolog": 10,
    "MRS_Demand_Gen": 50,
}

AD_GROUPS = [
    {
        "name": "MRS_Phone УЗИ",
        "url": "https://kravira.by/services/diagnosticheskoe-otdelenie/yzi/",
        "keywords": [
            "узи минск",
            "сделать узи в минске",
            "запись на узи минск",
            "узи клиника минск",
        ],
        "headlines": [
            "УЗИ в Минске",
            "Запись на УЗИ онлайн",
            "УЗИ в Кравира",
            "Сделать УЗИ в Минске",
            "УЗИ брюшной полости",
            "УЗИ сердца в Кравира",
            "Современное УЗИ",
            "УЗИ детям и взрослым",
            "Диагностика УЗИ Кравира",
            "Запись на сайте",
            "УЗИ платно в Минске",
            "Точная диагностика",
            "УЗИ щитовидной железы",
            "ЭхоКГ в Минске",
            "Медцентр Кравира",
        ],
        "descriptions": [
            "УЗИ в медцентре Кравира. Запись онлайн на сайте",
            "УЗИ сердца, сосудов, ОБП и других органов. Удобная запись в Минске",
            "Точная ультразвуковая диагностика. Опытные специалисты Кравира",
            "Сделайте УЗИ в Минске. Запишитесь на сайте",
        ],
    },
    {
        "name": "MRS_Phone Эндоскопия",
        "url": "https://kravira.by/services/diagnosticheskoe-otdelenie/endoskopicheskoe-obsledovanie/",
        "keywords": [
            "фгдс минск",
            "гастроскопия минск",
            "эндоскопия минск",
            "сделать фгдс в минске",
        ],
        "headlines": [
            "Эндоскопия в Минске",
            "Гастроскопия в Минске",
            "ФГДС в Минске",
            "Запись на эндоскопию",
            "ФГДС под седацией",
            "Запись на сайте",
            "ФГДС в Кравира",
            "Диагностика ЖКТ",
            "Гастроскопия с седацией",
            "Комфортная гастроскопия",
            "Эндоскопия желудка",
            "Запись на ФГДС",
            "Современная эндоскопия",
            "Точная диагностика ЖКТ",
            "Медцентр Кравира",
        ],
        "descriptions": [
            "Эндоскопическое обследование в Минске. Точные результаты и комфорт",
            "ФГДС и гастроскопия в клинике Кравира. Запись онлайн на сайте",
            "Современное оборудование и опытные специалисты. Запишитесь сегодня",
            "Гастроскопия с седацией и без. Удобная запись в медцентр Кравира",
        ],
    },
    {
        "name": "MRS_Phone Справки",
        "url": "https://kravira.by/services/kompleksnye-programmy/ezhegodnyy-check-up-shkolniki-vydacha-spravki-v-shkolu/",
        "keywords": [
            "справка в школу минск",
            "справка 086 минск",
            "медсправка минск",
            "справка в сад минск",
        ],
        "headlines": [
            "Справка в школу в Минске",
            "Справка 086 Минск",
            "Медсправка в Минске",
            "Справка Кравира",
            "Справка в школу",
            "Запись на сайте",
            "Справка для вуза",
            "Оформление справки в школу",
            "Справки в школу Минск",
            "Медосмотр перед садом",
            "Справка в детский сад",
            "Без длинных очередей",
            "Онлайн-запись 24/7",
            "Справка в школу, Кравира",
            "Готовы к школе? Справка здесь",
        ],
        "descriptions": [
            "Получите справку о состоянии здоровья для школьного оформления в Минске",
            "Оформление школьной справки: осмотры и документы в Кравира",
            "Справки в школу: оформим медицинскую справку при поступлении",
            "Проведём обследования и выдадим справку в школу в Кравира",
        ],
    },
    {
        "name": "MRS_Phone ЛОР",
        "url": "https://kravira.by/services/-/otolaringologiya/konsultatsiya-otolaringologa/",
        "keywords": [
            "лор минск",
            "отоларинголог минск",
            "запись к лору минск",
            "лор врач минск",
        ],
        "headlines": [
            "Лор в Минске",
            "Запись к лору",
            "Отоларинголог Минск",
            "Лор Кравира",
            "Консультация Лора здесь",
            "Запись к Отоларингологу",
            "Лор в Минске запись здесь",
            "Помощь Отоларинголога в Минске",
            "Консультация врача Лора тут",
            "Лор Ухо, Горло, Нос",
            "Запись на сайте",
            "Лор - опытные специалисты",
            "Консультация Отоларинголога",
            "Деликатный подход здесь",
            "Медцентр Кравира",
        ],
        "descriptions": [
            "Получите профессиональную помощь отоларингологов в Минске",
            "Лор в Минске. Конфиденциально и деликатно помогаем решить вопрос",
            "Полный спектр лор-услуг: диагностика и консультация в Кравира",
            "Запись к лору онлайн на сайте медицинского центра Кравира",
        ],
    },
    {
        "name": "MRS_Phone Клиника",
        "url": "https://kravira.by/",
        "keywords": [
            "кравира минск",
            "медцентр кравира",
            "записаться к врачу минск",
            "частная клиника минск запись",
        ],
        "headlines": [
            "Кравира Минск",
            "Медцентр Кравира",
            "Запись к врачу в Минске",
            "Запись на сайте",
            "Частная клиника Минск",
            "Врачи Кравира",
            "Запишитесь сегодня",
            "Клиника в Минске",
            "Приём без очередей",
            "Онлайн-запись 24/7",
            "Медицинский центр",
            "Кравира – запись",
            "Врач в Минске",
            "Консультация в Кравира",
            "Запись в клинику",
        ],
        "descriptions": [
            "Медицинский центр Кравира в Минске. Запись на сайте",
            "Консультации врачей и диагностика. Удобная запись онлайн",
            "Частная клиника в Минске. Запишитесь на приём сегодня",
            "Врачи и обследования в Кравира. Откройте запись на сайте",
        ],
    },
]


def log(msg: str) -> None:
    print(msg, flush=True)


def err(label: str, ex: GoogleAdsException) -> None:
    print(f"[error] {label}")
    for e in ex.failure.errors:
        print(" ", e.message)


def one(q: str):
    rows = []
    for batch in ga.search_stream(customer_id=cid, query=q):
        rows.extend(batch.results)
    return rows


def ensure_goal() -> str:
    for r in one(
        f"""
        SELECT custom_conversion_goal.resource_name, custom_conversion_goal.name
        FROM custom_conversion_goal
        WHERE custom_conversion_goal.name = '{GOAL_NAME}'
        """
    ):
        log(f"goal exists {r.custom_conversion_goal.resource_name}")
        return r.custom_conversion_goal.resource_name
    svc = client.get_service("CustomConversionGoalService")
    op = client.get_type("CustomConversionGoalOperation")
    g = op.create
    g.name = GOAL_NAME
    g.conversion_actions.append(TEL_ACTION)
    g.status = client.enums.CustomConversionGoalStatusEnum.ENABLED
    resp = svc.mutate_custom_conversion_goals(customer_id=cid, operations=[op])
    rn = resp.results[0].resource_name
    log(f"goal created {rn}")
    return rn


def ensure_campaign() -> tuple[str, str]:
    for r in one(
        f"""
        SELECT campaign.id, campaign.resource_name, campaign.status
        FROM campaign WHERE campaign.name = '{CAMP_NAME}' AND campaign.status != 'REMOVED'
        """
    ):
        log(f"campaign exists {r.campaign.id} {r.campaign.status.name}")
        return r.campaign.resource_name, str(r.campaign.id)

    bud_svc = client.get_service("CampaignBudgetService")
    bop = client.get_type("CampaignBudgetOperation")
    b = bop.create
    b.name = "MRS_Phone $80"
    b.amount_micros = 80_000_000
    b.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    b.explicitly_shared = False
    bud_rn = bud_svc.mutate_campaign_budgets(
        customer_id=cid, operations=[bop]
    ).results[0].resource_name
    log(f"budget {bud_rn}")

    camp_svc = client.get_service("CampaignService")
    cop = client.get_type("CampaignOperation")
    c = cop.create
    c.name = CAMP_NAME
    c.status = client.enums.CampaignStatusEnum.PAUSED
    c.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
    c.campaign_budget = bud_rn
    c.maximize_conversions.target_cpa_micros = 0
    c.network_settings.target_google_search = True
    c.network_settings.target_search_network = True
    c.network_settings.target_content_network = False
    c.network_settings.target_partner_search_network = False
    c.geo_target_type_setting.positive_geo_target_type = (
        client.enums.PositiveGeoTargetTypeEnum.PRESENCE_OR_INTEREST
    )
    c.geo_target_type_setting.negative_geo_target_type = (
        client.enums.NegativeGeoTargetTypeEnum.PRESENCE
    )
    c.contains_eu_political_advertising = (
        client.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
    )
    c.ai_max_setting.enable_ai_max = True
    try:
        rn = camp_svc.mutate_campaigns(
            customer_id=cid, operations=[cop]
        ).results[0].resource_name
    except GoogleAdsException as e:
        err("create campaign", e)
        raise
    camp_id = rn.split("/")[-1]
    log(f"campaign created {camp_id}")
    return rn, camp_id


def attach_goal(camp_id: str, goal_rn: str) -> None:
    svc = client.get_service("ConversionGoalCampaignConfigService")
    op = client.get_type("ConversionGoalCampaignConfigOperation")
    cfg = op.update
    cfg.resource_name = f"customers/{cid}/conversionGoalCampaignConfigs/{camp_id}"
    cfg.goal_config_level = client.enums.GoalConfigLevelEnum.CAMPAIGN
    cfg.custom_conversion_goal = goal_rn
    op.update_mask.CopyFrom(
        field_mask_pb2.FieldMask(
            paths=["goal_config_level", "custom_conversion_goal"]
        )
    )
    try:
        svc.mutate_conversion_goal_campaign_configs(
            customer_id=cid, operations=[op]
        )
        log("conversion goal attached")
    except GoogleAdsException as e:
        err("attach goal", e)


def attach_criteria(camp_rn: str, camp_id: str) -> None:
    crit_svc = client.get_service("CampaignCriterionService")
    existing = {
        (r.campaign_criterion.type.name, r.campaign_criterion.display_name)
        for r in one(
            f"""
            SELECT campaign_criterion.type, campaign_criterion.display_name
            FROM campaign_criterion WHERE campaign.id = {camp_id}
            """
        )
    }
    ops = []

    def add(build):
        op = client.get_type("CampaignCriterionOperation")
        build(op.create)
        ops.append(op)

    if ("LOCATION", "") not in existing and not any(
        t == "LOCATION" for t, _ in existing
    ):
        def loc(c):
            c.campaign = camp_rn
            c.location.geo_target_constant = MINSK

        add(loc)

    if not any(t == "LANGUAGE" for t, _ in existing):
        def lang(c):
            c.campaign = camp_rn
            c.language.language_constant = RU

        add(lang)

    days = [
        "MONDAY",
        "TUESDAY",
        "WEDNESDAY",
        "THURSDAY",
        "FRIDAY",
        "SATURDAY",
        "SUNDAY",
    ]
    have_sched = any(t == "AD_SCHEDULE" for t, _ in existing)
    if not have_sched:
        for day in days:
            def sched(c, d=day):
                c.campaign = camp_rn
                c.ad_schedule.day_of_week = getattr(
                    client.enums.DayOfWeekEnum, d
                )
                c.ad_schedule.start_hour = 8
                c.ad_schedule.end_hour = 21
                c.ad_schedule.start_minute = client.enums.MinuteOfHourEnum.ZERO
                c.ad_schedule.end_minute = client.enums.MinuteOfHourEnum.ZERO

            add(sched)

    if ops:
        try:
            crit_svc.mutate_campaign_criteria(customer_id=cid, operations=ops)
            log(f"criteria +{len(ops)}")
        except GoogleAdsException as e:
            err("criteria", e)

    css_svc = client.get_service("CampaignSharedSetService")
    have = list(
        one(
            f"""
            SELECT campaign_shared_set.resource_name
            FROM campaign_shared_set
            WHERE campaign.id = {camp_id} AND shared_set.id = 12181664314
            """
        )
    )
    if not have:
        op = client.get_type("CampaignSharedSetOperation")
        s = op.create
        s.campaign = camp_rn
        s.shared_set = SHARED_NEG
        try:
            css_svc.mutate_campaign_shared_sets(customer_id=cid, operations=[op])
            log("shared negatives attached")
        except GoogleAdsException as e:
            err("shared set", e)


def ensure_ad_groups(camp_rn: str, camp_id: str) -> None:
    ag_svc = client.get_service("AdGroupService")
    kw_svc = client.get_service("AdGroupCriterionService")
    ad_svc = client.get_service("AdGroupAdService")
    existing = {
        r.ad_group.name: r.ad_group.resource_name
        for r in one(
            f"""
            SELECT ad_group.name, ad_group.resource_name
            FROM ad_group WHERE campaign.id = {camp_id} AND ad_group.status != 'REMOVED'
            """
        )
    }
    for spec in AD_GROUPS:
        ag_rn = existing.get(spec["name"])
        if not ag_rn:
            op = client.get_type("AdGroupOperation")
            ag = op.create
            ag.name = spec["name"]
            ag.campaign = camp_rn
            ag.status = client.enums.AdGroupStatusEnum.ENABLED
            ag.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
            ag_rn = ag_svc.mutate_ad_groups(
                customer_id=cid, operations=[op]
            ).results[0].resource_name
            log(f"ad group {spec['name']}")
        ag_id = ag_rn.split("/")[-1]
        have_kw = {
            r.ad_group_criterion.keyword.text.lower()
            for r in one(
                f"""
                SELECT ad_group_criterion.keyword.text
                FROM ad_group_criterion
                WHERE ad_group.id = {ag_id}
                  AND ad_group_criterion.type = 'KEYWORD'
                  AND ad_group_criterion.status != 'REMOVED'
                """
            )
        }
        kops = []
        for text in spec["keywords"]:
            if text.lower() in have_kw:
                continue
            o = client.get_type("AdGroupCriterionOperation")
            k = o.create
            k.ad_group = ag_rn
            k.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
            k.keyword.text = text
            k.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
            kops.append(o)
        if kops:
            try:
                kw_svc.mutate_ad_group_criteria(customer_id=cid, operations=kops)
                log(f"  keywords +{len(kops)}")
            except GoogleAdsException as e:
                err(f"keywords {spec['name']}", e)

        have_ad = list(
            one(
                f"""
                SELECT ad_group_ad.ad.id FROM ad_group_ad
                WHERE ad_group.id = {ag_id} AND ad_group_ad.status != 'REMOVED'
                """
            )
        )
        if have_ad:
            continue
        aop = client.get_type("AdGroupAdOperation")
        aga = aop.create
        aga.ad_group = ag_rn
        aga.status = client.enums.AdGroupAdStatusEnum.ENABLED
        ad = aga.ad
        ad.final_urls.append(spec["url"])
        rsa = ad.responsive_search_ad
        for h in spec["headlines"]:
            asset = client.get_type("AdTextAsset")
            asset.text = h
            rsa.headlines.append(asset)
        for d in spec["descriptions"]:
            asset = client.get_type("AdTextAsset")
            asset.text = d
            rsa.descriptions.append(asset)
        try:
            ad_svc.mutate_ad_group_ads(customer_id=cid, operations=[aop])
            log(f"  rsa ok")
        except GoogleAdsException as e:
            err(f"rsa {spec['name']}", e)


def shift_budgets() -> None:
    bud_svc = client.get_service("CampaignBudgetService")
    camp_svc = client.get_service("CampaignService")
    rows = one(
        """
        SELECT campaign.name, campaign.status, campaign.resource_name,
               campaign_budget.resource_name, campaign_budget.amount_micros
        FROM campaign
        WHERE campaign.status != 'REMOVED'
        """
    )
    by_name = {r.campaign.name: r for r in rows}
    for name, dollars in BUDGET_UPDATES.items():
        r = by_name.get(name)
        if not r:
            log(f"skip missing {name}")
            continue
        current = r.campaign_budget.amount_micros / 1e6
        if abs(current - dollars) < 0.01:
            log(f"budget {name} already ${dollars}")
            continue
        op = client.get_type("CampaignBudgetOperation")
        b = op.update
        b.resource_name = r.campaign_budget.resource_name
        b.amount_micros = int(dollars * 1_000_000)
        op.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["amount_micros"]))
        try:
            bud_svc.mutate_campaign_budgets(customer_id=cid, operations=[op])
            log(f"budget {name} ${current:.0f} → ${dollars}")
        except GoogleAdsException as e:
            err(f"budget {name}", e)

    video = by_name.get("Gynecology_Video_Conversions #2")
    if video and video.campaign.status.name != "PAUSED":
        op = client.get_type("CampaignOperation")
        c = op.update
        c.resource_name = video.campaign.resource_name
        c.status = client.enums.CampaignStatusEnum.PAUSED
        op.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["status"]))
        try:
            camp_svc.mutate_campaigns(customer_id=cid, operations=[op])
            log("paused Gynecology_Video_Conversions #2")
        except GoogleAdsException as e:
            err("pause video", e)
    else:
        log("video already paused or missing")


def enable_campaign(camp_rn: str) -> None:
    camp_svc = client.get_service("CampaignService")
    op = client.get_type("CampaignOperation")
    c = op.update
    c.resource_name = camp_rn
    c.status = client.enums.CampaignStatusEnum.ENABLED
    op.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["status"]))
    camp_svc.mutate_campaigns(customer_id=cid, operations=[op])
    log("MRS_Phone ENABLED")


def main() -> int:
    log("=== phone plan $300 ===")
    try:
        goal_rn = ensure_goal()
        camp_rn, camp_id = ensure_campaign()
        attach_goal(camp_id, goal_rn)
        attach_criteria(camp_rn, camp_id)
        ensure_ad_groups(camp_rn, camp_id)
        shift_budgets()
        enable_campaign(camp_rn)
    except GoogleAdsException as e:
        err("fatal", e)
        return 2
    log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
