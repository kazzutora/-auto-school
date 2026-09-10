# OSTRYCHARZ.md — перенос движка на вторую автошколу

Второй клиент: **OSK Ostrycharz**, Wieluń, `oskostrycharz.pl`.

Работаем на том же движке, что и OSK Nawrocki. Этот файл — данные их сайта, разбор отличий и промпты на перенос.

Читать вместе с `tech.md`, `FRONTEND.md`, `BLOCKS.md`.

---
---

# ЧАСТЬ A — ДАННЫЕ ИХ САЙТА

Собрано 9 сентября 2026 с `https://www.oskostrycharz.pl/`. Тексты приведены дословно, по-польски, готовы к переносу в сид.

## A.1 Реквизиты

```
OSK Ostrycharz — Ośrodek Szkolenia Kierowców
ul. Asnyka 7, 98-300 Wieluń
tel. +48 691 570 489
oskostrycharz@poczta.onet.pl
Facebook:  https://pl-pl.facebook.com/osrodekostrycharz/
YouTube:   https://www.youtube.com/channel/UCbXki-U-CJjcQ36tZ5GZ4lw
```

NIP на сайте не указан — запросить у владельца.

## A.2 О фирме — дословно

```
Nasza szkoła jest firmą z dużym doświadczeniem w zakresie szkolenia przyszłych
kierowców kat. B. Pracujący u nas instruktorzy posiadają wiedzę i kwalifikacje
na wysokim poziomie, dzięki doświadczeniu zdobytemu przez lata praktyki.
Możemy pochwalić się jedną z najwyższych zdawalności w województwie Łódzkim.
Posiadamy samochody z bogatym wyposażeniem - Klimatyzowane!
Gorąco pozdrawiamy - Kierownictwo Szkoły.
```

## A.3 Цены — дословно

| Позиция | Цена |
|---|---|
| Kurs | 3700 zł |
| Kurs przyspieszony (2 tygodnie) | 4300 zł |
| Skrzynia automatyczna | 4300 zł |
| Godziny doszkalające — manual | 160 zł/h |
| Godziny doszkalające — manual, dla kursantów | 140 zł/h |
| Godziny doszkalające — automat | 140 zł/h |
| Badanie lekarskie | 200 zł |
| Egzamin | 230 zł |
| Dowóz na egzamin | GRATIS |

Это редкость: школа публикует цены. У Навроцкого их не было вовсе. Значит блок `<c-price-row>` наполняется реальными числами с первого дня.

## A.4 Записи и документы — дословно

```
ZAPISY: po wcześniejszym ustaleniu telefonicznym 691 570 489

DOKUMENTY:
- orzeczenie lekarskie
- fotografia 3,5 x 4,5 cm
- dowód osobisty / paszport
- zaświadczenie o zameldowaniu (17 zł)
- zgoda rodziców (osoby niepełnoletnie)
```

## A.5 Статистика сдачи — дословно

```
92 Kursantów:
  za 1 razem  68  (76%)
  za 2 razem  16  (18%)
  za 3 razem   3   (3%)
  za 4 razem   3   (3%)

110 Opinii:
  Bardzo dobry  103  (96%)
  Dobry           2   (2%)
  Neutralny       1   (1%)
  Bardzo słaby    1   (1%)
```

Плюс изображения статистики по годам: `obrazy/galeria/statystyka/2019.jpg`, `2020.jpg`, `2021.jpg`.

**Это их главный актив.** 76% сдачи с первого раза и 96% отличных отзывов — самый сильный аргумент, какой может быть у автошколы. Сейчас он лежит текстом в середине одностраничника без разметки, поэтому в поиске звёзд рейтинга нет.

## A.6 Файлы для скачивания

| Название | URL |
|---|---|
| Regulamin | `/pliki/Regulamin%20-%20OSK%20Ostrycharz.pdf` |
| Umowa z kursantem | `/pliki/umowa_z_kursantem_OSK_Ostrycharz.pdf` |
| Oświadczenie dot. stanu zdrowia | `/pliki/oswiadczenie_dot_stanu_zdrowia.pdf` |
| Wzór — opłata za egzamin | `/pliki/wzor_oplata_za_egzamin.pdf` |
| Zgoda rodziców — niepełnoletni | `/pliki/zgoda_rodzicow_niepelnoletni.pdf` |

