"""Fix live Google Ads policy issues: phones, guarantees, clickbait, misleading video."""
from __future__ import annotations

import re

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from scripts.google_ads_client import customer_id, load_client, login_customer_id

CID = customer_id()
LOGIN = login_customer_id()


def client() -> GoogleAdsClient:
    return load_client()


def clean_text(s: str, maxlen: int) -> str:
    t = s
    repl = [
        (r"Звоните 403", "Запись на сайте"),
        (r"Запишитесь удобно\.", "Запишитесь на сайте."),
        (r"Запись по телефону 403", "Запись на сайте"),
        (r"Запись на УЗИ — 403", "Запись на УЗИ онлайн"),
        (r"Гастроэнтеролог — запись 403", "Гастроэнтеролог Кравира"),
        (r"Запишитесь онлайн или по 403", "Запишитесь онлайн на сайте"),
        (r"Запись по телефону 403", "Запись на сайте"),
        (r"Консультация ЛОРа — 403", "Консультация ЛОРа Минск"),
        (r"Невролог — запись 403", "Невролог, запись онлайн"),
        (r"онлайн или по телефону 403", "онлайн на сайте"),
        (r"онлайн или по единому номеру 403", "онлайн на сайте"),
        (r"онлайн или по телефону здесь", "онлайн на сайте"),
        (r"на сайте или по телефону здесь", "на сайте клиники"),
        (r"на сайте или по номеру телефона", "на сайте клиники"),
        (r"онлайн или по телефону 403", "онлайн на сайте"),
        (r"Запись онлайн или по 403", "Запись онлайн на сайте"),
        (r"Запись по 403 или онлайн", "Запись онлайн на сайте"),
        (r"или по телефону 403\.?", " или на сайте"),
        (r"или по телефону 403", " или на сайте"),
        (r"по единому номеру 403", "на сайте"),
        (r"по телефону 403\.?", "на сайте"),
        (r"по телефону здесь", "на сайте"),
        (r"по номеру телефона", "на сайте"),
        (r"или 403\.", " на сайте."),
        (r"или по 403", "или на сайте"),
        (r"Запись по 403", "Запись на сайте"),
        (r"по 403", "на сайте"),
        (r"— 403", ""),
        (r"– 403", ""),
        (r"\b403\b", ""),
        (r"Справка в школу без хлопот", "Справка в школу в Минске"),
        (r"Справка в школу за 1 день тут", "Справка в школу, Кравира"),
        (r"Справка в школу за один день", "Оформление справки в школу"),
        (r"Справка в школу за 1 день", "Справка для школы в Минске"),
        (r"Школьная справка за 1 день тут", "Школьная справка в Минске"),
        (r"Школьная справка за 1 день", "Школьная справка в Минске"),
        (r"Справка школьника за 1 день по цене от 128,76 руб\. Без очередей и стресса",
         "Медосмотр для школы: педиатр и специалисты в Кравира"),
        (r"Школьная справка за 1 день от 128,76 руб\. Педиатр, офтальмолог, слух и зрение",
         "Медосмотр для школы: педиатр, зрение и слух в Кравира"),
        (r"Школьная справка за 1 день: педиатр, офтальмолог, проверка слуха и зрения",
         "Медосмотр для школы: педиатр, зрение и слух в Минске"),
        (r"Справка в Детский сад - 1 день", "Справка в детский сад"),
        (r"Справка: ребенок будет здоров", "Медосмотр перед садом"),
        (r"Справка Детский сад быстро тут", "Справка в детский сад Минск"),
        (r"Медсправка быстро", "Медсправка в Минске"),
        (r"Справка в техникум за 1 день", "Справка в техникум"),
        (r"Справка студенту – быстро", "Справка абитуриенту"),
        (r"без лишних хлопот", "в Минске"),
        (r"без хлопот", "в Минске"),
        (r"за один день здесь", "в Минске"),
        (r"за один день", ""),
        (r"за 1 день", ""),
        (r"Школьная справка за день", "Школьная справка Минск"),
        (r"Быстрый медосмотр для школы без очередей\. Удобная запись и готовая справка",
         "Медосмотр для школы: запись онлайн и справка в Кравира"),
        (r"Быстрый медосмотр для школы", "Медосмотр для школы Минск"),
        (r"Подготовьте ребенка к школе за 1 визит\. Осмотр педиатра и офтальмолога",
         "Медосмотр перед школой: педиатр и офтальмолог в Кравира"),
        (r"за 1 визит", "в Минске"),
        (r"Обеспечьте спокойствие для себя и безопасное начало учебного года для вашего ребенка",
         "Оформление школьной справки: осмотры и документы в Кравира"),
        (r"Нужна справка для приёмной комиссии\? Платно, быстро и без нервов",
         "Справка для приёмной комиссии: осмотры и документы в Кравира"),
        (r"Оформим справку в вуз", "Медосмотр абитуриента"),
        (r"Готовим справки для вуза", "Осмотры для поступления"),
        (r"Медкомиссия без очередей", "Медкомиссия в Минске"),
        (r"Печати, анализы, осмотры всё тут", "анализы и осмотры в Кравира"),
        (r"Справки для будущих студентов здесь", "Медосмотр для поступления в Кравира"),
        (r"Все специалисты в одном месте\. Без очередей",
         "Все специалисты в одном медцентре Кравира"),
        (r"Без очередей", "в Минске"),
        (r"быстро и без нервов", "в клинике Кравира"),
        (r"без нервов", "в Минске"),
        (r"Слабая эректильная дисфункция", "Мужское здоровье в Минске"),
        (r"Помощь с эректильной функцией", "Консультация андролога"),
        (r"Помощь с потенцией у мужчин", "Приём уролога в Минске"),
        (r"Уролог - Проблемы с эрекцией", "Уролог, мужское здоровье"),
        (r"Операции без шрамов", "Лазерная хирургия Минск"),
        (r"Восстановите здоровье мочеполовой системы",
         "Консультация уролога в клинике Кравира"),
        (r"ФГДС всего за 86 рублей", "ФГДС в Минске, запись"),
        (r"Безопасные и эффективные операции\. Быстрое восстановление\.",
         "Консультация лазерного хирурга в клинике Кравира."),
        (r"Высокая точность и минимальный риск\. Запишитесь сейчас",
         "Консультация лазерного хирурга. Запись на сайте"),
    ]
    for pat, sub in repl:
        t = re.sub(pat, sub, t, flags=re.I)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\s+,", ",", t)
    t = re.sub(r"\s+\.", ".", t)
    t = t.replace("..", ".").strip(" -—,")
    t = re.sub(r"в Минске в Минске", "в Минске", t)
    t = t.strip()
    if len(t) > maxlen:
        t = t[:maxlen].rsplit(" ", 1)[0].rstrip(" -,.")
    return t


