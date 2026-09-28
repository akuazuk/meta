#!/usr/bin/env python3
"""One-shot optimization for MRS Эндоскопия_wk + theme split."""
from __future__ import annotations

import sys

from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2

from scripts.google_ads_client import customer_id, load_client, login_customer_id

cid = customer_id()
login = login_customer_id()
client = load_client()

ga = client.get_service("GoogleAdsService")
campaign_service = client.get_service("CampaignService")
ad_group_service = client.get_service("AdGroupService")
ad_group_criterion_service = client.get_service("AdGroupCriterionService")
ad_group_ad_service = client.get_service("AdGroupAdService")

CAMP = 21018894876
AG_ENDO = 163444539598
CAMP_RN = f"customers/{cid}/campaigns/{CAMP}"
AG_ENDO_RN = f"customers/{cid}/adGroups/{AG_ENDO}"

URL_PROMO = "https://kravira.by/actions/spetsialnoe-predlozhenie-na-fgds-v-kravira-/"
URL_ENDO = "https://kravira.by/services/diagnosticheskoe-otdelenie/endoskopicheskoe-obsledovanie/"
URL_FGDS_SED = "https://kravira.by/services/diagnosticheskoe-otdelenie/endoskopicheskoe-obsledovanie/gastroskopiya-s-sedatsiey/"
URL_COLON_SED = "https://kravira.by/services/diagnosticheskoe-otdelenie/endoskopicheskoe-obsledovanie/kolonoskopiya-s-sedatsiey/"

MatchType = client.enums.KeywordMatchTypeEnum
AdGroupStatus = client.enums.AdGroupStatusEnum
CriterionStatus = client.enums.AdGroupCriterionStatusEnum
AdGroupAdStatus = client.enums.AdGroupAdStatusEnum


def chk(s: str, lim: int, label: str) -> str:
    if len(s) > lim:
        raise ValueError(f"{label} too long ({len(s)}>{lim}): {s}")
    return s


def print_err(label: str, e: GoogleAdsException) -> None:
    print(f"{label}: FAIL")
    for err in e.failure.errors:
        print(" ", err.error_code, err.message)


def mutate_ag_criteria(ops, label: str, one_by_one_on_fail: bool = True):
    if not ops:
        print(f"{label}: nothing")
        return []
    try:
        resp = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=cid, operations=ops
        )
        print(f"{label}: OK {len(resp.results)}")
        return list(resp.results)
    except GoogleAdsException as e:
        print_err(label, e)
        if not one_by_one_on_fail or len(ops) == 1:
            return []
        ok = []
        for i, op in enumerate(ops):
            try:
                resp = ad_group_criterion_service.mutate_ad_group_criteria(
                    customer_id=cid, operations=[op]
                )
                ok.extend(resp.results)
            except GoogleAdsException as e2:
                msg = e2.failure.errors[0].message if e2.failure.errors else str(e2)
                print(f"  skip[{i}]: {msg}")
        print(f"{label}: partial OK {len(ok)}/{len(ops)}")
        return ok


def mutate_ads(ops, label: str):
    try:
        resp = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=cid, operations=ops
        )
        print(f"{label}: OK {len(resp.results)}")
        return list(resp.results)
    except GoogleAdsException as e:
        print_err(label, e)
        return []


def make_rsa(headlines, descriptions, path1, path2, final_url):
    ad = client.get_type("Ad")
    ad.final_urls.append(final_url)
    rsa = ad.responsive_search_ad
    rsa.path1 = chk(path1, 15, "path1")
    rsa.path2 = chk(path2, 15, "path2")
    for t in headlines:
        h = client.get_type("AdTextAsset")
        h.text = chk(t, 30, "H")
        rsa.headlines.append(h)
    for t in descriptions:
        d = client.get_type("AdTextAsset")
        d.text = chk(t, 90, "D")
        rsa.descriptions.append(d)
    return ad