## A.7 Медиа

- видео на YouTube: `https://www.youtube.com/watch?v=abeQhB0RfV4`
- фото занятий по первой помощи: `obrazy/galeria/pierwsza_pomoc1.jpg`, `pierwsza_pomoc2.jpg`
- фон главной: `obrazy/main_bg.jpg`, мобильный `main_bg_mobile.jpg`
- логотип: `obrazy/mcqueen.png`

## A.8 Внешние ссылки, которые у них есть

- `https://www.zdamyto.com/` — тесты
- `https://info-car.pl/infocar/prawo-jazdy/sprawdz-status.html` — статус PKK

---

# ЧАСТЬ B — ЧТО НЕ ТАК С ИХ САЙТОМ

Факты, без оценок. Годятся и для письма, и для ТЗ.

1. **Одностраничник.** Всё содержимое на одной странице, навигация якорями. В Google индексируется одна страница, поэтому под запросы «cennik prawa jazdy Wieluń», «kurs przyspieszony Wieluń», «zapisy prawo jazdy Wieluń» школа не показывается отдельными результатами.

2. **Нельзя дать ссылку.** Нет отдельных URL у прайса, документов, статистики. Клиенту нельзя прислать ссылку на цену — только «открой сайт и промотай».

3. **Копирайт 2018–2020.** Первое, что видит внимательный человек в подвале. Читается как «сайт заброшен».

4. **Запись через встроенную Google-форму.** Данные кандидатов уходят в чужой сервис, уведомления не настроены, информации RODO нет. Для персональных данных учеников это слабое место.

5. **Статистика не размечена.** 76% сдачи и 96% отзывов есть текстом, но нет разметки `Review` и `AggregateRating`, поэтому в выдаче Google нет звёзд. Лучший аргумент школы не работает там, где принимается решение.

6. **Нет мобильной версии как таковой** — есть отдельная фоновая картинка под мобильный, но макет один. Проверить отдельно.

7. **Тяжёлые фоны.** `main_bg.jpg` во весь экран без WebP и без адаптивных размеров.

8. **Нет админки.** Цены, статистику и файлы меняет только тот, кто делал сайт.

9. **Нет русской и украинской версий.** В Велюне это тот же недообслуженный сегмент, что и у Навроцкого.

---

# ЧАСТЬ C — ЧТО МЕНЯЕТСЯ В ДВИЖКЕ

## C.1 Главное отличие

Навроцкий — пятнадцать курсов, профессиональные водители, ADR, психотесты, погрузчики.
Ostrycharz — **только категория B**, но с реальными ценами, статистикой сдачи, документами и видео.

Движок это переживает без переделки: правило «нет данных — секция не рендерится» уже в контракте. Модели `Course(kind=professional)`, `Certificate`, `Instructor` просто остаются пустыми.

**Что менять не надо:** схему `Course`, `CourseIntake`, `PriceItem`, `Lead`, `GalleryImage`, `Testimonial`, `Faq`, `UsefulLink`, `SiteSettings`, `OpeningHours`, `Page`.

## C.2 Чего в схеме не хватает

Три вещи, которых у Навроцкого не было. Это `CONTRACT GAP` → ядро **v5**, режим LEAD.

```python
class PassRate(models.Model):
    """Статистика сдачи по годам. Главный актив школы."""
    year          = PositiveSmallIntegerField(unique=True, db_index=True)
    students      = PositiveSmallIntegerField()
    passed_1st    = PositiveSmallIntegerField()
    passed_2nd    = PositiveSmallIntegerField(default=0)
    passed_3rd    = PositiveSmallIntegerField(default=0)
    passed_4th    = PositiveSmallIntegerField(default=0)
    note          = CharField(max_length=200, blank=True)   [tr]
    is_published  = BooleanField(default=True)
    class Meta: ordering = ("-year",)
    # проценты считаются в services.py, в БД не хранятся

class DownloadFile(models.Model):
    """Документы для скачивания: regulamin, umowa, oświadczenia."""
    title        = CharField(max_length=200)              [tr]
    description  = CharField(max_length=300, blank=True)  [tr]
    file         = FileField(upload_to="documents/")
    size_bytes   = PositiveIntegerField(null=True, blank=True)  # заполняется при сохранении
    order        = PositiveSmallIntegerField(default=100)
    is_published = BooleanField(default=True)
    class Meta: ordering = ("order", "id")

# плюс поле в SiteSettings:
youtube_video_url = URLField(blank=True)   # промо-ролик на главной
youtube_url       = URLField(blank=True)   # канал
```

