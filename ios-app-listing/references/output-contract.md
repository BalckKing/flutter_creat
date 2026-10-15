# iOS App Listing Output Contract

## Output Structure

Always produce exactly:

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

Do not add extra files unless the user explicitly asks.

## Fixed File Contract

`AppListing/` path names are fixed and downstream-dependent:
- file and directory names are case-sensitive
- `Terms&Conditions.html` must include the `&`
- do not rename `Intro.md`
- do not add extra top-level files to `AppListing/`

## Inspect First

Before writing any listing content, run:

```bash
python3 scripts/inspect_app.py --target /abs/path/to/app > /tmp/app_inspect.json
```

Use these fields from the inspect output:
- `source_stack`
- `app_name`
- `app_slug`
- `support_email`
- `support_email_source`
- `permissions`
- `dependencies`
- `iap_codes`
- `evidence`
- `capability_candidates`
- `privacy_signals`
- `ai_signals`
- `access_signals`
- `brand_colors`
- `logo_candidates`

Treat capability candidates with `score >= 1.0` as active capabilities.

## AI Signal Interpretation

Read AI output in layers:
- `ai_signals.active` / `code_present`: AI code evidence exists
- `ai_signals.route_registered`, `navigation_invoked`, `entry_surface_visible`: structural entry evidence
- `ai_signals.claimable` / `disclosure_required`: downstream listing and legal decision

Current relaxed rule:
- if AI code exists and any one structural entry signal is present, treat AI as present for downstream claim and disclosure handling
- tab-mounted AI pages count as structural entry evidence
- `auth_gated`, `paywall_gated`, and `residual_code` are diagnostic labels and do not override a positive structural-entry judgment by themselves
- `runtime_enabled = false` means the AI flow is treated as not claimable even if code exists

Do not use UI copy wording alone to decide AI presence.

## Access Signal Interpretation

Read access output in layers:
- `access_signals.mode = credential_account|local_session|community_only|neutral`
- `credential_account`: real credential auth evidence exists
- `local_session`: local quick-entry or saved-session evidence exists without credential auth
- `community_only`: profile/feed/post/community evidence exists without credential auth

Hard rules:
- do not infer `credential_account` from `profile`, `feed`, `post_creation`, `following`, logout routes, session stores, or community vocabulary alone
- when `access_signals.mode != credential_account`, generated user-visible copy must avoid default `account`, `register`, `log in`, `sign in`, `credentials`, `username`, and `password` wording
- when `access_signals.mode != credential_account`, prefer `profile`, `community`, `member`, `saved preferences`, `saved details`, `service access`, or `repeat-use state` wording instead
- only add dedicated credential-authentication Privacy or Terms sections when inspect evidence supports `credential_account`

## Repository Boundaries

The skill must ignore any directory named `package` or `packages`.

Rules:
- do not add, delete, rename, or modify files under `package` or `packages`
- do not run formatters, generators, installers, migrations, or other write-producing commands inside those directories
- do not use those directories as evidence sources for capabilities, review claims, support email inference, URLs, or logo candidates
- inspect and generate from first-party app code only

## Category Classification

Build classifier input:

```bash
python3 scripts/classify_app_listing.py --inspect-json /tmp/app_inspect.json > /tmp/app_classification_input.json
```

Write a three-layer classification JSON with exactly:

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

Validate it:

```bash
python3 scripts/validate_app_listing_classification.py --evidence-json /tmp/app_inspect.json --classification-json /tmp/app_classification.json
```

Rules:
- do not infer category from app name, slug, or archetype
- use evidence and capability candidates only
- let `archetype` summarize the product's primary shape
- let `theme` summarize the vertical subject or audience focus using first-party evidence
- use `theme_hint` as AI-authored writing input instead of hardcoding app-specific theme copy in the generator
- do not claim unsupported features
- when `access_signals.mode != credential_account`, keep classification reasoning and generated theme-writing inputs free of strong account/login wording

## Current-Agent Authored Copy

The default skill workflow should have the current agent author the user-facing copy before invoking `scripts/generate_app_listing.py`.
The default workflow must remain non-interactive and workflow-safe:
- do not request browser access, local URL opening, or visual-helper confirmation
- do not require manual preview approval before generation, validation, or deployment
- prefer repository-local rendering and validators over any external design-assistant path
- when `ios-app-listing` is explicitly invoked, let this skill own the run and do not hand control to brainstorming, browser helpers, visual companions, or other interactive helper flows
- unless the user explicitly asks for plan-only or analysis-only output, default to direct execution without a second approval turn
- after a plan-only reply, if the user later says `执行`, `继续`, `发布出去`, or equivalent, continue immediately instead of asking for execution confirmation

