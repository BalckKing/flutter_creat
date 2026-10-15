---
name: ios-app-listing
description: Use when the user wants App Store listing copy, review-site pages, privacy or legal pages, or a regenerated AppListing for an iOS app. Applies to both Flutter iOS apps and native Swift iOS apps, especially reskin projects that need evidence-based capability classification and conditional AI privacy disclosures.
---

# iOS App Listing

Generate `AppListing/` for iOS apps from project facts, not guesswork.
This skill is the default listing workflow for both Flutter and Swift app roots.

Read these first:
- `references/output-contract.md`
- `references/privacy-ai-rules.md`

Use the local renderer in `scripts/render_app_listing.py` and the generator pipeline in `scripts/generate_app_listing.py` to produce `AppListing/site/*.html`.
Presentation must stay inside this repository's non-interactive render pipeline; output shape, factual claims, legal obligations, and AI privacy requirements stay owned by this skill.

## Output Contract

Default output must be exactly:

```text
AppListing/
  Intro.md
  site/
    index.html
    img/
      logo.png
    PrivacyPolicy.html
    Terms&Conditions.html
    Support.html
```

Do not add extra files unless the user explicitly asks for them.
Path names are fixed and downstream-dependent; keep exact casing and punctuation, especially `Terms&Conditions.html`.

## Workflow

### 1. Resolve the app root

If the user gives a directory, use it.
If not:
- prefer a directory containing `pubspec.yaml`
- otherwise prefer a directory containing `.xcodeproj`, `Info.plist`, or `Package.swift`

### 2. Inspect the app

Run:

```bash
python3 scripts/inspect_app.py --target /abs/path/to/app > /tmp/app_inspect.json
```

This unified inspector:
- detects `source_stack = flutter|swift`
- extracts app identity, permissions, dependencies, code evidence, brand colors, logo candidates
- extracts `iap_codes`
- computes `capability_candidates`
- computes `privacy_signals`
- computes `ai_signals`
- computes `access_signals`

Do not write listing copy before inspecting the app.

### 2.1 Interpret AI signals

Treat `ai_signals` as a layered result, not a single yes/no flag.

Current meaning:
- `active` / `code_present`: AI code evidence exists in the project
- `route_registered`, `navigation_invoked`, `entry_surface_visible`: structural entry evidence
- `claimable` / `disclosure_required`: the main downstream judgment for listing claims and AI legal copy

Current relaxed rule:
- if AI code exists and any structural signal exists, treat the app as having AI for downstream listing and legal handling
- tab-mounted AI pages count as structural entry evidence
- direct route registration, route jumps, and visible entry surfaces also count
- an explicit runtime-disabled signal can still suppress `claimable` and `disclosure_required`

Auxiliary labels:
- `runtime_enabled`: runtime disable guard, not standalone product-entry proof
- `auth_gated`: login gate detected around the AI flow
- `paywall_gated`: purchase, credits, or payment gate detected around the AI flow
- `residual_code`: AI code evidence exists but no structural entry was found

Do not use AI-facing copy differences alone to decide whether the app has AI.
Do not use `ai_signals.active = true` by itself as the trigger for AI legal copy.

### 2.2 Interpret access signals

Treat `access_signals` as the access-model source of truth for listing, legal, and review-note wording.

Modes:
- `credential_account`: inspect evidence supports real credential authentication
- `local_session`: inspect evidence supports local quick entry or saved-session behavior without credential auth
- `community_only`: inspect evidence supports profile/feed/post/community behavior without credential auth
- `neutral`: no strong access model was proven

Hard rules:
- do not infer `credential_account` from `profile`, `feed`, `post_creation`, `following`, logout routes, session stores, or community vocabulary alone
- do not default About, Support, Privacy, Terms, App Store description, or review notes to `account`, `register`, `log in`, `sign in`, `username`, `password`, or `User Accounts` wording unless `access_signals.mode = credential_account`
- when `access_signals.mode != credential_account`, prefer `profile`, `community`, `member`, `saved preferences`, `saved details`, `service access`, or `repeat-use state` wording
- in Privacy, distinguish private profile details from public/community content and from credentials/authentication; only add credential-authentication sections when inspect evidence supports them
- in Terms, keep the account chapter conditional; do not treat `User Accounts` as a default UGC requirement
- in Support, make FAQ items capability-driven; do not inject account-oriented FAQ by default