`Testimonial` уже есть — 110 отзывов ложатся в него, но **переносить только те, что реально существуют с источником**. Сводку «103 bardzo dobre» показываем как агрегат из `PassRate`-подобного блока, а не выдумываем 110 карточек.

## C.3 Навигация

```python
NAV = [
    NavItem("Kurs kat. B", "courses:detail", kwargs={"slug": "kat-b"}),
    NavItem("Cennik", "courses:pricing"),
    NavItem("Zapisy i dokumenty", "core:page", kwargs={"slug": "zapisy"}),
    NavItem("Zdawalność", "core:pass_rates"),
    NavItem("O nas", "core:page", kwargs={"slug": "o-nas"}),
    NavItem("Do pobrania", "core:downloads"),
    NavItem("Kontakt", "core:contact"),
]
```

Семь пунктов вместо якорей. `Kontakt` первым уровнем, как и было.

## C.4 Копия репозитория или мультитенант

Сейчас — **копия репозитория**. Два клиента не оправдывают мультитенантность, а ошибка в общем коде положила бы оба сайта сразу.

Но правило на будущее: всё, что отличается между школами, живёт **в данных и `.env`**, не в шаблонах. Если в шаблон попадает `{% if школа == "ostrycharz" %}` — ты сделал ветвление, которое через три клиента станет неуправляемым. На четвёртой школе переходишь на мультитенант.

## C.5 Про их фото и логотип

Логотип `mcqueen.png` и их фотографии — чужая собственность. В демо ставь либо нейтральные заглушки, либо их публичные фото с прямым указанием в письме, что это временно и заменится оригиналами. Логотип не трогай вообще: сделай леттеринг `OSK OSTRYCHARZ` тем же шрифтом, что и у Навроцкого.

---
---

# ЧАСТЬ D — ПРОМПТЫ

Порядок жёсткий. Одна сессия — один промпт — один PR.

## O0 — Копия репозитория

```
Режим: LEAD. Ядро: tech.md v4 → станет v5.

Задача: подготовить копию проекта под второго клиента, OSK Ostrycharz.

1. Скопируй репозиторий в новый: osk-ostrycharz. Историю Навроцкого не тащи,
   начни с одного коммита "chore: fork engine from osk-nawrocki".
2. Вычисти всё, что относится к первому клиенту:
   - scripts/seed.py — данные Навроцкого убрать целиком;
   - data/legacy/ — redirects.csv и useful_links.csv Навроцкого удалить;
   - tech.md §1 — блок «Проект» переписать под Ostrycharz;
   - deploy/Caddyfile — домен заменить на новый;
   - README — обновить.
3. Проверь, что нигде в коде не осталось строк "Nawrocki", "naukajazdywielun",
   "Zielona 45", "8321916014", "osk.adam.nawrocki@wp.pl". Прогони grep,
   приложи вывод к PR.
4. Секреты: сгенерируй новый DJANGO_SECRET_KEY и IP_HASH_SALT.
   Копировать старые нельзя.
5. tech.md §1 заполни данными из OSTRYCHARZ.md часть A.1.

Критерии приёмки:
- grep по перечисленным строкам пустой;
- docker compose up поднимает проект на чистой машине;
- тесты зелёные (кроме тех, что завязаны на сид — их чиним в O2).

Не начинай O1, пока это не смёржено.
```

---

## O1 — Контракты v5: три новых сущности

