#!/usr/bin/env python3
"""Generate de.html / ja.html (and re-emit index.html) from the English bundle.

Source of truth:
  - i18n/base.template.html  : pristine English rendered-page template
  - index.html               : provides the loader shell + asset manifest

Run:  python3 i18n/build.py            (writes files)
      python3 i18n/build.py --check    (dry run, report unmatched phrases)
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://zmaxjp-landing.vercel.app"
LANGS = {"en": "/", "de": "/de", "ja": "/ja"}
CHECK = "--check" in sys.argv

# ── translations: english -> {de, ja} ──────────────────────────────────
# Text nodes (matched between tag boundaries) and attribute values share
# this table; entries are applied as whole-segment replacements.
T = {
 "Custom Thermoelectric (Peltier) Coolers — Z-MAX Manufacturer | Request a Quote":
   {"de":"Kundenspezifische thermoelektrische (Peltier-)Kühler — Hersteller Z-MAX | Angebot anfordern",
    "ja":"カスタム熱電（ペルチェ）クーラー — メーカー Z-MAX｜見積依頼"},
 "THERMOELECTRIC":{"de":"THERMOELEKTRIK","ja":"熱電クーラー"},
 "Request a quote":{"de":"Angebot anfordern","ja":"見積を依頼"},
 "Peltier / thermoelectric coolers — manufacturer":
   {"de":"Peltier-/thermoelektrische Kühler — Hersteller","ja":"ペルチェ／熱電クーラー — メーカー"},
 "Custom thermoelectric coolers,":{"de":"Kundenspezifische thermoelektrische Kühler,","ja":"カスタム熱電クーラー、"},
 "direct from the manufacturer.":{"de":"direkt vom Hersteller.","ja":"メーカー直販。"},
 "We design and build Peltier modules, cooler units and OEM assemblies in our own factories — sized to your thermal load, not pulled off a distributor's shelf.":
   {"de":"Wir entwickeln und fertigen Peltier-Module, Kühleinheiten und OEM-Baugruppen in eigenen Werken — ausgelegt auf Ihre thermische Last, nicht ab Distributor-Regal.",
    "ja":"ペルチェモジュール、クーラーユニット、OEMアセンブリを自社工場で設計・製造します。流通在庫品ではなく、お客様の熱負荷に合わせて設計します。"},
 "English-speaking technical support":{"de":"Technischer Support auf Englisch","ja":"英語対応の技術サポート"},
 "Shipping to Germany &amp; Europe":{"de":"Versand nach Deutschland &amp; Europa","ja":"ドイツ・欧州へ発送"},
 "Reply within 2 business days":{"de":"Antwort innerhalb von 2 Werktagen","ja":"2営業日以内に返信"},
 "See technical range":{"de":"Technisches Programm ansehen","ja":"技術仕様を見る"},
 "Tell us what you need to cool — an engineer replies, not a bot.":
   {"de":"Sagen Sie uns, was gekühlt werden soll — ein Ingenieur antwortet, kein Bot.",
    "ja":"冷却したい対象をお知らせください — ボットではなく技術者が返信します。"},
 "Name":{"de":"Name","ja":"お名前"},
 "Please enter your name.":{"de":"Bitte geben Sie Ihren Namen ein.","ja":"お名前を入力してください。"},
 "Company":{"de":"Firma","ja":"会社名"},
 "Please enter your company.":{"de":"Bitte geben Sie Ihre Firma ein.","ja":"会社名を入力してください。"},
 "Work email":{"de":"Geschäftliche E-Mail","ja":"勤務先メール"},
 "Please enter a valid work email.":{"de":"Bitte geben Sie eine gültige geschäftliche E-Mail ein.","ja":"有効な勤務先メールを入力してください。"},
 "Phone":{"de":"Telefon","ja":"電話番号"},
 "Enter a valid phone number with country/area code.":
   {"de":"Bitte gültige Telefonnummer mit Landes-/Vorwahl eingeben.","ja":"国番号・市外局番を含む有効な電話番号を入力してください。"},
 "Application / requirement":{"de":"Anwendung / Anforderung","ja":"用途・要件"},
 "Please describe your application.":{"de":"Bitte beschreiben Sie Ihre Anwendung.","ja":"用途をご記入ください。"},
 "Estimated annual quantity":{"de":"Geschätzte Jahresmenge","ja":"年間予定数量"},
 "(optional)":{"de":"(optional)","ja":"（任意）"},
 "Select a range…":{"de":"Bereich wählen…","ja":"範囲を選択…"},
 "Prototype / samples":{"de":"Prototyp / Muster","ja":"試作／サンプル"},
 "Send RFQ":{"de":"Anfrage senden","ja":"見積依頼を送信"},
 "No obligation. We never share your details.":
   {"de":"Unverbindlich. Wir geben Ihre Daten niemals weiter.","ja":"義務は一切ありません。お客様の情報を第三者に提供することはありません。"},
 "Privacy policy / Datenschutzerklärung":{"de":"Datenschutzerklärung","ja":"プライバシーポリシー / Datenschutzerklärung"},
 "Thank you — your RFQ is in.":{"de":"Vielen Dank — Ihre Anfrage ist eingegangen.","ja":"ありがとうございます — 見積依頼を受け付けました。"},
 "An engineer will get back to you within 2 business days. For anything urgent, email":
   {"de":"Ein Ingenieur meldet sich innerhalb von 2 Werktagen. Bei dringenden Fällen schreiben Sie an",
    "ja":"技術者が2営業日以内にご連絡します。お急ぎの場合はこちらまでメールください："},
 "Since 1990":{"de":"Seit 1990","ja":"1990年創業"},
 "Thermoelectric specialist":{"de":"Spezialist für Thermoelektrik","ja":"熱電の専門メーカー"},
 "Own factories":{"de":"Eigene Werke","ja":"自社工場"},
 "Japan &amp; China":{"de":"Japan &amp; China","ja":"日本・中国"},
 "Custom &amp; OEM":{"de":"Individuell &amp; OEM","ja":"カスタム・OEM"},
 "Module to finished unit":{"de":"Vom Modul zur fertigen Einheit","ja":"モジュールから完成品まで"},
 "Pb-free options":{"de":"Pb-freie Optionen","ja":"鉛フリー対応"},
 "On selected lines":{"de":"Bei ausgewählten Serien","ja":"一部シリーズで対応"},
 "Why buy from the maker":{"de":"Warum beim Hersteller kaufen","ja":"メーカーから買う理由"},
 "You talk to the company that designs and builds the module.":
   {"de":"Sie sprechen mit dem Unternehmen, das das Modul entwickelt und fertigt.","ja":"モジュールを設計・製造する会社と直接やり取りできます。"},
 "Built to your spec":{"de":"Nach Ihren Vorgaben gefertigt","ja":"仕様に合わせて製作"},
 "Custom geometries and micro modules down to 3.2 mm, matched to your ΔT and heat load — not forced to fit a catalogue part.":
   {"de":"Kundenspezifische Geometrien und Mikromodule ab 3,2 mm, abgestimmt auf Ihr ΔT und Ihre Wärmelast — kein Zwang zum Katalogteil.",
    "ja":"3.2 mmまでのカスタム形状・マイクロモジュールを、ΔTと熱負荷に合わせて製作。カタログ品に無理に合わせる必要はありません。"},
 "Module or finished unit":{"de":"Modul oder fertige Einheit","ja":"モジュールまたは完成ユニット"},
 "From bare Peltier modules through to complete, ready-to-mount OEM cooling assemblies — one supplier across the whole stack.":
   {"de":"Von blanken Peltier-Modulen bis zu kompletten, einbaufertigen OEM-Kühlbaugruppen — ein Lieferant über die gesamte Kette.",
    "ja":"ペルチェ素子単体から、取付け可能な完成OEM冷却アセンブリまで — 全工程を一社で対応。"},
 "Volume production":{"de":"Serienproduktion","ja":"量産対応"},
 "Prototype, qualify, then scale to mass production in our own facilities — the same part, the same quality, at volume.":
   {"de":"Prototyp, Qualifizierung und Hochlauf zur Serienfertigung in eigenen Werken — dasselbe Teil, dieselbe Qualität, in Stückzahl.",
    "ja":"試作・評価から量産まで自社工場でスケール — 同じ部品・同じ品質を量産で。"},
 "Technical range":{"de":"Technisches Programm","ja":"技術ラインナップ"},
 "GL-II thermoelectric cooler series.":{"de":"Thermoelektrische Kühler der Serie GL-II.","ja":"GL-II 熱電クーラーシリーズ。"},
 "GL-II thermoelectric cooler series":{"de":"Thermoelektrische Kühler der Serie GL-II","ja":"GL-II 熱電クーラーシリーズ"},
 "Single &amp; 2-stage":{"de":"Ein- &amp; zweistufig","ja":"1段・2段"},
 "Operating temp":{"de":"Betriebstemperatur","ja":"動作温度"},
 "Heat-pumping (Qmax)":{"de":"Wärmeleistung (Qmax)","ja":"吸熱量 (Qmax)"},
 "up to ≈228 W":{"de":"bis ≈228 W","ja":"最大 ≈228 W"},
 "Module footprint":{"de":"Modulgrundfläche","ja":"モジュール外形"},
 "Configurations":{"de":"Konfigurationen","ja":"構成"},
 "1- &amp; 2-stage (high-ΔT)":{"de":"1- &amp; 2-stufig (hoch-ΔT)","ja":"1段・2段（高ΔT）"},
 "Exact Imax / Vmax / ΔTmax / Qmax per model on datasheet — request the sheet for your target.":
   {"de":"Exakte Imax / Vmax / ΔTmax / Qmax je Modell im Datenblatt — fordern Sie das Blatt für Ihr Ziel an.",
    "ja":"各モデルの正確な Imax / Vmax / ΔTmax / Qmax はデータシートに記載 — ご希望の仕様書をご請求ください。"},
 "Applications":{"de":"Anwendungen","ja":"用途"},
 "Where Z-MAX coolers go to work.":{"de":"Wo Z-MAX-Kühler zum Einsatz kommen.","ja":"Z-MAXクーラーの活躍分野。"},
 "Medical &amp; lab":{"de":"Medizin &amp; Labor","ja":"医療・ラボ"},
 "DNA analysers, incubators, reagent and sample cooling.":
   {"de":"DNA-Analysatoren, Inkubatoren, Reagenzien- und Probenkühlung.","ja":"DNA分析装置、インキュベーター、試薬・検体の冷却。"},
 "Semiconductor":{"de":"Halbleiter","ja":"半導体"},
 "Wafer and stage temperature control to ±0.1 °C.":
   {"de":"Wafer- und Stage-Temperaturregelung auf ±0,1 °C.","ja":"ウェハ・ステージの温度制御を±0.1 °Cで。"},
 "Optical":{"de":"Optik","ja":"光学"},
 "Laser-diode and CCD/sensor stabilisation.":
   {"de":"Stabilisierung von Laserdioden und CCD/Sensoren.","ja":"レーザーダイオードやCCD/センサーの安定化。"},
 "Industrial":{"de":"Industrie","ja":"産業機器"},
 "Electrical-cabinet and enclosure cooling.":
   {"de":"Kühlung von Schaltschränken und Gehäusen.","ja":"制御盤・筐体の冷却。"},
 "Food &amp; beverage":{"de":"Lebensmittel &amp; Getränke","ja":"食品・飲料"},
 "Dispensers, showcases and point-of-use chilling.":
   {"de":"Spender, Vitrinen und Kühlung am Einsatzort.","ja":"ディスペンサー、ショーケース、使用箇所での冷却。"},
 "Measurement":{"de":"Messtechnik","ja":"計測"},
 "Chromatography and gas-analysis temperature control.":
   {"de":"Temperaturregelung für Chromatographie und Gasanalyse.","ja":"クロマトグラフィーやガス分析の温度制御。"},
 "How it works":{"de":"So funktioniert es","ja":"ご依頼の流れ"},
 "From requirement to production, in four steps.":
   {"de":"Von der Anforderung zur Produktion in vier Schritten.","ja":"要件から量産まで4ステップ。"},
 "Send your requirement":{"de":"Anforderung senden","ja":"要件を送る"},
 "Heat load, temperature target, footprint and quantity — as much or as little as you have.":
   {"de":"Wärmelast, Zieltemperatur, Grundfläche und Menge — so viel oder so wenig wie vorhanden.",
    "ja":"熱負荷、目標温度、外形寸法、数量 — 分かる範囲で結構です。"},
 "We recommend or design":{"de":"Wir empfehlen oder konstruieren","ja":"提案または設計"},
 "An engineer matches a standard module or designs a custom geometry to your ΔT and load.":
   {"de":"Ein Ingenieur wählt ein Standardmodul oder konstruiert eine kundenspezifische Geometrie für Ihr ΔT und Ihre Last.",
    "ja":"技術者が標準モジュールを選定、またはΔTと負荷に合わせてカスタム形状を設計します。"},
 "Quote &amp; samples":{"de":"Angebot &amp; Muster","ja":"見積・サンプル"},
 "You receive a quotation and the datasheet, with samples where the application calls for them.":
   {"de":"Sie erhalten ein Angebot und das Datenblatt, mit Mustern, wo die Anwendung es erfordert.",
    "ja":"見積書とデータシートをお送りし、用途に応じてサンプルもご用意します。"},
 "Production":{"de":"Produktion","ja":"量産"},
 "We qualify the part and scale to volume in our own factories — repeatably and to spec.":
   {"de":"Wir qualifizieren das Teil und skalieren in eigenen Werken in Stückzahl — reproduzierbar und spezifikationsgerecht.",
    "ja":"自社工場で部品を評価し、仕様どおり再現性をもって量産へスケールします。"},
 "Get a quote for your thermoelectric cooling requirement.":
   {"de":"Fordern Sie ein Angebot für Ihre thermoelektrische Kühlaufgabe an.","ja":"熱電冷却の要件について見積をご依頼ください。"},
 "Send your thermal load and target temperature — we'll come back with a module or assembly and the ΔT you can realistically hold.":
   {"de":"Senden Sie uns Wärmelast und Zieltemperatur — wir antworten mit einem Modul oder einer Baugruppe und dem realistisch erreichbaren ΔT.",
    "ja":"熱負荷と目標温度をお送りください — モジュールまたはアセンブリと、現実的に達成できるΔTをご提案します。"},
 "Questions":{"de":"Fragen","ja":"よくある質問"},
 "Before you ask for a quote.":{"de":"Bevor Sie ein Angebot anfordern.","ja":"見積依頼の前に。"},
 "Can you ship to the EU?":{"de":"Liefern Sie in die EU?","ja":"EUへ発送できますか？"},
 "[PLACEHOLDER — confirm before launch.] Yes — we ship modules and assemblies to Germany and across Europe. Add your delivery country and target date to the RFQ and we'll confirm lead time and Incoterms.":
   {"de":"[PLATZHALTER — vor dem Launch bestätigen.] Ja — wir liefern Module und Baugruppen nach Deutschland und in ganz Europa. Geben Sie Lieferland und Wunschtermin in der Anfrage an, dann bestätigen wir Lieferzeit und Incoterms.",
    "ja":"[要確認（公開前）] はい — ドイツおよび欧州全域へモジュール・アセンブリを発送します。納品国と希望納期を見積依頼にご記入いただければ、納期とインコタームズをご確認します。"},
 "Do you offer samples?":{"de":"Bieten Sie Muster an?","ja":"サンプルは提供されますか？"},
 "[PLACEHOLDER — confirm sample policy before launch.] For most applications we can provide samples or prototype quantities ahead of a production order. Describe your target part in the RFQ and we'll advise what's available.":
   {"de":"[PLATZHALTER — Musterpolitik vor dem Launch bestätigen.] Für die meisten Anwendungen können wir vor einer Serienbestellung Muster oder Prototypmengen bereitstellen. Beschreiben Sie Ihr Zielteil in der Anfrage, dann beraten wir Sie zur Verfügbarkeit.",
    "ja":"[要確認（公開前・サンプル方針）] 多くの用途で、量産発注前にサンプルや試作数量をご提供できます。対象部品を見積依頼にご記入いただければ、提供可否をご案内します。"},
 "What's the minimum order?":{"de":"Wie hoch ist die Mindestbestellmenge?","ja":"最小発注数量は？"},
 "[PLACEHOLDER — confirm MOQ before launch.] Minimums depend on whether the part is standard or custom and on the production run. Tell us your estimated annual quantity in the RFQ and we'll quote accordingly.":
   {"de":"[PLATZHALTER — MOQ vor dem Launch bestätigen.] Mindestmengen hängen davon ab, ob das Teil Standard oder kundenspezifisch ist, und vom Produktionslauf. Nennen Sie Ihre geschätzte Jahresmenge in der Anfrage, dann kalkulieren wir entsprechend.",
    "ja":"[要確認（公開前・MOQ）] 最小数量は、標準品かカスタム品か、また生産ロットによって異なります。年間予定数量を見積依頼にご記入いただければ、それに応じてお見積りします。"},
 "Tell us what you need to cool.":{"de":"Sagen Sie uns, was gekühlt werden soll.","ja":"冷却したい対象をお知らせください。"},
 "One short form. An engineer — not a sales rep — reads every requirement and replies with a real recommendation.":
   {"de":"Ein kurzes Formular. Ein Ingenieur — kein Vertriebler — liest jede Anforderung und antwortet mit einer echten Empfehlung.",
    "ja":"短いフォームひとつ。営業担当ではなく技術者がすべての要件を読み、具体的な提案を返信します。"},
 "Manufacturer since 1990 — own factories":{"de":"Hersteller seit 1990 — eigene Werke","ja":"1990年創業のメーカー — 自社工場"},
 "No obligation, no shared details":{"de":"Unverbindlich, keine Datenweitergabe","ja":"義務なし・情報の第三者提供なし"},
 "Send your RFQ":{"de":"Anfrage senden","ja":"見積依頼を送信"},
 "Five fields. We reply within 2 business days.":
   {"de":"Fünf Felder. Wir antworten innerhalb von 2 Werktagen.","ja":"5項目のみ。2営業日以内に返信します。"},
 "Z-MAX — manufacturer of thermoelectric (Peltier) coolers, modules, cooler units and OEM assemblies since 1990, with its own factories in Japan and China.":
   {"de":"Z-MAX — Hersteller von thermoelektrischen (Peltier-)Kühlern, Modulen, Kühleinheiten und OEM-Baugruppen seit 1990, mit eigenen Werken in Japan und China.",
    "ja":"Z-MAX — 1990年以来、熱電（ペルチェ）クーラー、モジュール、クーラーユニット、OEMアセンブリを製造。日本と中国に自社工場を有します。"},
 "Contact":{"de":"Kontakt","ja":"お問い合わせ"},
 "© 2026 Z-MAX — Thermoelectric":{"de":"© 2026 Z-MAX — Thermoelektrik","ja":"© 2026 Z-MAX — 熱電"},
 "Datenschutzerklärung":{"de":"Datenschutzerklärung","ja":"プライバシーポリシー"},
}

# Attribute values (replaced as ="value")
ATTR = {
 "Z-MAX designs and builds custom Peltier modules, cooler units and OEM thermoelectric assemblies in its own factories in Japan &amp; China. Manufacturer since 1990. Request a quote.":
   {"de":"Z-MAX entwickelt und fertigt kundenspezifische Peltier-Module, Kühleinheiten und thermoelektrische OEM-Baugruppen in eigenen Werken in Japan &amp; China. Hersteller seit 1990. Angebot anfordern.",
    "ja":"Z-MAXは日本・中国の自社工場で、カスタムペルチェモジュール、クーラーユニット、OEM熱電アセンブリを設計・製造します。1990年創業。見積依頼を承ります。"},
 "Z-MAX — Thermoelectric, home":{"de":"Z-MAX — Thermoelektrik, Startseite","ja":"Z-MAX — 熱電、ホーム"},
 "e.g. cool a laser diode to 15 °C, footprint ≤ 20 × 20 mm, ~10 W load":
   {"de":"z. B. Laserdiode auf 15 °C kühlen, Grundfläche ≤ 20 × 20 mm, ~10 W Last",
    "ja":"例：レーザーダイオードを15 °Cに冷却、外形 ≤ 20 × 20 mm、負荷 ~10 W"},
 "Request a quote":{"de":"Angebot anfordern","ja":"見積を依頼"},
}

missing = []

def translate(tpl, lang):
    out = tpl
    # text nodes: match between tag boundaries, preserve surrounding whitespace
    for en, tr in T.items():
        pat = re.compile(r'(>\s*)' + re.escape(en) + r'(\s*<)')
        new, n = pat.subn(lambda m: m.group(1) + tr[lang] + m.group(2), out)
        if n == 0:
            missing.append((lang, "TEXT", en))
        out = new
    # attribute values
    for en, tr in ATTR.items():
        a = '="' + en + '"'
        if a in out:
            out = out.replace(a, '="' + tr[lang] + '"')
        else:
            missing.append((lang, "ATTR", en))
    return out

def switcher(lang):
    items = []
    for code, path in LANGS.items():
        label = {"en": "EN", "de": "DE", "ja": "日本語"}[code]
        if code == lang:
            items.append(f'<a href="{path}" hreflang="{code}" aria-current="page" style="font-weight:700;color:inherit">{label}</a>')
        else:
            items.append(f'<a href="{path}" hreflang="{code}" style="opacity:.55;color:inherit">{label}</a>')
    return ('<nav class="lang-switch" aria-label="Language" '
            'style="display:inline-flex;gap:12px;margin-right:16px;font-size:13px;align-items:center">'
            + "".join(items) + '</nav>')

def hreflang_block(active):
    links = [f'<link rel="alternate" hreflang="{c}" href="{BASE_URL}{p}">' for c, p in LANGS.items()]
    links.append(f'<link rel="alternate" hreflang="x-default" href="{BASE_URL}/">')
    links.append(f'<link rel="canonical" href="{BASE_URL}{LANGS[active]}">')
    return "\n".join(links)

def build_template(base, lang):
    t = base
    if lang != "en":
        t = translate(t, lang)
    t = t.replace('<html lang="en">', f'<html lang="{lang}">', 1)
    t = t.replace('<div class="header-cta">', '<div class="header-cta">' + switcher(lang), 1)
    n = t.count('autocomplete="off"></label></div>')
    t = t.replace('autocomplete="off"></label></div>',
                  f'autocomplete="off"></label><input type="hidden" name="locale" value="{lang}"></div>')
    if n != 2:
        missing.append((lang, "LOCALE", f"honeypot count={n}"))
    t = t.replace('</head>', hreflang_block(lang) + '\n</head>', 1)
    return t

def build_shell(prefix, suffix, lang):
    # operate on the outer loader-shell <head> (prefix holds it)
    p = prefix
    p = re.sub(r'<html(?:\s+lang="[a-z-]+")?>', f'<html lang="{lang}">', p, count=1)
    # canonical + og:url per language
    p = p.replace('href="https://zmaxjp-landing.vercel.app/"',
                  f'href="{BASE_URL}{LANGS[lang]}"')
    p = p.replace('content="https://zmaxjp-landing.vercel.app/"',
                  f'content="{BASE_URL}{LANGS[lang]}"')
    # outer title + description (English originals)
    en_title = "Custom Thermoelectric (Peltier) Coolers — Z-MAX Manufacturer | Request a Quote"
    if lang != "en":
        p = p.replace(en_title, T[en_title][lang])
        en_desc = ("Z-MAX manufactures custom thermoelectric (Peltier) coolers and assemblies "
                   "for cooling, heating, and temperature-control applications. Request a free "
                   "quote for your specifications.")
        # (outer description differs from template meta; translate loosely)
        p = p.replace(en_desc, {"de":"Z-MAX fertigt kundenspezifische thermoelektrische (Peltier-)Kühler und Baugruppen für Kühl-, Heiz- und Temperaturregelungsaufgaben. Fordern Sie ein kostenloses Angebot an.",
                                "ja":"Z-MAXは冷却・加熱・温度制御用途向けにカスタム熱電（ペルチェ）クーラーとアセンブリを製造します。仕様に応じた無料見積を承ります。"}.get(lang, en_desc))
    # inject hreflang once into outer head
    p = re.sub(r'\n?<link rel="alternate" hreflang.*?x-default[^>]*>', '', p, flags=re.S)
    if '<link rel="canonical"' in p:
        block = "\n".join([f'<link rel="alternate" hreflang="{c}" href="{BASE_URL}{pp}">' for c, pp in LANGS.items()]
                          + [f'<link rel="alternate" hreflang="x-default" href="{BASE_URL}/">'])
        p = p.replace('<link rel="canonical"', block + '\n  <link rel="canonical"', 1)
    return p, suffix

def main():
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/template">\s*)(.*?)(\s*</script>)', index, re.S)
    prefix = index[:m.start()]
    suffix = index[m.end():]
    base = (ROOT / "i18n" / "base.template.html").read_text(encoding="utf-8")

    outputs = {}
    for lang, path in LANGS.items():
        tpl = build_template(base, lang)
        pre2, suf2 = build_shell(prefix, suffix, lang)
        body = json.dumps(tpl, ensure_ascii=False).replace('</script', '<\\/script')
        full = pre2 + m.group(1) + body + m.group(3) + suf2
        fname = "index.html" if lang == "en" else f"{lang}.html"
        outputs[fname] = full

    if missing:
        print("UNMATCHED:")
        for lang, kind, s in missing:
            print(f"  [{lang}/{kind}] {s[:80]}")
        if CHECK:
            return
        print("Aborting due to unmatched phrases.")
        sys.exit(1)

    if CHECK:
        print("dry run OK — all phrases matched")
        return
    for fname, content in outputs.items():
        (ROOT / fname).write_text(content, encoding="utf-8")
        print("wrote", fname, len(content), "bytes")

if __name__ == "__main__":
    main()