### 2.3 Repository boundaries

The skill must treat the current app as a normal, reviewable app and must not rely on `package` or `packages` directories as evidence sources.

Hard rules:
- never add, delete, rename, or modify any directory named `package` or `packages`, or any file under those directories
- never run formatters, generators, installers, migrations, or any write-producing command inside `package` or `packages`
- never use files under `package` or `packages` as listing evidence, review evidence, logo candidates, support-email sources, or URL sources
- when inspecting code, skip `package` and `packages` directories entirely and continue with first-party app code only

### 3. Classify category and claimable features

Build AI-facing classification input:

```bash
python3 scripts/classify_app_listing.py --inspect-json /tmp/app_inspect.json > /tmp/app_classification_input.json
```

Produce a three-layer classification JSON with exactly:

```json
{
  "category": "...",
  "archetype": "...",
  "theme": "...",
  "theme_hint": {
    "identity": "...",
    "experience": "...",
    "keywords": ["..."],
    "currency": "...",
    "index_title_suffix": "...",
    "social_noun": "...",
    "post_label": "..."
  },
  "capabilities": ["..."],
  "claimable_features": ["..."],
  "confidence": "low|medium|high",
  "reasoning": "..."
}
```

Then validate it:

```bash
python3 scripts/validate_app_listing_classification.py --evidence-json /tmp/app_inspect.json --classification-json /tmp/app_classification.json
```

Rules:
- category must come from evidence, not app name or folder naming
- archetype should summarize the product's primary shape, such as community social, travel companion, photo-led, or utility
- theme should summarize the vertical subject or audience focus using inspected evidence, review notes, and first-party product copy
- `theme_hint` is AI-authored writing input for the generator; do not hardcode it in the script for one specific app
- only claim supported features
- when `access_signals.mode != credential_account`, keep classification reasoning and theme-writing inputs free of strong account/login wording
- use a support email only when explicitly confirmed in first-party project information; never invent `support@<slug>.com`

### 4. Write AppListing files

Use the inspected facts, validated classification, and output contract to write:
- `AppListing/Intro.md`
- `AppListing/site/index.html`
- `AppListing/site/PrivacyPolicy.html`
- `AppListing/site/Terms&Conditions.html`
- `AppListing/site/Support.html`

Default writing path:
- resolve the routed description style first with `python3 scripts/generate_app_listing.py --target /abs/path/to/app --select-description-style`
- have the current agent author a JSON file such as `/tmp/app_listing_authoring.json`
- pass that file into `python3 scripts/generate_app_listing.py --target /abs/path/to/app --authoring-json /tmp/app_listing_authoring.json`
- the JSON should contain at least `description`
- when the selector returns a style, write the `description` to match that format and set `description_style_label` to the same style
- it should usually also contain `brand_overview`, `index_subtitle`, `purpose`, and `members_intro`
- it may contain `onboarding` with English `tagline`, `cta_label`, `cards`, and `template_id`
- it must contain reviewed `legal` facts when the legal-facts gate reports unknown or conflicting material facts

Minimal example:

```json
{
  "description": "AppName is ...",
  "description_style_label": "members_first",
  "brand_overview": "A ... community for ...",
  "index_subtitle": "An evidence-based overview of ...",
  "purpose": "AppName is ...",
  "members_intro": "Members can ..."
}
```

Copy rules:
- if `access_signals.mode != credential_account`, do not default generated copy to `account`, `register`, `log in`, `sign in`, `credentials`, `username`, or `password`
- profile/community apps may describe profiles, posts, feeds, following, saved context, moderation, and repeat visits without implying a full external account system
- local quick-entry or saved-session apps should read like lightweight repeat-use products, not credential-login products