```
Режим: LEAD. Ядро: tech.md v4 → v5.

Прочитай OSTRYCHARZ.md часть C.2 и tech.md §4, §11.

Задача: добавить в ядро три вещи, которых не было у первого клиента.
Это append-only правка контракта, существующее не переписывать.

1. Модель PassRate — статистика сдачи по годам, схема в OSTRYCHARZ.md C.2.
   Проценты НЕ хранить в БД, считать в services.py: pass_rate_percent(entry).
2. Модель DownloadFile — документы для скачивания, схема там же.
   size_bytes заполнять в save() из файла, не просить у пользователя.
3. Поля youtube_video_url и youtube_url в SiteSettings.
4. Роуты: /zdawalnosc/ и /do-pobrania/. Добавь в tech.md §5.
5. Навигацию перепиши по OSTRYCHARZ.md C.3, в apps/core/navigation.py.
6. Компоненты: <c-passrate-table> и <c-download-list>. Пропсы опиши
   в tech.md §7 в том же формате, что остальные.
7. Бампни версию ядра до v5, добавь строку в changelog.
8. Сгенерируй миграции.

Ограничения:
- ни одно существующее поле не меняется и не удаляется;
- YouTube встраиваем БЕЗ скрипта YouTube: превью-картинка + ссылка,
  либо lite-embed без внешнего JS. Правило «никаких внешних CDN»
  из tech.md §2 действует.

Тесты:
- property: pass_rate_percent для любых значений возвращает 0..100
  и сумма процентов не превышает 100;
- unit: DownloadFile.save() заполняет size_bytes;
- unit: PassRate с students=0 не роняет расчёт.
```

---

## O2 — Сид под Ostrycharz

```
Режим: LEAD. Ядро: tech.md v5.

Прочитай OSTRYCHARZ.md часть A целиком.

Задача: переписать scripts/seed.py под нового клиента. Все тексты берутся
из части A ДОСЛОВНО, ничего не выдумывать.

Наполняешь:
1. SiteSettings — реквизиты из A.1. NIP оставь пустым и пометь
   TODO_OWNER: запросить NIP.
2. Один Course: slug="kat-b", kind="license", code="B", title="Prawo jazdy kat. B",
   price_gross=3700. Тексты entitlements и requirements возьми из своего
   первого проекта — законодательные требования к кат. B одинаковы для всех школ.
3. PriceItem — все восемь позиций из таблицы A.3, включая
   "Dowóz na egzamin — GRATIS" (price_gross=0, note="w cenie kursu").
4. PassRate — данные из A.5 за последний год: students=92, passed_1st=68,
   passed_2nd=16, passed_3rd=3, passed_4th=3. Годы 2019–2021 пометь
   TODO_OWNER — цифры есть только картинками, нужны от владельца.
5. DownloadFile — пять документов из A.6. Сами PDF пока не скачивай,
   создай записи с TODO_OWNER: получить файлы от владельца.
6. Page(slug="o-nas") — текст из A.2 дословно.
7. Page(slug="zapisy") — текст из A.4: как записаться и какие документы нужны.
8. UsefulLink — две ссылки из A.8 плюс gov.pl «uzyskaj prawo jazdy»
   и starostwo w Wieluniu.
9. Faq — восемь вопросов, выведи их из содержимого A.3 и A.4:
   ile kosztuje kurs, co wziąć na pierwsze zajęcia, ile trwa kurs przyspieszony,
   czy jest automat, ile kosztuje jazda doszkalająca, czy dowozicie na egzamin,
   od ilu lat można zacząć, jak wyrobić PKK.
10. Testimonial — НЕ создавай. Отзывы переносим только реальные,
    с источником. Оставь пустым, секция не отрендерится.

Сид идемпотентен: повторный запуск не плодит дубли.

Критерии приёмки:
- pytest -m owner_data печатает список того, что нужно запросить у владельца;
- все цены из A.3 присутствуют с точностью до злотого;
- ни одного выдуманного факта: если чего-то нет в части A — ставится TODO_OWNER.
```

---

## O3 — Страница статистики сдачи