def kw_create(ag_rn, text, match_type, final_url=None):
    o = client.get_type("AdGroupCriterionOperation")
    c = o.create
    c.ad_group = ag_rn
    c.status = CriterionStatus.ENABLED
    c.keyword.text = text
    c.keyword.match_type = match_type
    if final_url:
        c.final_urls.append(final_url)
    return o


def kw_neg(ag_rn, text, match_type):
    o = client.get_type("AdGroupCriterionOperation")
    c = o.create
    c.ad_group = ag_rn
    c.status = CriterionStatus.ENABLED
    c.negative = True
    c.keyword.text = text
    c.keyword.match_type = match_type
    return o


def kw_pause(resource_name):
    o = client.get_type("AdGroupCriterionOperation")
    c = o.update
    c.resource_name = resource_name
    c.status = CriterionStatus.PAUSED
    o.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["status"]))
    return o


def kw_set_url(resource_name, url):
    o = client.get_type("AdGroupCriterionOperation")
    c = o.update
    c.resource_name = resource_name
    c.final_urls.append(url)
    o.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["final_urls"]))
    return o


def add_rsa(ag_rn, headlines, descriptions, path1, path2, url, label):
    o = client.get_type("AdGroupAdOperation")
    aga = o.create
    aga.ad_group = ag_rn
    aga.status = AdGroupAdStatus.ENABLED
    aga.ad.CopyFrom(make_rsa(headlines, descriptions, path1, path2, url))
    return mutate_ads([o], label)


NEGATIVES = [
    ("нордин", MatchType.PHRASE),
    ("лодэ", MatchType.PHRASE),
    ("лоде", MatchType.PHRASE),
    ("это", MatchType.PHRASE),
    ("что такое", MatchType.PHRASE),
    ("википедия", MatchType.PHRASE),
    ("вакансия", MatchType.PHRASE),
    ("вакансии", MatchType.PHRASE),
    ("работа", MatchType.PHRASE),
    ("учеба", MatchType.PHRASE),
    ("учёба", MatchType.PHRASE),
    ("курс", MatchType.PHRASE),
    ("обучение", MatchType.PHRASE),
    ("узи", MatchType.PHRASE),
    ("подготовка", MatchType.PHRASE),
    ("гастроэнтеролог", MatchType.PHRASE),
    ("гастроэнтеролога", MatchType.PHRASE),
]


def step5_disable_content():
    op = client.get_type("CampaignOperation")
    camp = op.update
    camp.resource_name = CAMP_RN
    camp.network_settings.target_content_network = False
    camp.network_settings.target_google_search = True
    camp.network_settings.target_search_network = True
    op.update_mask.CopyFrom(
        field_mask_pb2.FieldMask(
            paths=[
                "network_settings.target_content_network",
                "network_settings.target_google_search",
                "network_settings.target_search_network",
            ]
        )
    )
    try:
        campaign_service.mutate_campaigns(customer_id=cid, operations=[op])
        print("5 content network OFF: OK")
    except GoogleAdsException as e:
        print_err("5 content network", e)
        raise


def ensure_theme_ags():
    names = [
        "MRS Колоноскопия_wk",
        "MRS Капсульная эндоскопия_wk",
        "MRS Детская эндоскопия_wk",
    ]
    found = {}
    q = (
        f"SELECT ad_group.id, ad_group.name, ad_group.resource_name, ad_group.status "
        f"FROM ad_group WHERE campaign.id = {CAMP} AND ad_group.name IN ("
        + ", ".join(f"'{n}'" for n in names)
        + ")"
    )
    for r in ga.search(customer_id=cid, query=q):
        found[r.ad_group.name] = r.ad_group.resource_name
        print("existing AG", r.ad_group.name, r.ad_group.id, r.ad_group.status.name)

    create_ops = []
    for name in names:
        if name in found:
            continue
        o = client.get_type("AdGroupOperation")
        ag = o.create
        ag.name = name
        ag.campaign = CAMP_RN
        ag.status = AdGroupStatus.ENABLED
        ag.cpc_bid_micros = 10000
        create_ops.append(o)
    if create_ops:
        try:
            resp = ad_group_service.mutate_ad_groups(
                customer_id=cid, operations=create_ops
            )
            print(f"4 create AGs: OK {len(resp.results)}")
        except GoogleAdsException as e:
            print_err("4 create AGs", e)
            raise
        for r in ga.search(customer_id=cid, query=q):
            found[r.ad_group.name] = r.ad_group.resource_name
            print("AG", r.ad_group.name, r.ad_group.resource_name)
    return found