`AppListing/site/index.html` is a standalone, self-contained app launch guide. It uses one of the templates in `assets/site-render/onboarding-templates-manifest.json`, contains no cross-page navigation, and preserves the required Continue bridge. Privacy, Terms, and Support pages are independently readable and do not link to one another.

All four HTML pages must be complete, polished, independently readable user-facing pages, not work-in-progress previews. Never expose page-state labels such as `Draft`, `WIP`, `TBD`, `TODO`, `Placeholder`, `Pending confirmation`, or `Coming soon`, bracketed fill-in fields, author notes, or unfinished section labels in rendered text, page titles, descriptions, image alternative text, or accessibility labels. A real product feature may use a similar word only when supported by project facts; never use it to label page status. Do not use a polished layout to disguise empty, generic, or unsubstantiated legal copy.

The onboarding manifest currently contains five independent templates: `onboarding-cards`, `onboarding-spotlight`, `onboarding-compact`, `onboarding-minimal`, and `onboarding-feature-list`. Unless `--onboarding-template-id` is explicitly supplied, generation randomly selects one template per execution. Template selection changes layout only; visible product claims always come from the inspected `project_profile` and confirmed facts.

Onboarding templates show pagination dots and the primary Continue action, without visible Pause/Play controls. Legal and support page templates must not add generic filler instructions such as "Review the information on this page."

The inspector also produces an evidence-backed `project_profile` with confirmed or candidate product features. Do not treat a field name, isolated example sentence, dependency, or generic capability keyword as a confirmed product feature. Use the profile to keep onboarding and site overview copy specific to the target project.

Never fill missing legal facts with generic assumptions. The generator reports unknowns and keeps them in the run summary for follow-up; missing facts do not block local HTML generation, but they remain internal review items and must not appear as page placeholders. If no confirmed support email exists, omit email/contact sections rather than render a guessed address or `None`. Keep public legal review marked incomplete while required operator, jurisdiction, audience, retention, contact, or network-recipient facts remain unresolved; do not describe the pages as ready for public legal publication. See `references/output-contract.md` for the legal facts schema and conditional clauses.

### 4.1 Workflow-safe execution

This skill must be safe to run inside unattended workflows.

### 4.1.1 Skill ownership

When `ios-app-listing` is explicitly invoked, this skill owns the run.

Default mode:
- if the user explicitly asks for `plan only`, `方案`, `先出方案`, `不执行`, `只分析`, or `只评审`, provide the requested plan or analysis without changing files
- otherwise default to direct execution and complete the full local workflow without waiting for a second approval message

Ownership rules:
- do not hand control to `brainstorming`, `frontend-design`, visual companions, browser helpers, or other interactive helper skills for normal AppListing generation
- do not convert a standard generate-and-deploy request into a separate design-confirmation or brainstorming phase
- if the user first asks for a plan and later says `执行`, `继续`, `发布出去`, or equivalent, resume direct execution immediately and do not ask `是否按这个方案执行`
- treat the default About deployment flow as the standard deployment target unless the user explicitly names a different target; do not stop to ask which target to use
- if the default sub-domain lookup fails, times out, or returns an unusable host, continue with placeholder URLs and finish the run without asking the user for another domain

Hard rules:
- do not ask to open a browser, local URL, preview tab, or visual helper surface
- do not require any click-to-continue confirmation for mockups, diagrams, comparisons, or screenshots
- do not depend on `frontend-design` or any external interactive design helper to produce final `site/*.html`
- do not pause for manual HTML preview when the local render + validator pipeline can continue
- generate, validate, and deploy using repository-local scripts only

External media failures are scoped to the affected media check. A failed Logo
request, an HTML response from the Logo UI, a blocked image host, a timeout, or
missing licence evidence must be recorded in the run summary, but must not stop
local `Intro.md`, the four HTML pages, `AppListing/`, directory normalization,
or downstream Review Remarks generation. Keep the affected item `Blocked` or
`Not verified`; never turn a fallback into a claim that the official asset
passed.

If a client offers optional browser-based assistance, decline it implicitly and continue with the repository-local path.

### 4.2 App Integration Boundaries