```
Режим: DEV. Ядро: tech.md v5.

Прочитай OSTRYCHARZ.md A.5 и B.5, BLOCKS.md разделы A и B.

Задача: страница /zdawalnosc/ — самый сильный аргумент этой школы.
Сейчас у них он лежит текстом в середине одностраничника.

Композиция:
1. <c-page-header>: eyebrow "WYNIKI", h1 "Zdawalność", лид одной фразой,
   в слоте aside — <c-fact-card> с крупным "76%" и подписью
   "zdaje za pierwszym razem".
2. <c-stat-band ground="ink">: четыре числа за последний год —
   kursantów, za 1 razem, za 2 razem, średnia liczba podejść.
3. <c-passrate-table>: разбивка по годам, колонки — rok, kursantów,
   za 1 raz, za 2 raz, za 3 raz, za 4 raz. Проценты data-типографикой
   с tabular-nums.
4. <c-callout>: как считается статистика и за какой период —
   честность здесь важнее красоты, иначе цифрам не верят.
5. Блок отзывов, если есть опубликованные Testimonial. Нет — секция
   не рендерится.
6. <c-cta-band ground="ink">: "Chcesz zdać za pierwszym razem?"

SEO:
- title "Zdawalność — OSK Ostrycharz Wieluń";
- JSON-LD AggregateRating ТОЛЬКО если есть подтверждённые Testimonial
  с source_url. Выдуманный рейтинг в разметку не ставить ни при каких
  условиях — это прямое нарушение правил Google и повод для санкций.

Тесты: unit на расчёт процентов, unit на отсутствие AggregateRating
при нуле отзывов, SEO-тест.

Не трогай питон вне apps/core, если модель уже готова из O1.
```

---

## O4 — Прайс

```
Режим: DEV. Ядро: tech.md v5.

Прочитай OSTRYCHARZ.md A.3 и BLOCKS.md B9.

Задача: страница /cennik/. В отличие от первого проекта, здесь есть
реальные цены — прайс становится сильной страницей, а не заглушкой.

Композиция:
1. <c-page-header>: eyebrow "CENNIK", h1, лид "Ceny brutto, bez ukrytych
   kosztów", в aside — <c-fact-card> "3700 zł" с подписью "kurs kat. B".
2. <c-anchor-nav>: Kurs, Jazdy dodatkowe, Opłaty zewnętrzne.
3. Группа "Kurs": три позиции <c-price-row> — kurs 3700, kurs przyspieszony
   4300 z заметкой "2 tygodnie", skrzynia automatyczna 4300.
   На основном курсе бейдж "Najczęściej wybierany".
4. <c-callout tone="accent">: что входит в цену. Отдельной строкой —
   "Dowóz na egzamin — GRATIS", это их реальное преимущество.
5. Группа "Jazdy doszkalające" на ground muted: manual 160 zł/h,
   manual dla kursantów 140 zł/h, automat 140 zł/h.
6. Группа "Opłaty zewnętrzne" на paper: badanie lekarskie 200 zł,
   egzamin państwowy 230 zł, zaświadczenie o zameldowaniu 17 zł.
   Выноской пояснить, что это оплаты не школе.
7. <c-steps> "Jak zapłacić" — если владелец даст условия рассрочки.
   Нет данных — секция не рендерится.
8. <c-cta-band ground="ink">.

Критерии приёмки:
- все восемь позиций из OSTRYCHARZ.md A.3 на странице, суммы совпадают
  до злотого;
- "GRATIS" не отображается как "0,00 zł";
- разница между ценой школы и внешними оплатами видна визуально,
  а не только текстом;
- на 320px строка не разваливается.

Не трогай питон.
```

---

## O5 — Страница курса и записи

```
Режим: DEV. Ядро: tech.md v5.

Прочитай OSTRYCHARZ.md A.2, A.4, BLOCKS.md раздел D.

Задача: две страницы — /kursy/kat-b/ и /zapisy/.

Страница курса:
- шапка с <c-spec-list> в aside: wiek 18 lat, start od 17 lat 9 mies.,
  cena 3700 zł, dowóz na egzamin gratis;
- uprawnienia и wymagania карточками, как в первом проекте;
- секция про автомат и ускоренный курс — это их отличие, вынести отдельно;
- секция "Nasze samochody": из A.2 — klimatyzowane, bogate wyposażenie.
  Фотографий пока нет, ставь <c-empty> с телефоном;
- <c-cta-band>.

Страница "Zapisy i dokumenty":
- <c-steps> "Jak się zapisać": позвонить 691 570 489, ustalić termin,
  wyrobić PKK, przynieść dokumenty, zacząć zajęcia;
- <c-spec-list> "Co przynieść" — пять пунктов из A.4 дословно;
- <c-callout> про zaświadczenie o zameldowaniu (17 zł) — единственная
  платная бумажка, о ней стоит предупредить заранее;
- блок <c-download-list> со ссылками на документы;
- форма заявки внизу;
- <c-cta-band>.

Критерии приёмки:
- все пять документов из A.4 перечислены дословно;
- телефон кликабельный на обеих страницах;
- страница "Zapisy" работает при нуле загруженных PDF.

Не трогай питон.
```

