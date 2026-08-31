# tech.md — ядро проекта OSK Nawrocki

**Версия ядра: v17**

| Версия | Изменение |
|---|---|
| v17 | Чертежи транспорта перерисованы подробно: кузов, остекление с рамками, линии дверей, фонари, зеркало, складки, пятиспицевые диски. Спрайт разбит на файл на машину — `static/illustrations/vehicles/<name>.svg`: страница курса рисует один чертёж, а спрайтом тянула ещё семь, 29 КБ вместо 4 на экране, где бюджет A.11 и так впритык. Оформление осталось на атрибутах. Контрактный тест держит потолок 9 КБ на файл |
| v16 | Добавлен второй спрайт `static/illustrations/vehicles.svg` — восемь чертежей транспорта в профиль на поле 720×240: мопед, мотоцикл, легковая, легковая с прицепом, грузовик, грузовик с прицепом, автобус, погрузчик. Иконочный спрайт не тронут: там пиктограммы 24px, тут виды сбоку, общий файл означал бы один viewBox на две задачи. Оформление — атрибутами, не классами, потому что внешний `<use>` не обязан переносить CSS. Добавлен компонент `<c-vehicle-drawing name label>` (поле 3/1) и фильтр `course_vehicles`, который берёт транспорт по коду категории, а для курсов без кода — по slug. `illustrations` внесена в `STATICFILES_DIRS` |
| v15 | Стадия S9 выполнена. Интерфейс переведён через gettext: каталоги `locale/{pl,ru,uk}` под контролем версий как `.po`, `.mo` собираются энтрипойнтом в dev и стадией `messages` в продовом образе, `gettext` добавлен в dev-образ. msgid — польский исходник; отдельный каталог `pl` существует ради тех строк моделей, что были написаны по-английски. Контент из БД переведён через `django-modeltranslation`, значения — в `scripts/seed_translations.py`, идемпотентно и только в колонки `_ru`/`_uk`. Переключатель языка виден с md, ниже — в панели меню. Контрактов не меняет |
| v14 | Из `BLOCKS.md` взяты семь блоков: A1 карточка звонка, A4 графическая цифра, B3 шаги, B5 список превращённый в карточки, B6 цитата, B9 строка цены, B10 плитки категорий. Добавлены `<c-quote>`, `<c-steps>`, `<c-fact-card>`, `<c-price-row>` и класс `.u-bignum` |
| v13 | Добавлены `FRONTEND_FIXES.md` (аудит работающего сайта: 18 находок и промпты X0–X8) и `BLOCKS.md` (каталог восемнадцати блоков с готовым набором по каждой странице). Контрактов не меняют, только применяют |
| v12 | Добавлен `FRONTEND_POLISH.md` — блоки и правила ритма внутренних страниц: пятнадцать новых cotton-компонентов, чередование фона секций, обязательные шапка страницы и финальный CTA. Расширяет `FRONTEND.md` часть A, не переопределяет её. **Файла в репозитории нет** — по нему заблокированы `<c-anchor-nav>`, `<c-page-header>`, `<c-callout>`, `<c-split>`, `<c-spec-list>`, `<c-toc>` и `<c-empty>` |
| v11 | У `<c-section>` добавлен проп `size=compact|normal|tall` (48/64, 64/96, 96/128 по вертикали, по умолчанию normal) — FRONTEND_FIXES.md X0 п.4. Добавлены `--header-h` и `scroll-margin-top` под неё, класс `.u-prose` для markdown из БД и фильтр `without_lead_in` в `apps/core/templatetags` |
| v10 | В перечисление `tone` у `<c-section>` добавлено `deep` — фирменный фиолетовый как второй тёмный грунт, решение владельца. Внутренние страницы получили по одной инвертированной полосе; фиолетовая никогда не идёт последней перед футером, потому что футер тоже фиолетовый. `<c-breadcrumbs>` переведён на чтение грунта: он называл `text-ink` и исчезал на любом инвертированном фоне. Добавлена утилита `.u-on-ground` |
| v9 | Пункт 2 A.6 наконец реализован: раскрытие аккордеона и мобильного меню за 180ms — до этого ни то, ни другое не анимировалось вовсе. Пункт 4 дополнен движениями меню и плитки категории. Исправлено наложение карты на шапку: Leaflet нумерует свои слои до 1000, контейнер карты теперь изолирован |
| v8 | Пункт 4 A.6 расширен: подъём карточки и ценовой плитки до 4px, стрелки в кнопках едут по своей оси, индикатор аккордеона и фотографии в галерее отвечают на наведение, строка расписания получает фон. Ценовая плитка, строка расписания и индикатор аккордеона до этого не отвечали вовсе. Таблица величин — в FRONTEND.md A.6 |
| v7 | A.6 дополнен пунктом 4 по просьбе владельца: карточка-ссылка поднимается на 2px, иконка в кнопке растёт до 1.08, оба за 120ms. `transform` возвращён в список разрешённых переходов только для них; `box-shadow`, `filter` и `opacity` остаются вне его. Под `prefers-reduced-motion` оба движения сбрасываются явно, а не только по длительности |
| v6 | Тёмная тема отменена решением владельца. Тема одна — светлая; шапка стала тёмной полосой (`--ground: ink`) над светлой страницей на всех страницах. Причина: в тёмной теме `paper` и фон шапки совпадали, разделитель давал 1.4:1, шапка растворялась в странице везде, кроме главной. Механизм `--ground`/`--on-ground` сохранён — на нём держатся шапка, инвертированный герой и жёлтая полоса. Добавлена утилита `.u-ground-paper` — возврат к странице внутри инвертированной области. Подробности в FRONTEND.md A.2 |
| v5 | У `<c-button>` добавлено значение `size=icon` — квадрат 44px без горизонтального padding для кнопок без подписи (закрыть, бургер), DESIGN-REVIEW п.2. Такая кнопка обязана нести `aria-label` |
| v4 | `<c-card>` и `<c-course-card>` получили проп `level` (уровень заголовка карточки, по умолчанию 3). Карточка под `h1` без него давала пропуск `h1 → h3` на четырёх страницах — DESIGN-REVIEW п.6. Ратифицированы также накопленные ранее: слот по умолчанию у `<c-intake-row>` |
| v3 | Таблица §7 расширена по `FRONTEND.md`: добавлен `<c-icon>` (спрайт A.7), проп `height` у `<c-map>` (F1 п.6), значение `accent` в перечислениях `tone` у `<c-badge>` (A.5) и `<c-section>` (A.9 п.5). Только добавления, ни один существующий проп не изменён |
| v2 | Добавлен `FRONTEND.md` — дизайн-контракт фронтенда: палитра, типографика, сетка, состояния компонентов, композиция главной, бюджеты производительности и доступности. Расширяет §7, не переопределяет его |
| v1 | Первая заморозка: стек, схема БД, контракты задач Celery, UI-компоненты, URL-карта, редиректы со старого сайта, доктрина тестов, инфраструктура и деплой. Комплект сведён к трём файлам: `tech.md`, `DEV.md`, `CLAUDE.md` |

Файл читают все сессии. Правится только в режиме LEAD, только append-only, каждое изменение контракта бампает версию и добавляет строку в changelog.