In this skill, `deploy about` means publishing the remote `AppListing/site/*.html` pages. It does not mean expanding an in-app About screen.

Hard rules:
- unless the user explicitly asks for app-side exposure, do not add app UI or app logic just to surface generated `index.html` or `Support.html`
- source sync is replacement-only for existing first-party listing/legal URL config under `lib/` or `ios/`
- do not create new constants, launch helpers, routes, controller methods, menu items, rows, labels, or sections for deployed listing pages
- if the app already has Terms or Privacy entry points, only update those existing URLs by default
- generating `AppListing/site/index.html` and `AppListing/site/Support.html` does not by itself justify adding in-app entry points for them

Forbidden examples:
- do not add `guideOpenAboutSite()` or `guideOpenSupportPage()`
- do not add `overviewSite` or `overviewSupport` copy constants
- do not insert new About rows just because `Support.html` or `index.html` was generated

`Intro.md` must include these sections in order and with exactly these names:
- `# App Name — App Store Description`
- `## App Name`
- `## Sub Title`
- `## Category`
- `## Description`
- `## Keywords`
- `## Support URL`
- `## Terms of Service URL`
- `## All URL`
- `## UGC`
- `## Chat`
- `## Copyright`

Use the fixed heading structure from `docs/intro.md`; do not add, remove, or rename headings.

`Sub Title` must be exactly two Title Case words joined by ` & `.
The two words must be abstract mood, lifestyle, energy, or social-atmosphere words rather than literal feature words.
Prefer phrases such as `Life & Fashion`, `Style & Vibes`, `Glow & Mood`, `Charm & Joy`, or similarly broad entertainment-facing language.
Do not use literal modality, tool, or object words in the subtitle such as `Chat`, `Call`, `AI`, `Bag`, `Preview`, `Notes`, or other concrete feature labels.
`Video` is the only allowed exception, and only when inspected evidence clearly supports a video-centered product identity.
The subtitle should feel like a reskinned entertainment, social, or lifestyle brand line, not a direct feature summary.
If the current agent does not provide `subtitle`, the generator assigns one from a fixed 50-entry abstract subtitle pool using global ordered rotation; it no longer derives the subtitle from the app slug.

`Category` must use a concise App Store category label derived from the validated classification category, such as `社交 (Social Networking)` or `天气 (Weather)`.
Do not include long descriptive text after the category label.

`All URL` must be a fixed block with this exact line structure:
- top border `==================================================`
- `首页: <index url>`
- `隐私政策: <privacy url>`
- `用户协议: <terms url>`
- `Support: <support url>`
- bottom border `==================================================`

`用户协议` must exactly match `## Terms of Service URL`.
`Support` must exactly match `## Support URL`.

`## UGC` must be exactly `Yes` or `No`.
Set it to `Yes` only when inspected evidence supports public or community user-generated content such as feeds, posts, publishing, or publicly visible user-authored profiles. A private editable profile, journal, note, photo collection, or saved preference does not qualify by itself.
Do not set `UGC` to `Yes` for direct messaging alone.

`## Chat` must be exactly `Yes` or `No`.
Set it to `Yes` only when inspected evidence supports user-to-user messaging, inbox, threads, or chat conversations.
Do not set `Chat` to `Yes` for AI assistant chat alone.

`Description` must use exactly one selected style from the allowed pool on each generation.
Do not let the current agent freely pick a style from the full list.
Instead:
- derive a candidate style pool from inspected app signals such as category, UGC, chat, IAP, translation, and AI-review risk
- rotate through that candidate pool in order on each new generation run: first style, then second style, then third style, and loop back to the first
- if the current agent first resolves a style with `--select-description-style`, reuse that exact style in `description_style_label` when passing authored copy into the generator
By default, the current agent should write the final `Description` and related overview copy directly from inspected app facts, then pass that authored copy into `scripts/generate_app_listing.py --authoring-json /tmp/app_listing_authoring.json`.
Normal generation must not depend on any external AI provider, model selection, rewrite prompt adapter, or API key. Treat the script's local description generator as a compatibility fallback rather than the default skill path.