Before writing `description`, resolve the assigned Intro style with:

```bash
python3 scripts/generate_app_listing.py --target /abs/path/to/app --select-description-style
```

Use the returned style as the required `description_style_label` for the authored JSON.

When using the generator, pass a JSON file with at least:
- `description`

Recommended additional fields:
- `brand_overview`
- `index_subtitle`
- `purpose`
- `members_intro`

Optional fields:
- `description_style_label`
- `subtitle`
- `keywords`

Do not rely on external AI provider or rewrite flags in the normal path.

After `scripts/generate_app_listing.py` completes, use the generated JSON fields `total_timing` and `completion_summary` in the final response. The final report must include the calculated total elapsed time and the generated completion-summary wording.

## Intro.md

`Intro.md` must be a Markdown document with these headings in order and with exactly these names:
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

Structure rules:
- headings are fixed and case-sensitive
- keep all sections present even when values are short

Content rules:
- `## App Name`: final product name only
- `## Sub Title`: <= 30 characters, exactly two Title Case words joined by ` & `
- if no authored subtitle is provided, the generator assigns one from a fixed 50-entry abstract pool using global ordered rotation
- `## Category`: one concise App Store category label such as `社交 (Social Networking)` or `天气 (Weather)`
- `## Description`: <= 4000 characters, plain text only, no HTML
- `## Keywords`: <= 100 characters total, comma-separated
- `## Support URL`: full `https://...` URL
- `## Terms of Service URL`: full `https://...` URL
- `## All URL`: a fixed 6-line block using the exact labels `首页` / `隐私政策` / `用户协议` / `Support`, bounded by `==================================================`
- `## UGC`: exactly `Yes` or `No`, based on inspected public or community user-generated content; private profile editing and direct messaging alone do not qualify
- `## Chat`: exactly `Yes` or `No`, based on inspected user-to-user messaging/chat evidence
- `## Copyright`: use a real rights line such as `© 2026 Example Studio. All rights reserved.`

URL resolution rules:
- always use `https://xxx.xxx.xxx/...` consistently for `## Support URL`, `## Terms of Service URL`, and every line inside `## All URL`
- by default, keep the placeholder URLs during generation and only rewrite `Intro.md` to the real published host after the About deployment succeeds; use `--no-deploy-about` to keep the placeholders in the final output
- treat the About deployment task status `succeeded` as deployment success; do not wait for CDN/static propagation and do not block URL rewriting on HTTP probes of `index.html`, `PrivacyPolicy.html`, `Terms&Conditions.html`, or `Support.html`
- if the `app_name` sub-domain lookup fails, times out, or returns an unusable host, skip deployment and keep the placeholder URLs; do not substitute repo-local or other-project domains
- after a successful About deployment and successful Intro rewrite validation, sync matching first-party listing/legal URLs inside `lib/` and `ios/` source files to the published host
- only exact listing-page URLs and legal/listing config host values may be rewritten; do not do a repo-wide domain replacement
- project source sync is replacement-only; do not add new app-side constants, launch helpers, controller methods, routes, labels, or About rows for `index.html` or `Support.html`
- if the app source already exposes only Terms or Privacy links, update only those existing links by default
- generated `index.html` and `Support.html` may remain deploy-only artifacts when the app has no existing in-app entry for them
- `package` and `packages` remain out of scope for source URL sync
- do not stop to ask the user which deployment target or domain to use when the default About deployment path is available; use the default path and let lookup failure fall back to placeholder URLs

Inherited old-rule priority:
- subtitle uses abstract mood, lifestyle, entertainment, or social-atmosphere words
- do not use concrete feature, modality, or object words such as `Chat`, `Call`, `AI`, `Bag`, `Preview`, or `Notes`
- `Video` may be used only when inspected evidence clearly supports a video-centered product identity
- `## Category` should be derived from the validated classification category, using a short bilingual label only
- each generation must use exactly one description style from this pool:
  - `concise`
  - `feature_3`
  - `feature_4`
  - `feature_5`
  - `benefit_3`
  - `benefit_4`
  - `longform`
  - `summary_plus_feature_3`
  - `summary_plus_benefit_3`
  - `community_then_purchase`
  - `feature_then_value`
  - `you_can_3`
  - `you_can_4`
  - `why_choose_3`
  - `homebase_4`
  - `all_in_one`
  - `members_first`
  - `everyday_use`