**Комплект проекта — восемь файлов.** `tech.md` — ядро и все контракты (этот файл). `DEV.md` — порядок сборки скелета, чек-листы и стадийный список задач бэкенда. `PROMPTS.md` — промпты бэкенда, по одному на шаг. `FRONTEND.md` — дизайн-контракт и промпты фронтенда. `FRONTEND_POLISH.md` — блоки и ритм внутренних страниц. `FRONTEND_FIXES.md` — аудит работающего сайта и промпты на починку. `BLOCKS.md` — каталог блоков с набором по каждой странице. `CLAUDE.md` — указатель для сессии.

**Команда — один человек в двух режимах.** Режим **LEAD**: скелет, контракты, миграции, общие файлы, CI/CD, ревью. Режим **DEV**: фичи, один вертикальный слайс за сессию. Режимы не смешиваются в одной сессии — это единственное, что физически мешает фиче-сессии походя переписать общий контракт, чтобы стало удобнее.

---

## 1. Проект

**Что:** новый сайт ośrodek szkolenia kierowców «OSK Nawrocki» (Ośrodek Kształcenia i Doskonalenia Zawodowego Adam Nawrocki, Mariola Nawrocka S.C.), Wieluń.

**Взамен чего:** `naukajazdywielun.pl` на конструкторе WebWave. Старый сайт: нерабочий HTTPS (сертификат на чужое имя), невидимая форма контакта, «Kontakt» спрятан в подменю, ноль цен и дат, ноль `h1`, пустые `meta description`, URL с пробелами (`/KAT.%20B`).

**Для кого:**
- кандидат на права кат. B, 17–25 лет, приходит с телефона по запросу «prawo jazdy Wieluń», ищет цену и ближайший старт;
- профессиональный водитель, ищет kwalifikację wstępną / szkolenie okresowe / ADR, часто русско- или украиноязычный;
- работодатель, отправляет сотрудников на психотесты и wózki widłowe.

**Цель:** заявка или звонок. Всё остальное на сайте существует ради этих двух действий.

**Ключевое преимущество школы, которое сайт обязан показывать:** занятия ведутся в том числе на русском языке. На старом сайте эта фраза спрятана в абзаце на главной.

**Реквизиты (константы, попадают в `SiteSettings` через сид):**

```
Ośrodek Kształcenia i Doskonalenia Zawodowego Adam Nawrocki, Mariola Nawrocka S.C.
ul. Zielona 45, 98-300 Wieluń
NIP: 8321916014
tel. 43 843 29 11 / 605 065 795 / 667 615 184
osk.adam.nawrocki@wp.pl
Работает с 1996 года
Геокоордината офиса: см. SiteSettings.map_lat / map_lng (заполнить при сиде)
```

Номер банковского счёта на публичных страницах не выводим. Хранится в `SiteSettings.bank_account` с флагом `bank_account_public=False`, показывается только в админке и на странице оплаты после явного включения.

---

## 2. Стек

| Слой | Технология | Комментарий |
|---|---|---|
| Язык | Python 3.12 | |
| Фреймворк | Django 5.1 | |
| БД | PostgreSQL 16 | |
| Шаблоны | Django Templates + **django-cotton** | компоненты с пропсами вместо `{% include %}` с километром контекста |
| Интерактив | **HTMX 2** + Alpine.js 3 (точечно) | формы, фильтры, лайтбокс, языковой переключатель |
| CSS | **Tailwind CSS 3** (standalone CLI, без Node в проде) | токены в `tailwind.config.js` |
| Очередь | **Celery 5 + Redis 7** | + `celery beat` для периодических задач |
| Изображения | **django-imagekit** + Pillow | WebP-рендишены, `<picture>` |
| i18n | Django i18n (UI) + **django-modeltranslation** (контент) | PL (default), RU, UK |
| Конфиг | **django-environ** | всё из `.env`, `.env.example` в репо |
| Синглтон настроек | **django-solo** | `SiteSettings` |
| Статика | WhiteNoise (сжатие + манифест) | раздаёт Caddy, WhiteNoise как фоллбэк |
| Формы | django-crispy-forms + crispy-tailwind | |
| Антиспам | honeypot-поле + `django-ratelimit` | без внешней капчи, чтобы не тащить чужие куки |
| Карта | **Leaflet + OpenStreetMap** | без Google-скриптов, значит без cookie-гейта на карту |
| Веб-сервер | Gunicorn (gthread) за **Caddy 2** | Caddy = автоматический Let's Encrypt, это лечит главную боль старого сайта |
| Контейнеры | Docker + docker compose | dev и prod |
| CI/CD | GitHub Actions | гейт на PR + деплой на мёрдж в `main` |
| Тесты | **pytest**, pytest-django, factory-boy, **hypothesis**, **Playwright** (Python) | |
| Линт | **ruff** (lint + format), **mypy** + django-stubs | |
| Ошибки | Sentry (self-hosted или free tier) | |

Запрещено без решения в режиме LEAD: jQuery, Bootstrap, React/Vue, любой CDN-скрипт стороннего хоста на публичных страницах, Google Fonts с внешнего хоста (шрифты самохостим).

---

## 3. Структура репозитория

```
osk/
├── config/
│   ├── settings/            base.py, dev.py, prod.py, test.py
│   ├── urls.py              корневой роутер, i18n_patterns
│   ├── celery.py            app + beat schedule
│   ├── wsgi.py  asgi.py
├── apps/
│   ├── core/                SiteSettings, Page, OpeningHours, SEO, контракты, UI-теги
│   ├── courses/             Course, CourseIntake, PriceItem
│   ├── leads/               Lead, LeadForm, tasks
│   ├── people/              Instructor, Vehicle
│   ├── gallery/             GalleryImage, Certificate
│   ├── links/               UsefulLink, Faq, tasks
│   └── reviews/             Testimonial
├── templates/
│   ├── base.html
│   ├── cotton/              UI-примитивы (django-cotton), см. §7
│   ├── layout/              header.html, footer.html, nav.html, cookie_banner.html
│   ├── pages/               home.html, page_detail.html, contact.html …
│   ├── courses/  leads/  gallery/  links/  reviews/
│   └── seo/                 jsonld_*.html
├── static/
│   ├── src/css/app.css      Tailwind input
│   ├── js/                  htmx.min.js, alpine.min.js, app.js, leaflet/
│   └── fonts/               самохостинг
├── tests/
│   ├── unit/  contracts/  idempotency/  property/  e2e/
│   └── factories.py  conftest.py
├── scripts/
│   ├── seed.py              общие фикстуры, единственный источник демо-данных
│   └── import_legacy.py     импорт текстов старого сайта из data/legacy/
├── data/legacy/             выгрузка старого сайта: тексты .md + список URL
├── deploy/
│   ├── Caddyfile  docker-compose.prod.yml  Dockerfile
├── .github/workflows/       ci.yml, deploy.yml
├── tech.md  DEV.md  PROMPTS.md  FRONTEND.md
├── FRONTEND_POLISH.md  FRONTEND_FIXES.md  BLOCKS.md  CLAUDE.md
├── .env.example  pyproject.toml  pytest.ini  tailwind.config.js
```

**Правило приложений:** каждое приложение — вертикальный слайс. Модели, админка, формы, вьюхи, urls, задачи, шаблоны фичи лежат внутри своего `apps/<name>/`. Общее — только в `apps/core/`.

---

## 4. Схема БД

Заморожена. Разработчик поля не добавляет. Не хватает поля — `CONTRACT GAP` (§11).

Все модели наследуют `apps.core.models.TimeStampedModel` (`created_at`, `updated_at`).
Поля, помеченные `[tr]`, переводимы через `django-modeltranslation` (создаются колонки `_pl`, `_ru`, `_uk`).

### 4.1 core

