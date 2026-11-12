# Agentix: состояние и продолжение работы

Обновлено **12 ноября 2026**. Краткая точка входа; подробное evidence хранится
в owning документах, а не в этой памятке.

## Репозитории и правила

`agentix-skill` содержит общий плагин Codex/Claude Code. Сервис и веб-приложение —
в `../agentix`. Оба checkout сейчас на локальной ветке `codex/architecture-hardening`.
До правок читать [AGENTS.md](../AGENTS.md), проверять status и diff; WIP сохранять.

| Где | Назначение |
|---|---|
| [README](../README.md) | Установка, проверки, opt-in updater |
| [Общий skill](../skills/agentix/SKILL.md) | Поведение агента и discovery возможностей сервера |
| `.claude-plugin/`, `.codex-plugin/`, `.agents/plugins/` | Manifests/marketplace |
| `hooks/hooks.json`, `scripts/auto-update.sh`, `scripts/auto-update.py` | Host-aware opt-in update, lock/deadline |
| `contracts/agentix-contract*.json` | Три поддерживаемых inventory/compat fixtures |
| `contracts/agentix-schema-contract-v1.json` | Новая локальная field-schema projection; ещё не release |
| `scripts/verify-contract.py`, `scripts/test_*.py` | Static/live compatibility и offline mocks |
| `.github/workflows/validate-plugin.yml` | Package CI и scheduled public probe |

Три прежних snapshots сохраняются. Live MCP schemas и `/api/docs` владеют сервисным
контрактом; fixtures не переписываются ради зелёного probe. Credentials вне пакета.
Один shared skill и opt-in updates сохраняются. Node/DB не нужны пользователю плагина;
optional updater использует Python 3/POSIX. Software license плагина пока не выбрана.

## Релиз 0.6.0 (12 ноября 2026)

Plugin **0.6.0** выпущен: main, tag `agentix--v0.6.0`, marketplace `kyzdes/claude-skills`.
Skill описывает аудит-фиксы сервиса `68c5855` и `28f3226` (ветка `audit-fixes`): cursor у
activity/inbox, `project` для документов с общим slug, необязательный `expectedRevision`
у project/epic/milestone, результат `unlink_issues`, лимиты 200. Schema snapshot v1
пересобран из `lib/schemas/schema-contract.ts` сервиса на `28f3226` (zod 4 изменил
сериализацию uuid/integer). Production 12 ноября всё ещё `eb894513`: public REST probe
PASS, schemaContract там нет, authenticated MCP не проверялся. Разделы ниже — история
до этого релиза; «push/release не выполнялись» относится к состоянию на 4 октября.

## Аудит, план и локальные изменения

- [Архитектурный отчёт](../../agentix/docs/reviews/2026-10-03/architecture-review.md):
  исходный snapshot,22 находки, источники и уровни уверенности.
- [Канонический план W0–W6 и очередь E1–E8](../../agentix/docs/reviews/2026-10-03/improvement-plan.md):
  зависимости, приёмка, критерии остановки и три продуктовых цикла.
- [Проверки и статус](../../agentix/docs/reviews/2026-10-03/verification.md):
  свежие результаты отдельно от прошлых checkpoint и release evidence.

Исходная база: service `eb894513ceaec3b6fd9d0a0453f8aaaf873bcbe8`, plugin
`2441cb4e8d14194d06251a4a77a7131f59009538`. Released plugin **0.5.0**;
versions/tags не менялись. Исходный README и untracked AGENTS/docs WIP сохранены.
Предыдущие локальные commits: service `c0cbfd3`, plugin `c48918b`;
comments checkpoint: service `b740d94`, plugin `1e5477f`.
E1/E2/E3 checkpoint: service `1ef9831`, plugin `ba41257`. Push/release не выполнялись.

Предыдущие пакеты исправили safe errors до Next stderr, document ambiguity/final
scope, draft/baseRevision, input/MCP guards, schema projection, opt-in updater,
document/history/backlink pagination, parent-cycle/blockers/auth lock order,
generic maintenance без mail keys. Comments detail теперь latest20 с cursor pages
20/max200; UI сохраняет draft, явно сбрасывает историю при changed snapshot.