def main():
    step5_disable_content()

    mutate_ag_criteria(
        [kw_neg(AG_ENDO_RN, t, mt) for t, mt in NEGATIVES],
        "1 negatives ENDO",
    )

    new_ags = ensure_theme_ags()
    ag_colon = new_ags["MRS Колоноскопия_wk"]
    ag_cap = new_ags["MRS Капсульная эндоскопия_wk"]
    ag_child = new_ags["MRS Детская эндоскопия_wk"]

    pause_texts = {
        "колоноскопия",
        "колоноскопия кишечника",
        "колоноскопия минск",
        "колоноскопия минск цена",
        "колоноскопия под наркозом цена",
        "запись на колоноскопию минск",
        "капсульная эндоскопия",
        "капсульная эндоскопия желудка цена",
        "детская эндоскопия",
        "эндоскопическая диагностика",
        "седация фгдс",
        "эндоскоп для желудка",
        "эндоскоп гастроскопия",
        "диагностическая эндоскопия",
        "желудочно кишечная эндоскопия",
        "гастроскопия эндоскопия",
    }
    pause_ops = []
    for r in ga.search(
        customer_id=cid,
        query=f"""
        SELECT ad_group_criterion.resource_name, ad_group_criterion.keyword.text
        FROM ad_group_criterion
        WHERE ad_group.id = {AG_ENDO} AND ad_group_criterion.type = 'KEYWORD'
          AND ad_group_criterion.negative = FALSE
          AND ad_group_criterion.status = 'ENABLED'
        """,
    ):
        if r.ad_group_criterion.keyword.text.lower() in pause_texts:
            pause_ops.append(kw_pause(r.ad_group_criterion.resource_name))
    mutate_ag_criteria(pause_ops, "4 pause moved/weak in ENDO", one_by_one_on_fail=False)

    colon_kw = [
        ("колоноскопия", MatchType.BROAD, URL_COLON_SED),
        ("колоноскопия кишечника", MatchType.BROAD, URL_COLON_SED),
        ("колоноскопия минск", MatchType.BROAD, URL_COLON_SED),
        ("колоноскопия минск цена", MatchType.BROAD, URL_COLON_SED),
        ("колоноскопия под наркозом цена", MatchType.BROAD, URL_COLON_SED),
        ("запись на колоноскопию минск", MatchType.BROAD, URL_COLON_SED),
        ("колоноскопия минск", MatchType.PHRASE, URL_COLON_SED),
        ("колоноскопия минск", MatchType.EXACT, URL_COLON_SED),
        ("колоноскопия под наркозом минск", MatchType.PHRASE, URL_COLON_SED),
        ("колоноскопия под наркозом минск", MatchType.EXACT, URL_COLON_SED),
        ("колоноскопия под седацией минск", MatchType.PHRASE, URL_COLON_SED),
        ("колоноскопия под седацией", MatchType.PHRASE, URL_COLON_SED),
        ("сделать колоноскопию в минске", MatchType.PHRASE, URL_COLON_SED),
        ("колоноскопия в минске", MatchType.PHRASE, URL_COLON_SED),
    ]
    cap_kw = [
        ("капсульная эндоскопия", MatchType.BROAD, URL_ENDO),
        ("капсульная эндоскопия желудка цена", MatchType.BROAD, URL_ENDO),
        ("капсульная эндоскопия минск", MatchType.PHRASE, URL_ENDO),
    ]
    child_kw = [
        ("детская эндоскопия", MatchType.BROAD, URL_ENDO),
        ("детская эндоскопия минск", MatchType.PHRASE, URL_ENDO),
    ]
    for label, ag_rn, kws in [
        ("COLON", ag_colon, colon_kw),
        ("CAP", ag_cap, cap_kw),
        ("CHILD", ag_child, child_kw),
    ]:
        mutate_ag_criteria(
            [kw_create(ag_rn, t, mt, url) for t, mt, url in kws],
            f"4 keywords {label}",
        )

    fgds_new = [
        ("фгдс минск", MatchType.PHRASE, URL_PROMO),
        ("фгдс минск", MatchType.EXACT, URL_PROMO),
        ("гастроскопия минск", MatchType.PHRASE, URL_PROMO),
        ("гастроскопия минск", MatchType.EXACT, URL_PROMO),
        ("сделать фгдс в минске", MatchType.PHRASE, URL_PROMO),
        ("сделать фгдс в минске", MatchType.EXACT, URL_PROMO),
        ("фгдс под наркозом минск", MatchType.PHRASE, URL_FGDS_SED),
        ("фгдс под седацией минск", MatchType.PHRASE, URL_FGDS_SED),
        ("фгдс с седацией минск", MatchType.PHRASE, URL_FGDS_SED),
        ("фгдс минск цена", MatchType.PHRASE, URL_PROMO),
        ("фгдс минск цена", MatchType.EXACT, URL_PROMO),
        ("фгдс минск платно", MatchType.PHRASE, URL_PROMO),
        ("эгдс минск", MatchType.PHRASE, URL_PROMO),
        ("записаться на фгдс минск", MatchType.PHRASE, URL_PROMO),
        ("фгдс в минске", MatchType.PHRASE, URL_PROMO),
        ("фгдс в минске", MatchType.EXACT, URL_PROMO),
        ("гастроскопия под седацией", MatchType.PHRASE, URL_FGDS_SED),
        ("гастроскопия под седацией минск", MatchType.PHRASE, URL_FGDS_SED),
        ("фгдс с биопсией минск", MatchType.PHRASE, URL_PROMO),
        ("эндоскопия в минске", MatchType.PHRASE, URL_ENDO),
        ("эндоскопия минск", MatchType.PHRASE, URL_ENDO),
        ("фгдс цена", MatchType.PHRASE, URL_PROMO),
        ("фгдс", MatchType.EXACT, URL_PROMO),
        ("гастроскопия", MatchType.EXACT, URL_PROMO),
    ]
    mutate_ag_criteria(
        [kw_create(AG_ENDO_RN, t, mt, url) for t, mt, url in fgds_new],
        "2 phrase/exact FGDS",
    )

    url_by_text = {
        "фгдс": URL_PROMO,
        "фгдс минск": URL_PROMO,
        "фгдс цена": URL_PROMO,
        "фгдс минск цена": URL_PROMO,
        "фгдс под седацией": URL_FGDS_SED,
        "фгдс с седацией": URL_FGDS_SED,
        "гастроскопия под седацией": URL_FGDS_SED,
        "гастроскопия с седацией": URL_FGDS_SED,
        "гастроскопия седация": URL_FGDS_SED,
        "фгдс седация": URL_FGDS_SED,
        "седация гастроскопия": URL_FGDS_SED,
        "гастроскопия с седацией цена": URL_FGDS_SED,
        "гастроскопия под седацией цена": URL_FGDS_SED,
        "фгдс с седацией цена": URL_FGDS_SED,
        "эндоскопия желудка": URL_ENDO,
        "эндоскопия кишечника": URL_ENDO,
        "эндоскопия пищевода": URL_ENDO,
        "эндоскопическое исследование желудка": URL_ENDO,
        "эндоскопическое исследование": URL_ENDO,
        "эндоскопия пищевода и желудка": URL_ENDO,
        "эндоскопия под наркозом": URL_ENDO,
        "эндоскопия фгдс": URL_PROMO,
        "фгдс и эндоскопия": URL_PROMO,
        "фгдс эндоскопия": URL_PROMO,
        "эндоскопия цены": URL_ENDO,
        "эндоскопия пищевода цена": URL_ENDO,
        "желудок эндоскопия": URL_ENDO,
        "биопсия желудка цена": URL_ENDO,
    }
    url_ops = []
    for r in ga.search(
        customer_id=cid,
        query=f"""
        SELECT ad_group_criterion.resource_name, ad_group_criterion.keyword.text,
          ad_group_criterion.final_urls
        FROM ad_group_criterion
        WHERE ad_group.id = {AG_ENDO} AND ad_group_criterion.type = 'KEYWORD'
          AND ad_group_criterion.negative = FALSE
          AND ad_group_criterion.status = 'ENABLED'
        """,
    ):
        t = r.ad_group_criterion.keyword.text.lower()
        url = url_by_text.get(t)
        if url and not list(r.ad_group_criterion.final_urls):
            url_ops.append(kw_set_url(r.ad_group_criterion.resource_name, url))
    mutate_ag_criteria(url_ops, "6 final URLs ENDO", one_by_one_on_fail=False)

    # 3. Ads
    pause_ad = client.get_type("AdGroupAdOperation")
    pause_ad.update.resource_name = (
        f"customers/{cid}/adGroupAds/{AG_ENDO}~778896192473"
    )
    pause_ad.update.status = AdGroupAdStatus.PAUSED
    pause_ad.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["status"]))
    mutate_ads([pause_ad], "3 pause old promo RSA")

    promo_h = [
        "ФГДС всего за 86 рублей",
        "Гастроскопия по цене 86 руб",
        "Записывайтесь на ФГДС за 86 р",
        "Гастроскопия всего за 86 руб",
        "Цена дня: ФГДС 86 руб",
        "Лёгкая запись - ФГДС за 86 руб",
        "Днём дешевле: ФГДС 86 руб",
        "Проверка желудка за 86 руб",
        "ФГДС под седацией",
        "ФГДС с биопсией",
        "Гастроскопия в Минске",
        "ФГДС в Минске",
        "Запись на ФГДС — 403",
        "ФГДС после 15:00 выгоднее",
        "Хотите пройти ФГДС выгодно?",
    ]
    promo_d = [
        "Проверьте желудок без лишних затрат: ФГДС за 86 руб. по будням",
        "Дневная выгода ФГДС за 86 руб. с 15:00. Запись по телефону 403",
        "Забота о себе без переплат: ФГДС 86 руб. после 15:00 в Кравира",
        "Быстрая запись, современное оборудование. ФГДС за 86 руб. днём",
    ]
    service_h = [
        "Эндоскопия в Минске",
        "Эндоскопическое обследование",
        "Гастроскопия в Минске",
        "ФГДС под седацией",
        "Эндоскопия желудка",
        "Запись на эндоскопию",
        "Эндоскопия цена в Минске",
        "ФГДС с биопсией",
        "Диагностика ЖКТ в Кравира",
        "Комфортная гастроскопия",
        "Эндоскопия кишечника",
        "Современная эндоскопия",
        "Запись по телефону 403",
        "Гастроскопия с седацией",
        "Точная диагностика ЖКТ",
    ]
    service_d = [
        "Эндоскопическое обследование в Минске. Точные результаты и комфорт",
        "ФГДС и гастроскопия в клинике Кравира. Запись онлайн или по 403",
        "Современное оборудование и опытные специалисты. Запишитесь сегодня",
        "Гастроскопия с седацией и без. Удобная запись в медцентр Кравира",
    ]
    colon_h = [
        "Колоноскопия в Минске",
        "Колоноскопия с седацией",
        "Колоноскопия под наркозом",
        "Запись на колоноскопию",
        "Колоноскопия цена Минск",
        "Колоноскопия кишечника",
        "Комфортная колоноскопия",
        "Диагностика кишечника",
        "Запись по телефону 403",
        "Колоноскопия в Кравира",
        "Сделать колоноскопию",
        "Колоноскопия без седации",
        "Точная диагностика кишки",
        "Колоноскопия платно Минск",
        "Опытные эндоскописты",
    ]
    colon_d = [
        "Колоноскопия с седацией и без в Минске. Запись в клинику Кравира",
        "Современная диагностика кишечника. Комфорт и точный результат",
        "Запишитесь на колоноскопию онлайн или по единому номеру 403",
        "Колоноскопия в Кравира: опытные врачи и современное оборудование",
    ]
    cap_h = [
        "Капсульная эндоскопия",
        "Эндоскопия капсулой",
        "Диагностика ЖКТ капсулой",
        "Капсульная эндоскопия Минск",
        "Запись на эндоскопию",
        "Обследование кишечника",
        "Эндоскопия в Кравира",
        "Запись по телефону 403",
        "Современная диагностика",
        "Капсула для ЖКТ",
        "Эндоскопия без зонда",
        "Точная диагностика ЖКТ",
        "Эндоскопия в Минске",
        "Запись в медцентр Кравира",
        "Диагностика ЖКТ в Кравира",
    ]
    cap_d = [
        "Капсульная эндоскопия в медцентре Кравира. Запись по номеру 403",
        "Современная диагностика ЖКТ. Уточните детали и запишитесь онлайн",
        "Эндоскопическое обследование в Минске. Комфорт и точный результат",
        "Запишитесь на обследование в Кравира онлайн или по телефону 403",
    ]
    child_h = [
        "Детская эндоскопия",
        "Эндоскопия для детей",
        "Детская эндоскопия Минск",
        "Запись на эндоскопию",
        "Диагностика ЖКТ детям",
        "Эндоскопия в Кравира",
        "Запись по телефону 403",
        "Комфортная диагностика",
        "Детям — бережный подход",
        "Гастроскопия для детей",
        "Эндоскопия желудка детям",
        "Современная эндоскопия",
        "Эндоскопия в Минске",
        "Запись в медцентр Кравира",
        "Бережная диагностика детям",
    ]
    child_d = [
        "Детская эндоскопия в клинике Кравира. Бережный подход и опыт врачей",
        "Запишитесь на обследование ребёнка онлайн или по телефону 403",
        "Эндоскопическая диагностика для детей в Минске. Комфортные условия",
        "Современное оборудование и опытные специалисты. Запись по 403",
    ]

    add_rsa(AG_ENDO_RN, promo_h, promo_d, "Гастроскопия", "акция", URL_PROMO, "3 promo RSA clean")
    add_rsa(AG_ENDO_RN, service_h, service_d, "эндоскопия", "в Минске", URL_ENDO, "3 service RSA")
    add_rsa(ag_colon, colon_h, colon_d, "колоноскопия", "в Минске", URL_COLON_SED, "4 colon RSA")
    add_rsa(ag_cap, cap_h, cap_d, "капсульная", "эндоскопия", URL_ENDO, "4 capsule RSA")
    add_rsa(ag_child, child_h, child_d, "детская", "эндоскопия", URL_ENDO, "4 child RSA")

    for ag_rn, label in [
        (ag_colon, "COLON"),
        (ag_cap, "CAP"),
        (ag_child, "CHILD"),
    ]:
        mutate_ag_criteria(
            [kw_neg(ag_rn, t, mt) for t, mt in NEGATIVES],
            f"1 negatives {label}",
        )

    print("\n=== DONE ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