```python
class SiteSettings(SingletonModel):
    legal_name          = CharField(max_length=200)
    short_name          = CharField(max_length=80, default="OSK Nawrocki")
    street              = CharField(max_length=120)
    postal_code         = CharField(max_length=10)
    city                = CharField(max_length=80)
    nip                 = CharField(max_length=20)
    email               = EmailField()
    phone_primary       = CharField(max_length=32)
    phone_secondary     = CharField(max_length=32, blank=True)
    phone_tertiary      = CharField(max_length=32, blank=True)
    whatsapp            = CharField(max_length=32, blank=True)
    bank_account        = CharField(max_length=40, blank=True)
    bank_account_public = BooleanField(default=False)
    founded_year        = PositiveSmallIntegerField(default=1996)
    map_lat             = DecimalField(max_digits=9,  decimal_places=6, null=True)
    map_lng             = DecimalField(max_digits=9,  decimal_places=6, null=True)
    facebook_url        = URLField(blank=True)
    google_business_url = URLField(blank=True)
    lead_notify_emails  = CharField(max_length=300, help_text="через запятую")
    analytics_enabled   = BooleanField(default=False)

class OpeningHours(models.Model):
    DEPT = TextChoices("OFFICE", "PSYCHOLOGY")
    department = CharField(choices=DEPT.choices, max_length=16)
    weekday    = PositiveSmallIntegerField()          # 0=Mon … 6=Sun
    opens      = TimeField(null=True, blank=True)     # null = выходной
    closes     = TimeField(null=True, blank=True)
    note       = CharField(max_length=120, blank=True)   [tr]
    class Meta: unique_together = ("department", "weekday"); ordering = ("department", "weekday")

class Page(models.Model):                    # плоские страницы: o-nas, polityka-prywatnosci, rodo
    slug        = SlugField(unique=True)
    title       = CharField(max_length=200)              [tr]
    lead        = TextField(blank=True)                  [tr]
    body        = TextField()                            [tr]   # markdown
    seo_title   = CharField(max_length=70, blank=True)   [tr]
    seo_desc    = CharField(max_length=170, blank=True)  [tr]
    is_published= BooleanField(default=True)
    updated_at  = DateTimeField(auto_now=True)
```

### 4.2 courses

```python
class Course(models.Model):
    class Kind(TextChoices):
        LICENSE      = "license",      "Kategoria prawa jazdy"
        PROFESSIONAL = "professional", "Kierowca zawodowy"
        PSYCHOTEST   = "psychotest",   "Badania psychologiczne"
        OPERATOR     = "operator",     "Uprawnienia operatora"

    kind            = CharField(choices=Kind.choices, max_length=16, db_index=True)
    slug            = SlugField(unique=True)              # kat-b, kwalifikacja-wstepna …
    code            = CharField(max_length=16, blank=True)   # "B", "B+E", "ADR"
    title           = CharField(max_length=160)           [tr]
    lead            = TextField(blank=True)               [tr]   # 1-2 предложения на карточке
    entitlements    = TextField(blank=True)               [tr]   # "Uprawnia do kierowania:" — markdown-список
    requirements    = TextField(blank=True)               [tr]   # "Wymagania…" — markdown-список
    body            = TextField(blank=True)               [tr]   # доп. текст, markdown
    min_age         = PositiveSmallIntegerField(null=True, blank=True)
    theory_hours    = PositiveSmallIntegerField(null=True, blank=True)
    practice_hours  = PositiveSmallIntegerField(null=True, blank=True)
    total_hours     = PositiveSmallIntegerField(null=True, blank=True)
    price_gross     = DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    price_note      = CharField(max_length=160, blank=True)  [tr]  # "cena od", "z egzaminem wewnętrznym"
    languages       = ArrayField(CharField(max_length=2), default=list)  # ["pl","ru","uk"]
    hero_image      = ImageField(upload_to="courses/", blank=True)
    hero_alt        = CharField(max_length=160, blank=True)  [tr]
    seo_title       = CharField(max_length=70, blank=True)   [tr]
    seo_desc        = CharField(max_length=170, blank=True)  [tr]
    is_active       = BooleanField(default=True, db_index=True)
    order           = PositiveSmallIntegerField(default=100)
    class Meta: ordering = ("kind", "order", "id"); indexes = [Index(fields=["kind", "is_active"])]

class CourseIntake(models.Model):            # набор / старт группы
    class Mode(TextChoices):
        STATIONARY = "stationary"; ELEARNING = "elearning"; MIXED = "mixed"
    class Status(TextChoices):
        PLANNED = "planned"; OPEN = "open"; FULL = "full"; CLOSED = "closed"

    course      = FK(Course, related_name="intakes", on_delete=PROTECT)
    start_date  = DateField(db_index=True)
    end_date    = DateField(null=True, blank=True)
    mode        = CharField(choices=Mode.choices, max_length=12)
    language    = CharField(max_length=2, default="pl")
    seats_total = PositiveSmallIntegerField(null=True, blank=True)
    seats_taken = PositiveSmallIntegerField(default=0)
    status      = CharField(choices=Status.choices, max_length=8, default=Status.PLANNED, db_index=True)
    note        = CharField(max_length=200, blank=True)   [tr]
    class Meta: ordering = ("start_date",); indexes = [Index(fields=["status", "start_date"])]

class PriceItem(models.Model):               # доп. услуги вне курсов
    title      = CharField(max_length=160)                [tr]
    note       = CharField(max_length=200, blank=True)    [tr]
    price_gross= DecimalField(max_digits=8, decimal_places=2)
    unit       = CharField(max_length=40, blank=True)     [tr]   # "za godzinę", "za osobę"
    group      = CharField(max_length=40, blank=True)     [tr]   # "Jazdy doszkalające"
    order      = PositiveSmallIntegerField(default=100)
    is_active  = BooleanField(default=True)
```

### 4.3 leads

```python
class Lead(models.Model):
    class Status(TextChoices):
        NEW = "new"; CONTACTED = "contacted"; ENROLLED = "enrolled"; REJECTED = "rejected"; SPAM = "spam"

    first_name        = CharField(max_length=80)
    last_name         = CharField(max_length=80, blank=True)
    phone             = CharField(max_length=32)
    email             = EmailField(blank=True)
    course            = FK(Course, null=True, blank=True, on_delete=SET_NULL, related_name="leads")
    intake            = FK(CourseIntake, null=True, blank=True, on_delete=SET_NULL, related_name="leads")
    preferred_language= CharField(max_length=2, default="pl")
    message           = TextField(blank=True, max_length=2000)
    consent_rodo      = BooleanField(default=False)
    consent_marketing = BooleanField(default=False)
    status            = CharField(choices=Status.choices, max_length=10, default=Status.NEW, db_index=True)
    source_path       = CharField(max_length=200, blank=True)
    utm_source        = CharField(max_length=80, blank=True)
    utm_medium        = CharField(max_length=80, blank=True)
    utm_campaign      = CharField(max_length=80, blank=True)
    ip_hash           = CharField(max_length=64, blank=True)   # sha256(ip + SECRET_SALT), сырой IP не храним
    user_agent        = CharField(max_length=300, blank=True)
    notified_at       = DateTimeField(null=True, blank=True)   # ключ идемпотентности уведомления
    confirmed_at      = DateTimeField(null=True, blank=True)   # ключ идемпотентности автоответа
    class Meta: ordering = ("-created_at",); indexes = [Index(fields=["status", "created_at"])]
```