Завершённая локальная волна E1/E2/E3: issue writes выбирают card/spec/parentId без nested history;
complete возвращает собственный report, link — relationId. Старые ledger results
повторяются точно после текущей auth; unlink не заставляет link replay создавать связь
снова. Capability issueMutationResultsVersion:1, REST/MCP/skill обновлены вместе.
Legacy getIssue и final activation read сохранены. Linear UI честно описывает add-only
import; changed-upstream regression защищает существующие fields/local edits.
Projection по-прежнему7REST/6MCP плюс reader/write capabilities; inventory47tools/70ops.
Candidate contract ещё не выпущен; не все22 находки закрыты.

Проверки используют свой loopback PostgreSQL и synthetic accounts/fake provider.
Свежий DB aggregate732 PASS +2 opt-in benchmarks skipped; tsc/build/worker/lint PASS,
plugin16 offline/static/shell PASS. Browser32 уникальных сценария (31 aggregate +2 targeted),
HTTP7 и strict REST/authenticated MCP probe PASS. Свои servers/БД остановлены.
Mutation benchmark3×20: large edit result1904308→4872B, SQL полного write→refresh34→31,
p50 43.396–46.371→22.502–26.226ms. Refresh не вырос, small speedup не доказан;
JSON bytes отличаются от pg_column_size и общего disk usage. Все границы в verification.

## Подтверждённое production и историческое evidence

3 октября во время исходного audit public health вернул HTTP 200, database ready,
release `agentix-beta-release-eb894513ceae`, ту же revision, provenance image.
Публичный REST inventory/enums probe прошёл: 70 операций. Авторизованный production MCP
в локальных волнах не проверялся; 47 tools/17 read-only — snapshot и прежнее release evidence.
Эти результаты не подтверждают публикацию текущих локальных patches.

Remote main/tag plugin совпадали 2 октября; сейчас remote refs не обновлялись.
Результат 2 октября по почте: Gmail принял письмо в Спам, SPF/DKIM/DMARC PASS,
callback в БД. Inbox/outbox/recovery этим не доказаны.

| Источник | Когда нужен |
|---|---|
| `../agentix/ARCHITECTURE.md`, `SECURITY.md`, `README.md` | Архитектура, границы доступа, runtime |
| `../agentix/docs/operations/release-runbook.md` | Candidate/release gates |
| `../agentix/docs/operations/restore-drill.md` | Restore и миграции |
| `../agentix/docs/implementation/activation.md` | Первый результат агента |
| `../agentix/docs/implementation/verified-email.md` | Mail lifecycle |
| `../agentix-release-evidence/2026-09-25-eb894513/release-evidence.md` | Предыдущий release |
| `../agentix-release-evidence/2026-10-02-resend/resend-status.md` | Mail evidence/ограничения |

## Продолжение

Сначала status/diff и верхний раздел verification. E1/E2/E3 завершены локально.
Следующий пакет E4: доступ к completion report старше последних20;
E5: один activity/inbox reader; E6: wiki lifecycle; E7: planning revisions. E8 candidate
можно готовить для ограниченного scope после E3; весь аудит до этого закрывать не нужно.
У каждого пакета есть зависимости и stop criteria в едином плане. Schema/API migrations
не начинать поверх непроверенного diff. Service/plugin имеют отдельные versions и
validation; контрактные изменения требуют согласованной миграции consumers.

Resend integration **приостановлена пользователем**. Новых писем, sender/credential
switch, signup/delivery-ready toggles и production deployment в этой работе нет.
При возобновлении нужны свежая outbox/domain проверка, разрешённые адресаты и реальные
Inbox/outbox/recovery gates, два независимых Codex/Claude pilot цикла и observation.
Snapshot flags 2 октября: ALLOW_SIGNUP=0, MAIL_ENABLED=1, MAIL_DELIVERY_READY=0;
перед действиями проверить заново. Пауза разработки не означает остановку worker.

Обновлять эту памятку заменой устаревших утверждений, сохранять менее 120 строк.
Не создавать параллельные MEMORY/CONTEXT/TODO с пересказом диалога.