def uniq_fit(items: list[str], maxlen: int, min_n: int) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    extras = [
        "Запись на сайте",
        "Клиника Кравира Минск",
        "Приём в медцентре Кравира",
        "Консультация в Минске",
        "Опытные врачи Кравира",
        "Удобная запись онлайн",
        "Медицинский центр Кравира",
        "Запишитесь на приём",
    ]
    for s in items + extras:
        c = clean_text(s, maxlen)
        if not c or c.lower() in seen:
            continue
        if len(c) < 3:
            continue
        seen.add(c.lower())
        out.append(c)
        if len(out) >= 15:
            break
    if len(out) < min_n:
        raise RuntimeError(f"not enough unique assets: {out}")
    return out


def main() -> None:
    gc = client()
    ga = gc.get_service("GoogleAdsService")

    def q(sql: str):
        rows = []
        for batch in ga.search_stream(customer_id=CID, query=sql):
            rows.extend(batch.results)
        return rows

    ad_ops = []
    pause_aga = []
    pause_ad = []
    pmax_replace = []  # (aga_rn, asset_group_rn, field_type, new_text)

    # RSA
    for r in q(
        """
        SELECT campaign.name, ad_group.name, ad_group_ad.resource_name,
          ad_group_ad.ad.resource_name, ad_group_ad.ad.id, ad_group_ad.ad.type,
          ad_group_ad.ad.responsive_search_ad.headlines,
          ad_group_ad.ad.responsive_search_ad.descriptions
        FROM ad_group_ad
        WHERE campaign.status="ENABLED" AND ad_group.status="ENABLED"
          AND ad_group_ad.status="ENABLED"
          AND ad_group_ad.ad.type="RESPONSIVE_SEARCH_AD"
        """
    ):
        old_h = [h.text for h in r.ad_group_ad.ad.responsive_search_ad.headlines]
        old_d = [d.text for d in r.ad_group_ad.ad.responsive_search_ad.descriptions]
        new_h = uniq_fit(old_h, 30, 3)[:15]
        new_d = uniq_fit(old_d, 90, 2)[:4]
        if new_h == old_h and new_d == old_d:
            continue
        print(f"RSA {r.campaign.name} / {r.ad_group.name} {r.ad_group_ad.ad.id}")
        for a, b in zip(old_h, new_h):
            if a != b:
                print(f"  H {a!r} -> {b!r}")
        for a, b in zip(old_d, new_d):
            if a != b:
                print(f"  D {a!r} -> {b!r}")
        op = gc.get_type("AdOperation")
        op.update.resource_name = r.ad_group_ad.ad.resource_name
        for t in new_h:
            asset = gc.get_type("AdTextAsset")
            asset.text = t
            op.update.responsive_search_ad.headlines.append(asset)
        for t in new_d:
            asset = gc.get_type("AdTextAsset")
            asset.text = t
            op.update.responsive_search_ad.descriptions.append(asset)
        op.update_mask.paths.extend(
            ["responsive_search_ad.headlines", "responsive_search_ad.descriptions"]
        )
        ad_ops.append(op)

    # Pause misleading gynecology video
    for r in q(
        """
        SELECT ad_group_ad.resource_name, campaign.name, ad_group.name, ad_group_ad.ad.id
        FROM ad_group_ad
        WHERE ad_group_ad.resource_name = "customers/7132108539/adGroupAds/191129016888~774348676493"
        """
    ):
        op = gc.get_type("AdGroupAdOperation")
        op.update.resource_name = r.ad_group_ad.resource_name
        op.update.status = gc.enums.AdGroupAdStatusEnum.PAUSED
        op.update_mask.paths.append("status")
        pause_ad.append(op)
        print("PAUSE video", r.campaign.name, r.ad_group.name, r.ad_group_ad.ad.id)

    # PMax texts + bad videos
    for r in q(
        """
        SELECT campaign.name, asset_group.resource_name,
          asset_group_asset.resource_name, asset_group_asset.field_type,
          asset.resource_name, asset.id, asset.type, asset.text_asset.text,
          asset_group_asset.policy_summary.policy_topic_entries
        FROM asset_group_asset
        WHERE campaign.status="ENABLED" AND asset_group_asset.status="ENABLED"
        """
    ):
        topics = [e.topic for e in r.asset_group_asset.policy_summary.policy_topic_entries]
        if r.asset.type.name == "YOUTUBE_VIDEO" and "DESTINATION_NOT_ACCESSIBLE" in topics:
            op = gc.get_type("AssetGroupAssetOperation")
            op.update.resource_name = r.asset_group_asset.resource_name
            op.update.status = gc.enums.AssetLinkStatusEnum.PAUSED
            op.update_mask.paths.append("status")
            pause_aga.append(op)
            print("PAUSE yt", r.campaign.name, r.asset.id)
            continue
        if r.asset.type.name != "TEXT":
            continue
        txt = r.asset.text_asset.text or ""
        field = r.asset_group_asset.field_type.name
        maxlen = 30 if field == "HEADLINE" else 90
        new = clean_text(txt, maxlen)
        if new == txt or not new:
            continue
        print(f"ASSET {r.campaign.name} {field} {r.asset.id}: {txt!r} -> {new!r}")
        pmax_replace.append(
            (
                r.asset_group_asset.resource_name,
                r.asset_group.resource_name,
                r.asset_group_asset.field_type,
                new,
            )
        )

    def mutate(label, fn, fatal: bool = True):
        try:
            fn()
            print(label, "ok")
            return True
        except GoogleAdsException as e:
            print("ERR", label)
            for err in e.failure.errors:
                print(" ", err.message)
                if err.location:
                    for f in err.location.field_path_elements:
                        print("   ", f.field_name, getattr(f, "index", None))
            if fatal:
                raise
            return False

    if ad_ops:
        mutate(
            f"ads updated {len(ad_ops)}",
            lambda: gc.get_service("AdService").mutate_ads(
                customer_id=CID, operations=ad_ops
            ),
        )
    else:
        print("ads: nothing to update")

    if pause_ad:
        mutate(
            f"ads paused {len(pause_ad)}",
            lambda: gc.get_service("AdGroupAdService").mutate_ad_group_ads(
                customer_id=CID, operations=pause_ad
            ),
        )

    for i, op in enumerate(pause_aga):
        mutate(
            f"pmax video pause {i+1}/{len(pause_aga)} {op.update.resource_name}",
            lambda op=op: gc.get_service("AssetGroupAssetService").mutate_asset_group_assets(
                customer_id=CID, operations=[op]
            ),
            fatal=False,
        )

    if pmax_replace:
        seen_text: dict[str, str] = {}
        create_ops = []
        create_keys = []
        for _aga, _ag, _ft, new in pmax_replace:
            if new in seen_text:
                continue
            op = gc.get_type("AssetOperation")
            op.create.text_asset.text = new
            create_ops.append(op)
            create_keys.append(new)
            seen_text[new] = ""
        resp = gc.get_service("AssetService").mutate_assets(
            customer_id=CID, operations=create_ops
        )
        for key, res in zip(create_keys, resp.results):
            seen_text[key] = res.resource_name
        print("text assets created", len(create_ops))

        aga_svc = gc.get_service("AssetGroupAssetService")
        for i, (aga_rn, ag_rn, field_type, new) in enumerate(pmax_replace, 1):
            remove_op = gc.get_type("AssetGroupAssetOperation")
            remove_op.remove = aga_rn
            add_op = gc.get_type("AssetGroupAssetOperation")
            add_op.create.asset_group = ag_rn
            add_op.create.asset = seen_text[new]
            add_op.create.field_type = field_type
            mutate(
                f"pmax swap {i}/{len(pmax_replace)} {new!r}",
                lambda remove_op=remove_op, add_op=add_op: aga_svc.mutate_asset_group_assets(
                    customer_id=CID, operations=[remove_op, add_op]
                ),
                fatal=False,
            )


if __name__ == "__main__":
    main()