`consent_rodo` обязателен на уровне формы. Лид без согласия не создаётся.

### 4.4 people

```python
class Instructor(models.Model):
    full_name   = CharField(max_length=120)
    role        = CharField(max_length=120, blank=True)   [tr]
    bio         = TextField(blank=True)                   [tr]
    since_year  = PositiveSmallIntegerField(null=True, blank=True)
    categories  = M2M(Course, blank=True, limit_choices_to={"kind": "license"}, related_name="instructors")
    photo       = ImageField(upload_to="people/", blank=True)
    order       = PositiveSmallIntegerField(default=100)
    is_active   = BooleanField(default=True)

class Vehicle(models.Model):
    class Gearbox(TextChoices): MANUAL = "manual"; AUTO = "auto"
    course      = FK(Course, on_delete=CASCADE, related_name="vehicles")
    make        = CharField(max_length=60)
    model       = CharField(max_length=60)
    year        = PositiveSmallIntegerField(null=True, blank=True)
    gearbox     = CharField(choices=Gearbox.choices, max_length=8, default=Gearbox.MANUAL)
    note        = CharField(max_length=200, blank=True)   [tr]
    photo       = ImageField(upload_to="vehicles/", blank=True)
    is_exam_spec= BooleanField(default=True, help_text="zgodny z wymogami egzaminacyjnymi")
    order       = PositiveSmallIntegerField(default=100)
    is_active   = BooleanField(default=True)
```

### 4.5 gallery

```python
class GalleryImage(models.Model):
    class Section(TextChoices):
        SCHOOL = "school"; VEHICLES = "vehicles"; YARD = "yard"; EVENTS = "events"
    section     = CharField(choices=Section.choices, max_length=10, db_index=True)
    image       = ImageField(upload_to="gallery/")
    alt         = CharField(max_length=160)               [tr]   # обязателен, пустой alt не проходит валидацию
    caption     = CharField(max_length=200, blank=True)   [tr]
    order       = PositiveSmallIntegerField(default=100)
    is_published= BooleanField(default=True)
    legacy_name = CharField(max_length=80, blank=True)    # "1.JPG" — связь с выгрузкой старого сайта

class Certificate(models.Model):
    title       = CharField(max_length=200)               [tr]   # обязателен: на старом сайте 11 сканов без подписей
    issuer      = CharField(max_length=160, blank=True)   [tr]
    issued_on   = DateField(null=True, blank=True)
    description = TextField(blank=True)                   [tr]
    image       = ImageField(upload_to="certificates/")
    file        = FileField(upload_to="certificates/pdf/", blank=True)
    order       = PositiveSmallIntegerField(default=100)
    is_published= BooleanField(default=True)
```

### 4.6 links

```python
class UsefulLink(models.Model):
    class Group(TextChoices):
        EXAM = "exam"; GOV = "gov"; TESTS = "tests"; LOCAL = "local"
    group        = CharField(choices=Group.choices, max_length=8, db_index=True)
    title        = CharField(max_length=160)              [tr]
    description  = CharField(max_length=240)              [tr]   # обязательна: голый URL без пояснения запрещён
    url          = URLField()
    order        = PositiveSmallIntegerField(default=100)
    is_active    = BooleanField(default=True)
    last_checked_at = DateTimeField(null=True, blank=True)
    last_status  = PositiveSmallIntegerField(null=True, blank=True)   # HTTP-код последней проверки
    last_error   = CharField(max_length=200, blank=True)

class Faq(models.Model):
    question  = CharField(max_length=240)   [tr]
    answer    = TextField()                 [tr]
    group     = CharField(max_length=40, blank=True)   [tr]
    order     = PositiveSmallIntegerField(default=100)
    is_published = BooleanField(default=True)
```

### 4.7 reviews

```python
class Testimonial(models.Model):
    class Source(TextChoices): GOOGLE = "google"; MANUAL = "manual"; FACEBOOK = "facebook"
    author_name  = CharField(max_length=120)
    rating       = PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text         = TextField()              [tr]
    source       = CharField(choices=Source.choices, max_length=10, default=Source.MANUAL)
    source_url   = URLField(blank=True)
    published_on = DateField(null=True, blank=True)
    is_published = BooleanField(default=False)   # публикуем только вручную подтверждённые
    order        = PositiveSmallIntegerField(default=100)
```

Отзывы вводятся только вручную из реальных источников с указанием `source_url`. Синтетические отзывы запрещены.

### 4.8 Редиректы со старого сайта

Используем `django.contrib.redirects` + data-миграцию, которая заполняет таблицу из `data/legacy/redirects.csv`. Формат: `old_path,new_path`. Обязательный минимум (301):

```
/KAT. AM                              → /kursy/kat-am/
/KAT. A1                              → /kursy/kat-a1/
/KAT. A2                              → /kursy/kat-a2/
/KAT. A                               → /kursy/kat-a/
/KAT. B                               → /kursy/kat-b/
/KAT. BE                              → /kursy/kat-be/
/KAT. C                               → /kursy/kat-c/
/KAT. CE                              → /kursy/kat-ce/
/KAT. D                               → /kursy/kat-d/
/Szkolenia okresowe                   → /kierowca-zawodowy/szkolenia-okresowe/
/Kwalifikacja wstępna                 → /kierowca-zawodowy/kwalifikacja-wstepna/
/Kwalifikacja wstępna przyspieszona   → /kierowca-zawodowy/kwalifikacja-wstepna-przyspieszona/
/Badania psychologiczne               → /badania-psychologiczne/
/Kurs ADR                             → /kierowca-zawodowy/adr/
/Wózki widłowe                        → /wozki-widlowe/
/Oferta                               → /kursy/
/O nas                                → /o-nas/
/Kontakt                              → /kontakt/
/Galeria                              → /galeria/
/Certyfikaty                          → /certyfikaty/
/Przydatne strony                     → /przydatne-linki/
```

Каждый путь заводится в двух вариантах: с пробелами и в percent-encoded виде (`/KAT.%20B`). Тест на редиректы обязателен.

---

## 5. URL-карта

`i18n_patterns` с `prefix_default_language=False`: польский без префикса, `/ru/…`, `/uk/…`.

| URL | View | Модель |
|---|---|---|
| `/` | `core.views.home` | Course, CourseIntake, Testimonial |
| `/kursy/` | `courses.views.course_list` | Course(kind=license) |
| `/kursy/<slug>/` | `courses.views.course_detail` | Course |
| `/kierowca-zawodowy/` | `courses.views.pro_hub` | Course(kind=professional) |
| `/kierowca-zawodowy/<slug>/` | `courses.views.course_detail` | Course |
| `/badania-psychologiczne/` | `courses.views.course_detail` | Course(slug=badania-psychologiczne) |
| `/wozki-widlowe/` | `courses.views.course_detail` | Course(slug=wozki-widlowe) |
| `/cennik/` | `courses.views.pricing` | Course, PriceItem |
| `/terminy/` | `courses.views.intakes` | CourseIntake |
| `/o-nas/` | `core.views.page_detail` | Page + Instructor + Vehicle |
| `/galeria/` | `gallery.views.gallery` | GalleryImage |
| `/certyfikaty/` | `gallery.views.certificates` | Certificate |
| `/przydatne-linki/` | `links.views.useful_links` | UsefulLink |
| `/faq/` | `links.views.faq` | Faq |
| `/kontakt/` | `core.views.contact` | SiteSettings, OpeningHours, LeadForm |
| `/zapisz-sie/` | `leads.views.enroll` | LeadForm |
| `/zapisz-sie/dziekujemy/` | `leads.views.thanks` | — |
| `/polityka-prywatnosci/`, `/rodo/` | `core.views.page_detail` | Page |
| `/sitemap.xml`, `/robots.txt` | contrib.sitemaps / static view | — |