- style selection must not be free-form or fully random across the whole list
- first derive a candidate style pool from inspected app signals such as category, UGC, chat, IAP, translation, and AI-review risk
- inside that candidate pool, rotate styles in order on each new generation run and loop back to the first style after the last
- if the current agent first resolves a style with `--select-description-style`, it should pass the same style back in `description_style_label` when generating the final authored copy
- the first 255 characters of the description must explain the app clearly in broad consumer language
- keep the description high-level and avoid overly concrete feature narration unless the chosen style is `feature_3`, `feature_4`, or `feature_5`
- for non-`feature_3`, non-`feature_4`, and non-`feature_5` styles, avoid explicit low-level phrasing such as `video chat`, `1v1 call`, `preview flow`, or similar implementation wording unless accuracy requires it
- do not use competitor references, pricing copy, or unsupported superlatives
- when IAP is present, mention the purchase or virtual goods context naturally inside `## Description`
- when `## UGC` is `Yes`, the description should naturally mention community, public profile, post, or sharing behavior
- when `## Chat` is `Yes`, the description should naturally mention messaging or conversations
- when `## Chat` is `No`, the description must not imply in-app messaging

## index.html

Use the repository-local render pipeline to implement the site, and keep content evidence-based.

Requirements:
- act as the app's standalone launch guide and reflect the app identity and validated capabilities
- keep HTML, CSS, JavaScript, and visuals in this file; do not load external resources
- use an onboarding template independent from the legal-page template pool
- introduce the product with 3–5 evidence-based English cards, automatic rotation, clickable pagination dots, and a Continue action
- do not show Pause/Play controls; keep pagination dots centered above the bottom Continue action
- choose one of the five onboarding templates randomly per generation unless `--onboarding-template-id` explicitly overrides it
- keep template choice independent from product claims; cards must be backed by the inspected `project_profile` or reviewed authoring facts
- make Continue a prominent, full-width bottom action with at least a 60px touch height
- include `viewport-fit=cover` and safe-area inset padding
- preserve the required `continueToApp()` AppBridge / `go://continue` behavior exactly
- show no cross-page navigation
- do not invent new product claims
- do not create unsupported screenshots or product promises
- do not surface internal listing metadata or audit-only fields such as `Category`, `UGC`, `Chat`, `IAP Codes`, claimable-feature lists, capability names, capability scores, or product-id inventories
- do not block on browser preview, local preview approval, or visual mockup confirmation
- if `ai_signals.disclosure_required = false`, user-facing AppListing copy must not introduce `AI`, `AI Preview`, `assistant`, or similar AI-feature wording
- if `access_signals.mode != credential_account`, user-facing AppListing copy must not introduce strong credential-account wording by default

`PrivacyPolicy.html`, `Terms&Conditions.html`, and `Support.html` must each stand alone and must not contain navigation links to the other generated HTML files. In-page section anchors and email links remain valid.

Do not add generic template filler such as "Review the information on this page." to page headers or other visible copy.

Legal copy is generated from the shared `product_facts` matrix. Never infer a feature, permission purpose, third-party recipient, retention period, age policy, purchase type, support contact, or operator jurisdiction from a fallback or category label. `unknown` is not `false`; unknown or conflicting material facts must be reported with the field and evidence. Keep those review items in the internal generation summary, never as visible page placeholders. Missing facts do not block local HTML generation, but they keep public legal review incomplete; do not report the pages as ready for public legal publication until the required facts are confirmed.

The generation authoring JSON may provide a `legal` object:

```json
{
  "legal": {
    "confirmed": true,
    "operator_name": "Verified operator name",
    "operator_jurisdiction": "Verified jurisdiction",
    "children_targeted": false,
    "minimum_age": 16,
    "data_retention": "Verified retention and deletion description",
    "features": {
      "reporting": true,
      "blocking": true,
      "moderation": true,
      "terms_acceptance": true
    },
    "review_time": "Verified moderation response commitment",
    "network_services": [
      {
        "host": "api.example.com",
        "recipient_type": "first_party",
        "data_types": ["Verified data categories"],
        "purposes": ["Verified service purpose"]
      }
    ],
    "iap_types": ["subscription"],
    "ai": {
      "inputs": ["text prompts"],
      "providers": ["Verified provider"],
      "processing": "Verified processing location and behavior",
      "retention": "Verified provider and local retention",
      "deletion": "Verified deletion process",
      "send_condition": "Verified user action before transmission",
      "equivalent_protection_confirmed": true,
      "identity_processing": false
    },
    "tracking": {
      "enabled": true,
      "authorization_gated": true,
      "authorization_evidence": "Verified ATT integration reference",
      "data_types": ["Verified data"],
      "purposes": ["Verified purpose"],
      "providers": ["Verified provider"]
    }
  }
}
```