---

## O6 — Документы для скачивания

```
Режим: DEV. Ядро: tech.md v5.

Прочитай OSTRYCHARZ.md A.6 и C.2.

Задача: страница /do-pobrania/ и компонент <c-download-list>.

Композиция:
1. <c-page-header>: eyebrow "DOKUMENTY", h1 "Do pobrania", лид объясняет,
   что эти документы нужны до начала курса.
2. Список файлов карточками: название, описание одной строкой, размер
   data-типографикой, иконка PDF, кнопка "Pobierz".
3. <c-callout>: какие документы нужно принести подписанными,
   а какие только прочитать.
4. <c-cta-band>.

Требования:
- размер файла отображается человекочитаемо: "1,2 MB", не "1258291";
- ссылка с атрибутом download и rel="noopener";
- файла нет — запись не рендерится, а не даёт битую ссылку;
- на мобильном кнопка "Pobierz" не меньше 44x44px.

Тесты: unit на форматирование размера, unit на скрытие записи
без прикреплённого файла.

Не трогай питон.
```

---

## O7 — Видео и главная

```
Режим: DEV. Ядро: tech.md v5.

Прочитай OSTRYCHARZ.md A.7, C.2, FRONTEND.md A.9.

Задача: главная страница под профиль этой школы.

Порядок секций — как в FRONTEND.md A.9, но с заменами:
1. Герой на ink: h1 "Prawo jazdy kat. B w Wieluniu", жёлтая плашка
   под "Wieluniu", подзаголовок про автомат и ускоренный курс,
   две кнопки, ряд фактов: "76% ZA PIERWSZYM RAZEM · KURS 3700 ZŁ ·
   DOWÓZ NA EGZAMIN GRATIS".
2. Вместо плиток девяти категорий — три карточки: kurs standardowy,
   kurs przyspieszony, automat. С ценами.
3. Блок статистики: крупные числа из PassRate, ссылка на /zdawalnosc/.
4. Видео: превью-картинка с кнопкой play, по клику открывается YouTube
   в новой вкладке ЛИБО lite-embed без внешнего скрипта.
   Скрипт youtube.com на странице не подключать.
5. Секция "Co dostajesz w cenie": dowóz na egzamin, klimatyzowane auta,
   materiały. Из A.2 и A.3.
6. Блок отзывов — только реальные, иначе не рендерится.
7. FAQ — пять вопросов из сида.
8. Контакт: адрес Asnyka 7, телефон, карта Leaflet, короткая форма.
9. Финальный CTA.

Критерии приёмки:
- ноль запросов к youtube.com и google.com до клика пользователя;
- страница читается при пустых PassRate и Testimonial;
- первый экран весит меньше 400 КБ;
- жёлтых акцентов на первом экране не больше трёх.

Не трогай питон.
```

---

## O8 — SEO и деплой

```
Режим: LEAD. Ядро: tech.md v5.

Прочитай tech.md §8, §17, §19, OSTRYCHARZ.md B.

Задача: SEO-пакет и вывод на временный адрес.

SEO:
1. Seo на всех страницах. Titles под локальные запросы:
   "Prawo jazdy Wieluń — OSK Ostrycharz", "Cennik kursu prawa jazdy Wieluń",
   "Zdawalność — OSK Ostrycharz", "Zapisy na kurs prawa jazdy Wieluń".
2. JSON-LD DrivingSchool с адресом Asnyka 7 и телефоном.
3. JSON-LD Course на странице курса с ценой 3700 zł.
4. AggregateRating — только при наличии подтверждённых отзывов.
5. sitemap.xml, robots.txt.
6. Редиректы: у них одностраничник, поэтому таблица простая —
   якоря вида /#informacje, /#pliki, /#kontakt перенаправить
   на соответствующие новые URL. Собери data/legacy/redirects.csv.

Деплой:
1. Новый поддомен DuckDNS, например osk-ostrycharz.duckdns.org.
2. Caddy на том же сервере, второй блок в Caddyfile.
   Порты 80 и 443 уже открыты.
3. Отдельные тома для БД и медиа — базы двух клиентов не смешивать.
4. ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, SECURE_PROXY_SSL_HEADER.
5. Проверка: https отвечает 200, сертификат валидный,
   /healthz зелёный.

Критерии приёмки:
- оба сайта работают одновременно на одном сервере и не пересекаются;
- Lighthouse mobile на главной ≥ 90;
- в разметке нет ни одного выдуманного отзыва или рейтинга.
```