HTMX-эндпоинты (частичные ответы, всегда `_partial` в имени шаблона):

| URL | Что делает |
|---|---|
| `POST /zapisz-sie/submit/` | приём формы, возвращает `leads/_form_result.html` |
| `GET /terminy/filter/` | фильтр наборов по курсу/языку/режиму, возвращает `courses/_intake_rows.html` |
| `GET /galeria/lightbox/<pk>/` | одиночное изображение для лайтбокса |

---

## 6. Контракты фоновых задач (Celery)

Общие правила:

- Очередь по умолчанию `default`, брокер и бэкенд результатов — Redis.
- Все задачи `bind=True`, `autoretry_for=(Exception,)`, `retry_backoff=True`, `retry_backoff_max=600`, `max_retries=5`, `acks_late=True`.
- **Идемпотентность обязательна.** Каждая задача первым делом проверяет своё поле-ключ и выходит без побочного эффекта, если работа уже сделана.
- Payload задачи — только примитивы (id, строки). Объекты модели в аргументы не передаём.
- Payload валидируется через `apps.core.contracts` (TypedDict + функция `validate_payload`). Тест контракта обязателен.

| Задача | Payload | Ключ идемпотентности | Эффект |
|---|---|---|---|
| `leads.tasks.notify_owner` | `{"lead_id": int}` | `Lead.notified_at is None` | письмо на `SiteSettings.lead_notify_emails`, затем `notified_at = now()` |
| `leads.tasks.send_confirmation` | `{"lead_id": int}` | `Lead.confirmed_at is None` | автоответ заявителю на его языке, затем `confirmed_at = now()` |
| `gallery.tasks.build_renditions` | `{"model": str, "pk": int}` | наличие файлов рендишенов | генерит WebP 480/960/1600 через imagekit |
| `links.tasks.check_links` | `{}` (beat, ежедневно 03:20) | по природе повторяемая | HEAD/GET по каждому `UsefulLink`, пишет `last_status`, `last_checked_at`, `last_error` |
| `core.tasks.ping_sitemap` | `{}` (beat, ежедневно 04:00) | по природе повторяемая | пинг Google/Bing на `sitemap.xml` |
| `core.tasks.db_backup` | `{}` (beat, ежедневно 02:00) | имя файла с датой | `pg_dump` в `deploy/backups/`, ротация 14 дней |

Расписание beat живёт в `config/celery.py` и нигде больше.

**Внешние клиенты за интерфейсами.** Реальных доступов нет с первого дня, разработка идёт против фейков:

```python
# apps/core/clients/base.py
class MailClient(Protocol):
    def send(self, *, to: list[str], subject: str, body_html: str, body_text: str) -> str: ...

class SmsClient(Protocol):
    def send(self, *, to: str, text: str) -> str: ...
```

Реализации: `FakeMailClient` (пишет в `tests/outbox/`, валидирует поля), `SmtpMailClient`; `FakeSmsClient`, `SmsApiClient` (SMSAPI.pl, включается позже). Выбор через `settings.MAIL_CLIENT` / `SMS_CLIENT`. В dev и в тестах — всегда фейки.

---

## 7. UI-компоненты (собирает LEAD в скелете)

`django-cotton`, каталог `templates/cotton/`. Разработчик использует их и не пишет свою разметку кнопок, карточек и полей.

| Компонент | Тег | Пропсы |
|---|---|---|
| Кнопка | `<c-button>` | `variant=primary|secondary|ghost`, `size=sm|md|lg|icon`, `href`, `type`, `full` |
| Карточка | `<c-card>` | `href`, `padded`, `level=2|3|4`, слот `title`, слот по умолчанию |
| Бейдж | `<c-badge>` | `tone=neutral|success|warning|danger|accent`, слот |
| Цитата | `<c-quote>` | `text`, `author`, `role` |
| Шаги | `<c-steps>` | `steps` (строки с `.title` и `.text`) |
| Карточка факта | `<c-fact-card>` | `label`, `value`, `note`, `href`, слот `action`, слот по умолчанию |
| Строка цены | `<c-price-row>` | `title`, `price`, `note`, `badge`, `href` |
| Секция | `<c-section>` | `id`, `tone=default|muted|brand|deep|accent`, `size=compact|normal|tall`, слот `heading`, слот `sub` |
| Заголовок секции | `<c-heading>` | `level=1..4`, `eyebrow`, слот |
| Таблица | `<c-table>` | `headers` (list), слот строк |
| Аккордеон | `<c-accordion>` / `<c-accordion.item>` | `title`, `open` |
| Модалка | `<c-modal>` | `id`, `title`, слот; Alpine |
| Поле формы | `<c-field>` | `field` (BoundField), `label`, `help`, `required` |
| Инпут | `<c-input>` | `name`, `type`, `value`, `error`, `placeholder` |
| Селект | `<c-select>` | `name`, `options`, `value`, `error` |
| Textarea | `<c-textarea>` | `name`, `rows`, `value`, `error` |
| Чекбокс | `<c-checkbox>` | `name`, `checked`, `error`, слот (текст согласия) |
| Алерт | `<c-alert>` | `tone=info|success|warning|danger`, `title`, слот |
| Хлебные крошки | `<c-breadcrumbs>` | `items` (list of {title,url}) |
| Картинка | `<c-picture>` | `image` (ImageField), `alt`, `sizes`, `loading=lazy|eager`, `ratio` |
| Плитка галереи | `<c-gallery-grid>` | `images`, `columns` |
| Лайтбокс | `<c-lightbox>` | `images`; Alpine |
| CTA-панель | `<c-cta-bar>` | `title`, `phone`, `href`; sticky снизу на мобильном |
| Плитка цены | `<c-price-tile>` | `title`, `price`, `note`, `href` |
| Карточка курса | `<c-course-card>` | `course`, `level=2|3` |
| Строка набора | `<c-intake-row>` | `intake`, слот по умолчанию (то, что строка не выводит из самого набора: свободные места) |
| Часы работы | `<c-hours-table>` | `department` |
| Карта | `<c-map>` | `lat`, `lng`, `zoom`, `label`, `height=sm|md|lg`; Leaflet, без внешних скриптов |
| Иконка | `<c-icon>` | `name`, `size=sm|md|lg`, `label`; локальный спрайт `static/icons/sprite.svg` |
| Переключатель языка | `<c-lang-switcher>` | — |
| Cookie-баннер | `<c-cookie-banner>` | — |
| Панель отзывов | `<c-testimonials>` | `items` |
| Навигация | `<c-nav>` | берёт пункты из `apps/core/navigation.py` |

**Навигация — данные, не разметка.** Единственный источник — `apps/core/navigation.py`:

```python
NAV = [
    NavItem("Kursy", "courses:list", children=[...]),
    NavItem("Kierowca zawodowy", "courses:pro_hub", children=[...]),
    NavItem("Cennik", "courses:pricing"),
    NavItem("Terminy", "courses:intakes"),
    NavItem("O nas", "core:page", kwargs={"slug": "o-nas"}),
    NavItem("Galeria", "gallery:index"),
    NavItem("Kontakt", "core:contact"),
]
```

`Kontakt` — пункт первого уровня. Прятать его в подменю запрещено: это была главная ошибка старого сайта.