Available description styles:
- `concise`: two short direct sentences that explain the app quickly
- `feature_3`: one overview sentence followed by exactly 3 concise feature bullets
- `feature_4`: one overview sentence followed by exactly 4 concise feature bullets
- `feature_5`: two overview sentences followed by `With {AppName}, you can:`, exactly 5 concise feature bullets, and one short closing sentence
- `benefit_3`: one overview sentence followed by exactly 3 user-benefit bullets
- `benefit_4`: one overview sentence followed by exactly 4 user-benefit bullets
- `longform`: a clear opening summary sentence followed by 3 supporting sentences and a closing sentence, with paragraph breaks when appropriate
- `summary_plus_feature_3`: one overview sentence, a `Highlights:` line, and exactly 3 concise feature bullets
- `summary_plus_benefit_3`: one overview sentence, a `Why People Return:` line, and exactly 3 user-benefit bullets
- `community_then_purchase`: one overview sentence, an `Inside {AppName}:` line, exactly 3 community-or-purchase bullets, and one short closing sentence
- `feature_then_value`: one overview sentence, `With {AppName}, you can:`, exactly 2 feature bullets, `Why It Feels Easy:`, exactly 2 benefit bullets, and one short closing sentence
- `you_can_3`: one overview sentence, `With {AppName}, you can:`, exactly 3 concise bullets, and one short closing sentence
- `you_can_4`: one overview sentence, `With {AppName}, you can:`, exactly 4 concise bullets, and one short closing sentence
- `why_choose_3`: one overview sentence followed by exactly 3 benefit-led bullets explaining why people use the app
- `homebase_4`: one overview sentence followed by exactly 4 bullets describing how the app keeps the core experience in one place
- `all_in_one`: 2 to 3 sentences that frame the app as a clear all-in-one place for the core experience
- `members_first`: 2 to 3 sentences that foreground members, profiles, posts, and community participation in a grounded way
- `everyday_use`: 3 sentences describing how the app stays easy to reuse across ordinary repeat visits

For every description style:
- keep the copy broad and consumer-facing instead of overly specific
- describe the overall experience, vibe, expression, connection, or entertainment feeling before detailed mechanics
- avoid turning the description into a technical walkthrough or a dense capability list
- for non-`feature_3`, non-`feature_4`, and non-`feature_5` styles, avoid explicit low-level wording such as `video chat`, `1v1 call`, `preview flow`, `try-on pipeline`, or similar literal implementation terms unless accuracy absolutely requires it
- even in `feature_3`, `feature_4`, and `feature_5`, keep the bullets high-level and product-facing rather than mechanical
- do not invent unsupported claims; keep the writing aligned with inspected evidence
- the first 255 characters should explain the app clearly in broad consumer language
- if IAP exists, mention the purchase or virtual goods context naturally in the description
- if `UGC = Yes`, the description should naturally reflect community, publishing, public profile, post, or sharing behavior
- if `Chat = Yes`, the description should naturally reflect messaging or conversation behavior
- if `Chat = No`, the description must not imply in-app user messaging

`Support URL` and `Terms of Service URL` must be full `https://...` URLs.
Always use the placeholder host `https://xxx.xxx.xxx/...` in `## Support URL`, `## Terms of Service URL`, and `## All URL`.
By default, the run keeps the placeholder URLs during generation, then rewrites those Intro URLs to the real published host after the About deployment succeeds. Use `--no-deploy-about` only when you intentionally want a local-only output.