Values above illustrate schema only; they are not defaults. `legal.confirmed` means the operator reviewed the supplied facts. Unknown facts remain review items and must not be silently converted into affirmative legal claims. The generated summary exposes them so the operator can complete review before final public/legal publication.

Site-page metadata rules:
- `## Category` belongs only in `Intro.md`
- `iap_codes` / `iap_shop_code_display` are inspect-only fields and must never appear in `site/*.html`
- page copy may naturally mention supported purchase behavior, but must not expose SKU or goods-code inventories

## Logo

Copy the best logo candidate to:

```text
AppListing/site/img/logo.png
```

The source must be a decodable raster image with a real image signature. The
Stargate URL `http://stargate.local:3100/image` is a generation UI, not a file
URL; reject HTML, JSON, error pages, and page source even when a response is
named `.png`. Prefer `assets/logo.png`, then `ios/Runner/assets/logo.png`, and
then a valid existing AppIcon. If the Logo service failed, record the
official Logo and palette as `Blocked`; a valid AppIcon or explicitly marked
`unverified` development brand may keep local generation moving, but must not
be represented as the approved Logo. Revalidate the copied output after it is
written. A missing valid source is a `required_logo_missing` delivery warning,
not permission to save HTML or to stop independent local HTML, directory, and
Review Remarks work. The normal whitelist still contains `site/img/logo.png`,
so preserve a valid source/provenance whenever one exists and report the exact
gap when it does not.

External photo failures follow the same boundary: 403/429 responses,
timeouts, blocked hosts, login walls, or unverified licences leave the photo
item `Blocked`/`Not verified` and do not prevent local AppListing/About,
`aduit/`, or `aduit/review/remarks.md` generation.

In the no-valid-image case, Intro and all four pages are written with
`local_generation_complete: true`, while `media_review_errors` contains
`required_logo_missing`, `logo_source` is null, and the required-image
contract remains failed. Leave `img/` empty rather than invent a file. A
nonzero validator exit does not authorize dropping these local artifacts or
skipping downstream normalization and factual Remarks. Publication readiness
remains false for missing or fallback branding.

## PrivacyPolicy.html

The privacy policy must:
- name the app specifically
- reflect real permissions and collection signals
- explain what data is collected
- explain how data is collected
- explain why data is used
- describe third-party service categories when relevant
- include user-rights contact instructions
- include a children privacy section

Required sections when the corresponding legal fact is confirmed:
1. Overview
2. Information We Collect
3. How We Use Information
4. Sharing and Service Providers
5. Data Retention
6. Your Rights and Choices
8. Changes to This Policy
9. Contact

Conditional sections:
- camera or photo library -> image and media access section
- microphone -> audio processing section
- tracking -> analytics and advertising section
- recharge or payments -> purchases and billing section
- feed or post_creation -> user content and community section
- messaging -> message handling section only; do not add community moderation rules unless public/community UGC is also confirmed
- credential-based sign-in evidence -> credential-authentication section
- AI disclosure required -> dedicated AI section required by `references/privacy-ai-rules.md`
- confirmed child-audience policy -> Children's Privacy section

## Terms&Conditions.html

Required sections when the corresponding legal fact is confirmed:
1. Definitions
2. Acceptance of Terms
3. Use of the Service
4. Access and Service Security
5. Intellectual Property
6. Disclaimers and Limitation of Liability
7. Service Availability
8. Amendments
10. Contact

Conditional sections:
- `User Accounts` replaces section 4 only when inspect evidence supports `access_signals.mode = credential_account`
- recharge or payments -> purchases and credits
- feed or post_creation -> user content and community rules
- messaging -> message-use rules without community moderation obligations
- AI disclosure required -> AI-assisted features and output limitations
- translation-like features -> translation accuracy disclaimer
- confirmed operator jurisdiction -> Governing Law section

## Support.html

Support.html must:
- use the same shared visual system as the other site pages
- include app-specific FAQ content based on validated capabilities
- include a support email only when it is explicitly confirmed in first-party project information; never infer `support@<slug>.com`
- when no support email is confirmed, omit the email/contact panel and record the missing contact channel in the internal generation summary
- avoid generic placeholder FAQ copy
- avoid default account/login FAQ unless inspect evidence supports `credential_account`