**Что добавила v14 и почему.** Правая половина шапки страницы пустовала на всех внутренних страницах: на `/o-nas/` заголовок занимал левые 40%, справа тысяча пустых пикселей. Туда встали карточка звонка там, где человеку нужна цена или человек, и графическая цифра там, где показать нечего. Цифра — сознательно украшение: выдумать данные ради заполнения слота было бы хуже.

**Что добавила v11 и почему.** Осмотр сайта (FRONTEND_FIXES.md) нашёл четыре вещи каркаса. Липкая шапка резала контент при переходе по якорю — у якоря нет представления о ней, и браузер ставил цель под шапку. Секция на 337 символов занимала 707px, поэтому у высоты появились три ступени. Markdown из БД рендерился как обычная проза, и заголовки разделов проигрывали по весу лиду страницы. И заголовок секции дублировался первой строкой тела на всех пятнадцати страницах курсов.

**Что добавила v10 и почему.** Внутренние страницы читались пустыми, и замер объяснил почему: ступень `paper-50`, которой они разделялись, даёт контраст 1.044:1 — на телефоне при дневном свете такой полосы нет. А единственный по-настоящему видимый грунт, инвертированный, стоял только на главной. Теперь по одной тёмной полосе на страницу, чёрной или фиолетовой. Заодно вскрылось, что крошки и часть подписей называли цвета страницы и на тёмном фоне пропадали — их нашёл axe, а не глаз.

**Что добавила v9 и почему.** Владелец указал на меню и плитки категорий как на неподвижные, и на карту, которая при прокрутке налезала на шапку. Проверка показала, что пункт 2 самого A.6 — раскрытие аккордеона и мобильного меню — не был реализован никогда: `<details>` не рендерит содержимое закрытым, а `<dialog>` открывается за кадр. Карта — не вопрос дизайна: Leaflet нумерует панели от 400 и контроллы до 1000 абсолютными значениями, и они били шапку на z-30.

**Что добавила v8 и почему.** Владелец сказал, что анимации в кнопках и блоках всё ещё мало. Проверка показала, что дело было не в величине, а в охвате: ценовая плитка, строка расписания и индикатор аккордеона не отвечали на указатель ни одним свойством. Добавлен отклик там, где его не было, а подъём карточки увеличен вдвое — 2px тонули в собственной рамке.

**Что добавила v7 и почему.** Сайт читался неподвижным: A.6 разрешал ровно переходы цвета и появление секции, и на наведение отвечали только рамка и цвет. Владелец попросил живее. Добавлены два движения и ни одного больше — их достаточно, чтобы интерфейс отвечал, и мало, чтобы страница не начала шевелиться сама по себе. Обнуления длительности под reduced-motion оказалось мало: оно превращает переход в прыжок, поэтому `transform` там снимается отдельным правилом.

**Что изменила v6 и почему.** Тёмная тема убрана целиком, а не подкрашена. Её главный дефект был структурным: шапка брала грунт страницы, и в тёмной теме оба становились `#0E0E10`. Между ними оставалась волосяная линия `line.soft` — 1.4:1, то есть ничего. Владелец выбрал тёмную полосу над светлой страницей, всегда. Заодно исчезли наблюдатель `data-stuck` и его часовой в `base.html`: граница теперь сама смена цвета, и наблюдать за прокруткой незачем.

**Что добавила v5 и почему.** Иконочная кнопка. A.7 разрешает иконке стоять без слова ровно в двух местах — закрыть и бургер, — а `<c-button>` задавала высоту 48px и padding 24px, под которые такая кнопка не подходит. Из-за этого семь кнопок в шаблонах были написаны руками мимо §7. `size=icon` — квадрат 44px, то есть минимальная честная цель касания из A.11.

**Что добавила v4 и почему.** Заголовок карточки — уровень, а не константа. Карточка под `h1` страницы это элемент второго уровня, карточка внутри секции со своим `h2` — третьего. Жёстко зашитый `h3` давал пропуск уровня на `/kursy/`, `/kierowca-zawodowy/`, `/certyfikaty/` и `/zapisz-sie/`, а пропуск уровня скринридер читает как отсутствующий раздел. По умолчанию 3, то есть прежнее поведение.

**Что добавила v3 и почему.** `FRONTEND.md` расширяет §7, а не переопределяет его, и на четырёх строках это расширение стало обязательным: A.5 требует у бейджа единственный заливной вариант `accent` («Nowy termin»); A.9 п.5 требует секцию жёлтой полосой во всю ширину, а в перечислении `tone` для неё не было имени; F1 п.6 требует у карты высоту пропом; A.7 требует локальный спрайт, а без `<c-icon>` каждый компонент повторял бы одну и ту же разметку `<svg><use>` и один и тот же путь `{% static %}`. Значения перечислений только добавлены — ни одно существующее не изменило смысла.

**Дизайн-токены.** Полная палитра, типографическая шкала, сетка, состояния компонентов и композиция страниц заморожены в `FRONTEND.md` часть A. Ниже — исходный набросок токенов; при расхождении с `FRONTEND.md` A.2 действует `FRONTEND.md`.

```js
brand:  { 900:"#2A1F55", 700:"#3B2D71", 500:"#5B47A8", 100:"#EBE6F8" }
accent: { 500:"#FFD400", 600:"#E0BA00" }   // жёлтый с баннера OSK NAWROCKI
ink:    { 900:"#181328", 700:"#3A3350", 500:"#6B6383" }
paper:  { 0:"#FFFFFF", 50:"#F7F6FA", 100:"#EFEDF4" }
state:  { ok:"#1E7A56", warn:"#B27C00", err:"#B3382B" }
```

Шрифты самохостим: заголовки — condensed grotesque, текст — humanist sans. Конкретные файлы кладёт LEAD в `static/fonts/` и фиксирует в `app.css`.

---

## 8. SEO-контракт

Каждая публичная вьюха обязана отдавать в контекст `seo` — экземпляр `apps.core.seo.Seo`:

```python
@dataclass
class Seo:
    title: str          # ≤ 70 символов, формат "<Тема> — OSK Nawrocki Wieluń"
    description: str    # ≤ 170 символов
    canonical: str      # абсолютный URL
    og_image: str | None = None
    robots: str = "index,follow"
    jsonld: list[dict] = field(default_factory=list)
```

Правила, невыполнение — красный гейт:

- ровно один `<h1>` на страницу;
- `title` содержит «Wieluń» на всех коммерческих страницах;
- `description` не пустой; при пустом поле в БД собирается из `lead` обрезкой до 170;
- `hreflang` на все три языка + `x-default` на PL;
- JSON-LD: `DrivingSchool` (на всех страницах, из `SiteSettings`), `Course` (на страницах курсов), `BreadcrumbList`, `FAQPage` (на `/faq/`), `AggregateRating` — **только** если есть подтверждённые отзывы с `source_url`;
- `sitemap.xml` собирается из `Course`, `Page`, `GalleryImage`(нет), статических роутов; `lastmod` из `updated_at`;
- у каждого `<img>` непустой `alt`; проверяется тестом, который обходит все шаблоны.

---

## 9. Доктрина тестов

Тесты привязаны к слайсу и PR, не к стадии. Слайс мёрджится только с тестами.

**Главное правило: тест выводится из критериев приёмки задачи, а не из реализации.** Тест кодирует контракт. Запрещено писать тест, который просто повторяет то, что делает код, вместе с его багами.

Обязательные типы на каждый слайс:

1. **Контрактный тест на стыке.** Payload задачи Celery валидируется против схемы из §6. Фейковый клиент — это тестовый шов: он валидирует вход и падает, если слайс шлёт мусор. Пример: `tests/contracts/test_lead_notify_payload.py`.
2. **Идемпотентность задачи.** Каждый Celery-хендлер прогоняется дважды с тем же payload, проверяется ровно один эффект (одно письмо в outbox, один рендишен). Без такого теста задача не мёрджится.
3. **Путь ошибки.** Фейковый клиент умеет возвращать 500 и таймаут. Проверяем ретрай, что лид не теряется, что пользователь видит внятное сообщение.
4. **Property-based (hypothesis)** на чистой доменной логике: расчёт возрастного порога (`min_age` + «можно начать за 3 месяца»), форматирование цен, генерация slug, вычисление «открыто сейчас» из `OpeningHours`, обрезка `description` до 170 без разрыва слова.
5. **E2E (Playwright)** на критический путь: главная → страница курса → форма заявки → страница благодарности, с проверкой, что лид создан и письмо ушло в фейковый outbox. Плюс мобильный вьюпорт 390×844.

Дополнительно обязательны:

- тест редиректов: каждый путь из `data/legacy/redirects.csv` отдаёт 301 на существующий URL;
- SEO-тест: обход всех публичных URL, проверка одного `h1`, непустых `title`/`description`, наличия canonical и JSON-LD;
- тест доступности alt: ни один `<img>` в отрендеренных страницах не имеет пустого `alt`;
- тест, что форма без `consent_rodo` не создаёт `Lead`.

Покрытие ниже 80% по `apps/` — гейт красный.

---

## 10. Владение инфраструктурой

| Область | Владелец | Правило |
|---|---|---|
| `tech.md` | LEAD | append-only, бамп версии |
| Миграции | **LEAD** | генерятся из моделей, применяются в деплой-шаге. DEV миграции не пишет вообще |
| `apps/core/**` | LEAD | общие типы, контракты, SEO, навигация, клиенты |
| `templates/cotton/**`, `templates/base.html`, `templates/layout/**` | LEAD | UI-примитивы и каркас |
| `tailwind.config.js`, `static/src/css/app.css` | LEAD | токены |
| `config/**` | LEAD | настройки, celery, urls верхнего уровня |
| `scripts/seed.py` | LEAD | единственный источник фикстур, одинаковых для dev, тестов и фейков |
| `.env.example` | LEAD | все переменные с фиктивными значениями, чтобы проект стартовал без реальных секретов |
| `.github/workflows/**`, `deploy/**` | LEAD | |
| `apps/<фича>/**`, `templates/<фича>/**` | DEV | целиком, сверху донизу |

**Конфиг.** Единый модуль `config/settings/base.py` + `django-environ`. Обязательные переменные в `.env.example`:

```
DJANGO_SECRET_KEY=dev-not-secret
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://osk:osk@db:5432/osk
REDIS_URL=redis://redis:6379/0
MAIL_CLIENT=fake            # fake | smtp
SMS_CLIENT=fake             # fake | smsapi
EMAIL_HOST=  EMAIL_HOST_USER=  EMAIL_HOST_PASSWORD=  EMAIL_PORT=587
SMSAPI_TOKEN=
SENTRY_DSN=
IP_HASH_SALT=dev-salt
MEDIA_ROOT=/app/media
```

Проект обязан подниматься на чистой машине командой `docker compose up` + `make seed` без единого реального секрета.

---

## 11. CONTRACT GAP

Нужного поля, типа, задачи или эндпоинта нет в `tech.md` → **СТОП**. Код с выдуманным контрактом не пишется.

Сессия выдаёт блок ровно в такой форме:

```
CONTRACT GAP
Что нужно: <поле / тип / задача / эндпоинт>
Зачем: <какой критерий приёмки без него не закрывается>
Предлагаемая форма: <точное определение — имя, тип, ограничения, дефолт>
Затрагивает: <модели, задачи, шаблоны>
Временная заглушка: <что делаю локально, пока контракт не приедет>
```

Дальше: issue с меткой `contract-change`, работа продолжается на локальной заглушке. LEAD аппендит контракт в `tech.md`, бампает версию, закрывает issue. DEV подтягивает новую версию ядра.

---

## 12. Конвенция коммитов, PR и комментариев

Применяют все сессии.

**Язык всего технического текста — только английский:** коммиты, заголовки и тела PR, комментарии в коде, docstrings. Пользовательские тексты сайта — польский/русский/украинский.

**Формат коммита фиксированный, всегда** Conventional Commits:

```
type(scope): summary
```

- `type` из закрытого набора: `feat|fix|test|refactor|chore|docs`;
- `scope` — имя приложения или области: `courses`, `leads`, `gallery`, `seo`, `ci`, `ui`;
- `summary` в императиве, со строчной буквы, без точки в конце, до ~50 символов, по делу;
- тело коммита только если надо объяснить **почему**, не **что**.

Примеры: `feat(courses): add intake filter by language`, `fix(leads): keep lead when smtp times out`, `test(gallery): cover rendition idempotency`.

**Сессия коммитит сама по ходу работы**, маленькими логическими коммитами после каждого осмысленного шага. Не сваливать всё одним коммитом в конце. Каждый коммит по возможности проходит `ruff` и `mypy`.

**PR:** заголовок краткий и содержит ID задачи. Тело короткое: что делает слайс, какие контракты и типы затрагивает, чем покрыт тестами. Без простыней.

**Комментарии в коде:** кратко, объясняют **почему**, а не пересказывают очевидный код. Закомментированный код в PR не оставлять.

**Дисциплина письма (`stop-slop`)** на всю прозу: активный залог, императив, конкретика вместо общих фраз, без em-dash, без филлеров, без эмодзи.

---

## 13. Definition of Done одной задачи

Задача закрыта, когда всё зелёное:

- `ruff check` и `ruff format --check` без замечаний;
- `mypy apps/` без ошибок;
- миграции: `makemigrations --check --dry-run` не находит несгенерированных изменений;
- `pytest` зелёный, покрытие ≥ 80%;
- тесты выведены из критериев приёмки задачи, не из реализации;
- для каждой новой Celery-задачи есть тест идемпотентности;
- на стыке слайса есть контрактный тест;
- если слайс добавляет публичную страницу — она проходит SEO-тест и alt-тест;
- `docker compose build` проходит;
- PR привязан к задаче, коммиты по конвенции;
- ревью LEAD пройдено.

---

## 14. Дорожная карта по стадиям

| Стадия | Содержание | Владелец |
|---|---|---|
| **S0** | Скелет: репо, CI, Docker, Postgres, Celery, Tailwind, cotton-примитивы, base/layout/nav, `SiteSettings`, seed, фейковые клиенты, эталонный слайс | LEAD |
| **S1** | Курсы: модель, админка, `/kursy/`, `/kursy/<slug>/`, хаб `/kierowca-zawodowy/`, психотесты, погрузчики. Импорт текстов старого сайта | DEV |
| **S2** | Цены и сроки: `/cennik/`, `/terminy/`, HTMX-фильтр наборов | DEV |
| **S3** | Заявки: форма, HTMX-сабмит, антиспам, RODO-согласие, две Celery-задачи, страница благодарности | DEV |
| **S4** | Контакты: `/kontakt/`, часы работы, Leaflet-карта, sticky-кнопка звонка | DEV |
| **S5** | О школе: `/o-nas/`, инструкторы, автопарк | DEV |
| **S6** | Медиа: галерея, сертификаты с подписями, WebP-пайплайн, лайтбокс | DEV |
| **S7** | Полезные ссылки с описаниями, FAQ, ежедневная проверка ссылок | DEV |
| **S8** | SEO-пакет: JSON-LD, sitemap, robots, 301-редиректы со старых URL, OG-картинки | DEV |
| **S9** | i18n: RU и UK, переключатель, hreflang, посадочная «kursy po rosyjsku» | DEV, сделано в v15 кроме посадочной |
| **S10** | Отзывы, cookie-баннер с категориями, аналитика только после согласия | DEV |
| **S11** | Прод: домен, HTTPS через Caddy, бэкапы, Sentry, Search Console, финальный прогон Lighthouse | LEAD |