---
---

# ЧАСТЬ E — ПИСЬМО

Их слабые места другие, чем у Навроцкого: сайт работает, сертификат в порядке, цены опубликованы. Поэтому давить на «всё сломано» нельзя — будет неправдой и он это увидит.

Правильный угол: **у вас лучший результат в районе и он спрятан**.

**Temat:** `Nowa strona dla OSK Ostrycharz — proszę o opinię`

```
Dzień dobry,

nazywam się [IMIĘ], jestem programistą.

Szukałem w Wieluniu kursu na prawo jazdy kat. B i porównywałem ośrodki.
U Państwa zwróciłem uwagę na jedną rzecz: 76% kursantów zdaje za pierwszym
razem, a 96% opinii jest bardzo dobrych. To najmocniejszy argument, jaki
szkoła jazdy może mieć — a na stronie leży w środku, między galerią
a plikami, i Google go nie pokazuje.

Zajmuję się stronami, więc zamiast pisać maila z uwagami, zbudowałem
nową wersję. Jest gotowa mniej więcej w 80% i już działa:

[LINK]

Co zmieniłem:

1. Zdawalność ma własną stronę i widać ją od razu na stronie głównej.
   Dodałem też oznaczenie dla Google, dzięki któremu przy wyniku
   wyszukiwania mogą pojawić się gwiazdki ocen.

2. Cennik na osobnej stronie z własnym adresem. Teraz można wysłać
   komuś link prosto do cen, a nie prosić, żeby przewinął stronę.

3. Osobne strony zamiast jednej. Obecna strona to jedna strona
   z zakładkami wewnątrz — Google widzi ją jako jeden wynik.
   Po zmianie każda sekcja jest osobnym wynikiem, pod hasła w rodzaju
   „cennik prawa jazdy Wieluń" czy „zapisy na prawo jazdy Wieluń".

4. Formularz zapisu zamiast formularza Google. Zgłoszenia trafiają
   do Państwa panelu i na maila, a nie do zewnętrznej usługi.
   Jest też wymagana zgoda RODO, której teraz brakuje.

5. Panel administracyjny. Ceny, zdawalność, pliki i teksty zmieniają
   Państwo sami, bez programisty.

6. Wersja rosyjska i ukraińska — w Wieluniu to spora grupa kandydatów.

7. Telefon. Cała strona działa poprawnie na telefonie.

8. W stopce obecnej strony jest „Copyright 2018-2020". Drobiazg,
   ale kandydat, który to zauważy, myśli, że ośrodek już nie działa.

Czego brakuje:

- Państwa zdjęcia — auta, zajęcia, instruktorzy
- pliki PDF z regulaminem i umową
- dane o zdawalności za wcześniejsze lata (na stronie są tylko obrazki)
- NIP i godziny otwarcia biura
- Państwa uwagi

Moja propozycja: nie chcę za to pieniędzy. Chciałbym w zamian kurs
prawa jazdy kategorii B.

Kończę stronę według Państwa uwag, przenoszę na Państwa domenę
oskostrycharz.pl, przekazuję dostępy i pokazuję, jak samodzielnie
zmieniać ceny i zdawalność. Państwo zapisują mnie na kurs.

Jeśli strona się nie spodoba — nic Państwo nie tracą. Zrobiłem ją
z własnej inicjatywy.

Proszę o odpowiedź mailem.

Pozdrawiam,
[IMIĘ NAZWISKO]
[E-MAIL]
```

**Не пиши в это письмо:** что их сайт «старый» или «плохой». У них он работает, сертификат в порядке, цены на месте. Скажешь «плохой» — потеряешь доверие на первой строке. Работает только конкретика: одностраничник, копирайт 2018-2020, форма Google, нет отдельных URL.

**И не отправляй, пока не поставишь их статистику на видное место.** Всё письмо построено на этом одном аргументе. Если он откроет ссылку и не увидит 76% в первом экране — письмо развалится.