## Site Publication Readiness

All four HTML pages must read as complete, independent, carefully written product or policy pages. Do not ship page-state/authoring material such as `Draft`, `WIP`, `TBD`, `TODO`, `Placeholder`, `Pending confirmation`, `Coming soon`, bracketed fill-in fields, internal notes, or unfinished headings. Apply this to rendered copy, document titles, descriptions, image alternative text, and accessibility labels. A product feature may use a similar term only when supported by project facts; never use it as a page-state label. Do not replace missing legal facts with vague filler or invented details; omit unsupported contact or legal claims, record the exact gaps in the internal generation summary, and keep legal publication review marked incomplete.

Validate the full four-page set after generation:

```bash
python3 scripts/validate_site_publication_ready.py \
  --site-dir /abs/path/to/app/AppListing/site
```

Fix every page-copy error and rerun the validator. This check supplements, and does not replace, the product-claim, privacy, terms, support, and visual reviews.

## Claim Rules

Every capability claim in:
- Intro description
- index.html
- PrivacyPolicy.html
- Terms&Conditions.html
- Support.html

must map back to at least one of:
- `claimable_features`
- permissions
- explicit inspected evidence

## Intro Validation

`Intro.md` should be validated against the fixed heading contract and content rules before finishing.
Recommended validator:

```bash
python3 scripts/validate_intro_output.py \
  --inspect-json /tmp/app_inspect.json \
  --intro-md /abs/path/to/app/AppListing/Intro.md
```

## Review Wording Validation

All user-visible AppListing text must avoid review-harmful wording from this list when those terms expose implementation details:
- `mock`
- `local`
- `offline`
- `device storage`
- `local data`
- `mock data`
- `local storage`
- `offline only`

Reason:
- App Store review should not see wording that exposes local mock data, local-only storage, or offline-only simulation details. The listing should present a real app experience.

Run:

```bash
python3 scripts/validate_review_wording.py \
  --intro-md /abs/path/to/app/AppListing/Intro.md \
  --site-dir /abs/path/to/app/AppListing/site
```

## Site Metadata Validation

All `site/*.html` pages must avoid internal listing metadata labels and inventory values that belong to inspect, classification, or audit output instead of user-facing page copy.

Disallowed visible HTML examples:
- `Category`
- `UGC`
- `Chat`
- `IAP Codes`
- standalone App Store category labels that only restate `Intro.md`
- IAP product-code inventories such as `boldly1001 - boldly1012`

Run:

```bash
python3 scripts/validate_site_metadata_output.py \
  --site-dir /abs/path/to/app/AppListing/site
```

## UGC Legal Validation

If public/community UGC is confirmed (`privacy_signals.community_ugc = true`, or equivalent feed/post evidence), validate UGC coverage in legal pages:

```bash
python3 scripts/validate_ugc_legal_output.py \
  --inspect-json /tmp/app_inspect.json \
  --privacy-html /abs/path/to/app/AppListing/site/PrivacyPolicy.html \
  --terms-html /abs/path/to/app/AppListing/site/Terms\&Conditions.html
```

Terms should cover reporting, blocking or restriction, prohibited conduct, enforcement, contact guidance, timely review, EULA or terms acceptance, and age eligibility for community content. Actual UGC coverage errors block deployment; optional strengthening warnings do not.

## AI Privacy Validation

If `ai_signals.disclosure_required = true`, run:

```bash
python3 scripts/validate_privacy_output.py --inspect-json /tmp/app_inspect.json --privacy-html /abs/path/to/app/AppListing/site/PrivacyPolicy.html
```

The privacy policy must pass before finishing.

## Self-Check

Before finishing, confirm:
- output file names exactly match the required structure
- category classification passes validator
- description claims are evidence-backed
- privacy sections reflect real permissions and data flows
- AI privacy validator passes when AI signals are active

## Runner Result Contract

When the skill is invoked by AppDevOps-Runner, the Runner sets the environment variable
`IOS_APP_LISTING_RESULT_PATH`. The script writes a JSON file to that path atomically after
the normal generation workflow completes:

```json
{
  "protocolVersion": 1,
  "mode": "generation",
  "exitCode": 0,
  "summaries": [
    {
      "deployment": {
        "status": "succeeded",
        "published_base_url": "https://example.invalid"
      },
      "failures": []
    }
  ]
}
```

This file is Runner transport metadata, not an AppListing artifact. It must not be written
inside or committed from the project worktree. The regular CLI JSON written to stdout remains
the human-facing output and is not a machine protocol.