---

## 15. Наследие старого сайта

Тексты старого сайта выгружены и лежат в `data/legacy/` в виде markdown-файлов по одному на страницу, плюс `redirects.csv` и `links.csv`. Импортируются `scripts/import_legacy.py` в `Course.entitlements` / `Course.requirements` / `Page.body`.

При импорте обязательно исправить опечатки исходника:

| Было | Стало |
|---|---|
| `Szkolnie okresowe` | `Szkolenia okresowe` |
| `Jesteśmy firma rodzinną` | `Jesteśmy firmą rodzinną` |
| `otrzymuja` | `otrzymują` |
| `prowadzane` | `prowadzone` |
| `Pracowania czynna` | `Pracownia czynna` |

Два фрагмента исходника не удалось считать целиком, помечены `[…]` — дописать вручную при импорте: хвост первого пункта в `kat-a2` и возрастной диапазон кат. D в `kwalifikacja-wstepna-przyspieszona`.

Медиа старого сайта: 27 фото галереи, 11 сканов сертификатов, 4 слайда баннера, 1 фото авто. Оригиналы запрашиваем у владельца, с сайта тянем только как запасной вариант. Все изображения перед заливкой прогоняются через `scripts/optimize_media.py`.

`UsefulLink` на старте наполняется 9 ссылками старого сайта плюс тремя новыми: проверка штрафных баллов на `gov.pl`, Starostwo Powiatowe w Wieluniu (там выдают PKK), Wydział Komunikacji. Ссылка `info-car.pl/new/` заменяется на `https://info-car.pl/`. Каждая ссылка обязана иметь `description`.

---

## 16. Данные, которых нет и которые блокируют контент

Разработку не блокируют: сид заполняет правдоподобными заглушками, помеченными `TODO_OWNER`. Публикацию прода блокируют.

- цены по всем 15 курсам и услугам;
- часы работы офиса (известны только часы кабинета психотестов: вторник и пятница 8:00–16:00);
- даты стартов ближайших наборов;
- часы теории и практики по кат. B и остальным категориям;
- расшифровка 11 сертификатов;
- оригиналы фотографий;
- список машин: марка, модель, год, коробка;
- инструкторы: имена, стаж, фото;
- ссылки на профиль Google и Facebook;
- на каких именно курсах занятия идут на русском.

Сид помечает такие поля так, чтобы `pytest -m owner_data` показывал список незаполненного. Прод не выкатывается, пока список не пуст.

---

## 17. CI/CD

Два раздельных пайплайна GitHub Actions.

**Гейт на PR — `.github/workflows/ci.yml`, без деплоя.** Сервисы: `postgres:16`, `redis:7`.

```
ruff check
ruff format --check
mypy apps/
python manage.py makemigrations --check --dry-run
pytest -q --cov=apps --cov-fail-under=80
playwright e2e на собранном образе
docker build
```

**Деплой на мёрдж в `main` — `.github/workflows/deploy.yml`.**

```
build image → push в registry → ssh на VPS
→ docker compose pull && docker compose up -d
→ python manage.py migrate           (отдельный шаг, до старта нового контейнера)
→ python manage.py collectstatic --noinput
→ smoke: GET /healthz == 200
```

`/healthz` проверяет доступность БД и Redis и отдаёт 200 только при обоих живых.

**Branch protection на `main`:** только через PR, мёрдж при зелёном CI, линейная история. Прямой push в `main` запрещён.

---

## 18. CODEOWNERS и защита общих файлов

Правило «не трогай общие файлы» держит платформа, а не добрая воля сессии. Даже когда разработчик один, CODEOWNERS не даёт DEV-сессии молча уехать в контракты.

```
tech.md                     @lead
/config/**                  @lead
/apps/core/**               @lead
/templates/cotton/**        @lead
/templates/base.html        @lead
/templates/layout/**        @lead
/tailwind.config.js         @lead
/scripts/seed.py            @lead
/**/migrations/**           @lead
/.github/**                 @lead
/deploy/**                  @lead
```

**Миграции.** Генерируются только в режиме LEAD, только из моделей: `makemigrations <app>`. Одна миграция на один смысловой шаг, имя осмысленное (`0004_course_add_languages`). `RunPython` всегда с `reverse_code`, минимум `noop`. Data-миграции нужны для: редиректов из `redirects.csv`, начального `SiteSettings`, изменений набора `Course.languages`. В PR-гейте миграции прогоняются на эфемерном Postgres, в деплое применяются отдельным шагом. Файл миграции в PR от DEV-сессии — повод развернуть PR.

---

## 19. Прод: Caddy и HTTPS

`deploy/Caddyfile`. Один канонический хост, всё остальное 301. Сертификат Let's Encrypt берётся автоматически — это закрывает главную поломку старого сайта.

```
naukajazdywielun.pl, www.naukajazdywielun.pl {
    redir https://naukajazdywielun.pl{uri} permanent
}
naukajazdywielun.pl {
    encode zstd gzip
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options nosniff
        Referrer-Policy same-origin
    }
    handle_path /static/* { root * /srv/static; file_server }
    handle_path /media/*  { root * /srv/media;  file_server }
    reverse_proxy web:8000
}
```

`config/settings/prod.py`: `SECURE_SSL_REDIRECT=True`, `SECURE_HSTS_SECONDS=31536000`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `X_FRAME_OPTIONS=DENY`, `SECURE_REFERRER_POLICY="same-origin"`, CSP без внешних хостов.

Бэкапы: `core.tasks.db_backup` ежедневно в 02:00, `pg_dump` в `deploy/backups/`, ротация 14 дней. Восстановление проверяется вручную один раз перед переездом домена.

---

## 20. Long-lead

Внешние вещи, которые тянутся неделями. **Блокируют интеграцию и публикацию, не блокируют разработку** — она идёт против фейков с первого дня. Запросить в день один.

| Что | Зачем | Кто даёт |
|---|---|---|
| Доступ к DNS `naukajazdywielun.pl` | переключить A-запись, выпустить сертификат | владелец / текущий хостер |
| Почтовый ящик или SMTP-доступ | уведомления о заявках | владелец |
| Аккаунт SMSAPI.pl (опционально) | SMS о заявке | владелец |
| Доступ к Google Business Profile | отзывы, карта, локальный поиск | владелец |
| Google Search Console | подтверждение домена, sitemap, контроль переезда | режим LEAD после переключения DNS |
| Оригиналы фото и сканов сертификатов | галерея, сертификаты | владелец |
| Цены, часы работы, даты стартов | блокируют публикацию прода | владелец |

Пока их нет: `MAIL_CLIENT=fake`, `SMS_CLIENT=fake`, тестовый поддомен, контент из сида с пометкой `TODO_OWNER`.