When AppDevOps-Runner sets `IOS_APP_LISTING_RESULT_PATH`, write the Runner result envelope
documented in `references/output-contract.md` in addition to the normal stdout output. Keep the
raw About deployment status (`succeeded`, `skipped`, or `failed`) and any `failures` in that
envelope; do not convert deployment details into a new status model.
Treat the About deployment task status `succeeded` as the deployment success condition. Do not wait for CDN/static propagation and do not block on probing `index.html`, `PrivacyPolicy.html`, `Terms&Conditions.html`, or `Support.html` HTTP status before rewriting Intro URLs.
After the About deployment succeeds and Intro rewrite validation passes, the skill should also sync project-source listing URLs under first-party `lib/` and `ios/` files.
Default sync behavior:
- replace exact full listing URLs for `index.html`, `PrivacyPolicy.html`, `Terms&Conditions.html`, and `Support.html`
- allow old-host fallback replacement only in legal/listing config files under `lib/` or `ios/`
- treat project sync as replacement-only; never expand app UI or behavior to expose newly generated listing pages
- if the app has no existing `Support` or `index.html` entry point, keep those pages as deployed listing artifacts only unless the user explicitly asks for app-side exposure
- never rewrite `package` or `packages` content
- use `--no-sync-project-listing-urls` to disable this source sync when needed
`Copyright` must use a real rights line.

### 5. Copy logo

Copy the best logo candidate to:

```text
AppListing/site/img/logo.png
```

Accept only a decodable raster image with a real image signature. The HTML
route at `http://stargate.local:3100/image` is a generation interface, not a
download endpoint: never save its HTML, JSON, error page, or page source as
`logo.png`. Prefer the verified `assets/logo.png`, then
`ios/Runner/assets/logo.png`, then a valid existing AppIcon image. If the
Stargate request failed or returned non-image data, keep the official Logo and
palette state `Blocked` and record the response; when a valid existing AppIcon
or an explicitly marked `unverified` development brand source is available,
use it only to keep local HTML and review-material generation moving. Preserve
that provenance in the run summary and do not describe it as the approved
brand. If no valid image exists at all, report `required_logo_missing` while
continuing every independent local step that does not require the copied image;
never fabricate a successful Logo or silently copy HTML.

After copying, validate the output signature and decodability again. A valid
`AppListing/site/img/logo.png` is required for the normal whitelist, but its
provenance and any unresolved external Logo failure remain internal delivery
state rather than a reason to abandon `AppListing/`, `aduit/`, or
`aduit/review/remarks.md`.

When no valid image exists, the generator still writes Intro and the four
HTML pages, leaves `img/` empty, and reports `required_logo_missing` in
`media_review_errors`. The missing required image remains a contract failure
in `failures` and can produce a nonzero exit; `local_generation_complete`
describes written Intro/HTML only. Consume the summary and actual files
before continuing downstream work instead of using a single shell `&&` chain
to suppress directory normalization and factual Review Remarks. Do not claim
the normal whitelist or publication check passed with a missing image.

### 6. Enforce AI privacy policy rules when needed

If `/tmp/app_inspect.json` reports `ai_signals.disclosure_required = true`, the privacy policy must satisfy `references/privacy-ai-rules.md`.
Do not trigger AI legal copy from `ai_signals.active` alone, because `active` only means AI code evidence exists.
If `/tmp/app_inspect.json` reports `ai_signals.disclosure_required = false`, user-facing AppListing copy must not introduce `AI`, `AI Preview`, `assistant`, or similar AI-feature wording.

If `/tmp/app_inspect.json` reports `ai_signals.review_profile.needs_face_data_clauses = true`, treat the app as a high-risk AI Preview / face-data review case and do all of the following before shipping:
- `Intro.md`: within the first 255 characters, clearly explain that the app has an AI Preview flow where the user can choose a photo, generate a preview, review the result, optionally save it to Photos, and use credits or purchases if applicable
- `site/index.html`: include a dedicated AI Preview module that explains selected photo + consent + generated preview + optional save to Photos
- `site/PrivacyPolicy.html`: add dedicated face-data / AI Preview sections that clearly state what is collected, what it is used for, who receives it, where it is processed or stored, how long it is retained, and how it is deleted; explicitly state that it is not used for identity verification, face recognition, or biometric profiling
- `site/Terms&Conditions.html`: add an AI Preview use-limits section that states the feature is only for visual styling preview or similar consumer use and must not be used for identity verification, legal, medical, or safety-critical purposes
- `site/Support.html`: include FAQ entries for how AI Preview works and why camera / photo-library / add-to-library permissions are requested
- do not downgrade this into a generic AI paragraph even if the page style is broad or editorial

After writing `PrivacyPolicy.html`, run:

```bash
python3 scripts/validate_privacy_output.py --inspect-json /tmp/app_inspect.json --privacy-html /abs/path/to/app/AppListing/site/PrivacyPolicy.html
```

If validation fails, rewrite the privacy policy and rerun the validator.
Do not ship a generic AI privacy paragraph.

### 7. Enforce Intro and review wording validation

After writing `Intro.md`, run:

```bash
python3 scripts/validate_intro_output.py --inspect-json /tmp/app_inspect.json --intro-md /abs/path/to/app/AppListing/Intro.md
```

After writing all user-visible pages, run:

```bash
python3 scripts/validate_review_wording.py --intro-md /abs/path/to/app/AppListing/Intro.md --site-dir /abs/path/to/app/AppListing/site
```

All `site/*.html` pages must avoid internal listing metadata that belongs to inspect, classification, or audit output rather than user-facing page copy.
Do not surface items such as:
- `Category`
- `UGC`
- `Chat`
- `IAP Codes`
- claimable-feature lists
- capability names or scores
- product-id inventories such as `boldly1001 - boldly1012`

`## Category` belongs only in `Intro.md`.
`iap_codes` / `iap_shop_code_display` are inspect-only and must never appear in HTML pages.
Natural user-facing purchase wording is allowed, but SKU or goods-code inventories are not.

Run:

```bash
python3 scripts/validate_site_metadata_output.py --site-dir /abs/path/to/app/AppListing/site
```

Also validate that all four pages are complete user-facing copy and contain no visible draft-state or placeholder material:

```bash
python3 scripts/validate_site_publication_ready.py --site-dir /abs/path/to/app/AppListing/site
```

Run this after the final copy and metadata edits. A passing result does not imply missing legal facts have been confirmed or that legal publication is complete.

The banned review wording list is:
- `mock`
- `local`
- `offline`
- `device storage`
- `local data`
- `mock data`
- `local storage`
- `offline only`

Reason:
- App Store review should not see technical implementation language that implies mock data, local-only data, or offline-only simulation. The output must read like a real consumer app, not a local prototype.

If `privacy_signals.user_content = true`, also run:

```bash
python3 scripts/validate_ugc_legal_output.py --inspect-json /tmp/app_inspect.json --privacy-html /abs/path/to/app/AppListing/site/PrivacyPolicy.html --terms-html /abs/path/to/app/AppListing/site/Terms\&Conditions.html
```

Treat actual UGC legal coverage errors as pre-deployment blockers, not post-deployment cleanup. Optional UGC strengthening warnings and unknown operator, jurisdiction, audience, retention, or network-recipient facts remain review items and do not block About deployment. Do not modify `AppListing/site/*.html` after a successful About deployment unless the user explicitly asks for a follow-up publish.

## Autonomous Resolution

This skill must not stop for additional user confirmation during normal execution.

Autonomous rules:
- if more than one app root is plausible, prefer an explicitly provided target; otherwise prefer the nearest first-party Flutter or Swift app root from the current working directory
- if multiple roots remain plausible after scoring, pick the highest-confidence root and report the choice in the final summary instead of asking the user
- if `inspect_app.py` cannot determine `app_name` or `app_slug`, try the best first-party fallback source such as `pubspec.yaml`, `Info.plist`, bundle display name, or the app-root directory name
- if classification validation rejects an initial generated classification, retry with the strongest inspected evidence-backed category candidates before giving up
- if content validation fails for locally generated copy, retry with other allowed description styles from the routed style pool before closing the run as failed
- if a required step still cannot succeed after automatic fallback or retry, finish the run with a failure summary; do not pause to ask for browser-preview approval, deployment-target approval, or execution approval

## Reporting

Always report:
- app name
- detected stack (`flutter` or `swift`)
- category and evidence basis
- active capabilities
- whether AI privacy rules were activated
- whether intro validation passed
- whether review wording validation passed
- support email source (`explicit` or `missing`)
- logo source
- total elapsed time and final summary text from `generate_app_listing.py` output (`total_timing` and `completion_summary`)
