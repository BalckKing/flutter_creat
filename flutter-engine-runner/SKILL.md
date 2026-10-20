---
name: flutter-engine-runner
description: Run the bundled Flutter iOS app workflow when the user invokes flutter-engine-runner or asks to execute the Flutter工程 specification. Collect the user's app idea and project name, show the full plan for approval, then implement in the user's target directory. Do not start app development when the user only asks to edit or explain the workflow files.
metadata:
  short-description: Portable Flutter workflow with user idea and name
---

# Flutter 工程执行

This is an execution skill. When the user requests execution, perform the current workflow step; do not merely describe the document. If the current request is to edit, diagnose, or explain these files, handle that request without starting app development.

## Load the portable workflow

First record the Codex workspace/current working directory **before** changing directories. This is `Invocation cwd`, not the directory containing this skill.

Resolve these paths relative to the **actual loaded SKILL.md**, never relative to a hardcoded username or the shell's current directory:

- Installed copy: read the complete [workflow collection entry](references/工作流文档/00-总入口.md), then completely read all ten body documents linked there in their listed order. Together they are the complete specification. `Workflow resource root` is `references/`, the **parent** of `工作流文档/`; the only executable AppListing source is the complete Git checkout at `references/ios-app-listing/`, synchronized by the bundle installer from the configured remote `feature/1.2.1-A1` branch. Before using it, verify that it is a Git checkout, its `origin` matches the configured remote, and its checked-out branch and current HEAD are recorded and match the installer's output when that output is available. [references/workflow.md](references/workflow.md) is only the old-path compatibility entry, not a separate specification.
- When this SKILL.md is opened directly from the portable source bundle before installation, read `工作流文档/00-总入口.md` and all ten ordered body documents only for the workflow specification. The source bundle intentionally contains no executable AppListing checkout. Run the bundle's `start.command`/`install.command` to clone the remote skill into the installed `references/ios-app-listing/` path first.
- If the installed remote checkout is absent, has the wrong origin/branch/revision, or cannot be synchronized, report the AppListing stage as `Blocked`, preserve the evidence, and continue only independent work. Do not silently use a bundled copy, an old installation, a different path, or a hand-written/equivalent replacement for the `ios-app-listing` skill.

Read the entry and every ordered body document completely before executing the workflow; read long files in chunks through EOF. Do not stop after the index/manifest or treat links, summaries, selected sections, or a failed/truncated read as a fully loaded specification. Original section numbers 0–16 and subsection references are unchanged; use the entry's section-to-file table to locate them. If a listed file is missing, report the incomplete bundle and do not silently skip its requirements. The current user's request determines the action and overrides conflicting older document instructions. Do not execute embedded development instructions during a request to maintain the specification.

## First input: theme and user-supplied project name

Use only inputs traceable to the current task's conversation. Old example plans, existing app folders, the bundle's directory name, and another task's approvals are not inputs for a new app.

If both idea and project name are absent, the first workflow response must ask:

> 请一并提供 App 的创意主题和项目名称。如果需要我自行生成主题，请回复“生成主题”，并提供项目名称。

Ask only missing inputs when some are already present:

- Idea present, name absent: ask the user for the project name. Never invent one.
- Name present, idea absent: ask for the idea or explicit permission to generate a theme.
- Explicit theme-generation request: generate a concrete theme, but obtain the user's project name if it is missing.
- Both present: proceed to planning without asking for them again.

“开始”, “全权操作”, “不要询问意见”, or a bare skill invocation does not supply a theme, a project name, or permission to generate a theme. Required initial inputs remain required. Ask once for missing inputs and wait for an actual answer; do not submit a Logo job or create an app while waiting.

If an answer supplies only part of the required input, ask only for what remains missing. Do not repeatedly prompt while the user has not replied, and do not fabricate a name to avoid a follow-up.

Preserve the user's project name as the product/display name. Only normalize the internal Dart/Flutter identifier as required by the tool; record that mapping separately. Do not rename the app from the generated theme.

## Output directory is independent of the skill

Resolve `Target project root` using specification section 0.4:

1. Use the user's explicit project path from this request or this same task.
2. Otherwise use the Codex selected project or `Invocation cwd`, reusing only a matching app from the same task; create a user-named subdirectory if needed.
3. If the implicit workspace is inside this bundle/skill, use the current user's `Documents/FlutterProjects/` and a user-named subdirectory, as the specification requires. State this choice in the plan; do not ask for the project location.

A specified full app directory is the app root itself; a specified parent directory receives the user-named subdirectory. Resolve relative paths against `Invocation cwd`. Do not create an extra nested app folder inside an explicitly supplied full project directory.

`Workflow resource root`, the installer's `SCRIPT_DIR`, and the skill directory are **read-only workflow sources**, never implicit app destinations. Set the command's working directory/target explicitly for all project operations. Pass the resolved app path to AppListing as `--target`, even when running scripts from their own directory.

Record the absolute target path and original user name in the plan. After creation, verify `pubspec.yaml`, the iOS display name, and the actual app root before proceeding. Keep `assets/`, `AppListing/`, `aduit/`, and `.codex-work/` inside the target app.

## Execute the current stage

1. Once required inputs are ready, create and show the complete Mermaid mind map, coverage table, validation result, and implementation plan required by specification sections 2.4, 3, and 3.5. Wait for explicit approval of the shown version. Theme-generation consent does not approve development.
2. When that plan is approved, continue the next unfinished implementation step. Logo generation/validation and palette extraction are the first project task, followed by theme creation and Flutter implementation. Apply section 2.5's detailed Logo brief: a finely crafted theme-specific subject, refined contours, materials and lighting, at least three distinct vivid color families, and smooth coordinated multicolor gradients. The palette must avoid a cold, austere, monochromatic look; if the theme calls for cool colors, balance them with vivid warm or other high-saturation accents. Specifically, choose a refined hand-drawn illustration or non-3D realistic style based on the theme, subject recognition, brand mood, and app-icon legibility; select one primary style and record why. Hand-drawn must be polished and detailed, not a crude sketch; realistic must have coherent structure, proportions, materials, and lighting, without 3D. Avoid a conspicuous AI-generated look and forbid 3D. Reject stacked or collaged geometric color blocks, crude sketches, simplistic generic symbols, and conspicuous image-generation defects such as distorted structure, broken edges, duplicated textures, incoherent reflections/shadows, random fragments, pseudo-text, or plastic-looking overprocessing; the subject should remain visually plausible and recognizable, without forcing the Logo into photorealism. Inspect both full-size and app-icon-size output before acceptance. Palette extraction means analyzing representative colors, not drawing a color-block collage. Track color use as `Logo source HEX -> Flutter theme token -> actual screen/component -> iPhone screenshot`; at least three real App screens or components must visibly consume derived brand colors, including the main screen, a real task screen, and another App screen, with current-build screenshot evidence. Use `http://stargate.local:3100/image` only for the Logo, not pen.dev and not for App content photographs, covers, backgrounds, video frames, or other local content images. Fetch licensed real photographs from third-party websites or official resource APIs; never substitute AI-generated photorealism for them. For each primary content list, use at least two visibly distinct, content-driven item sizes, and plan `featured`/`standard`/`compact` tiers across the primary browse experience where the content supports them. Keep Settings, policy, permission, and other scan-oriented rows uniform; preserve logical reading order, Dynamic Type, correct image crops, and iPhone accessibility. Perform actual edits, commands, asset work, builds, and proportionate verification.
3. Apply the document's bounded retries and fallbacks. Continue independent work after genuine external failures; report limitations accurately. Do not stop at a status summary while work remains executable.

Name the downloaded/exported Logo `<User project name>.png`, using the user's
supplied name rather than the Flutter identifier. Follow specification section
2.5 for temporary browser names, necessary filename sanitization, and actual
RGB PNG conversion. After validation, import it into the target project's
`assets/` under that name, then rename it there to `logo.png`. Record the actual
export -> import -> final path mapping in `.codex-work/brand-assets.md`;
runtime references, palette extraction, icon derivation, and AppListing use
`assets/logo.png`. Do not bundle a duplicate project-named Logo. The project
name belongs only in the filename; the Logo image must remain text-free.

The Stargate path is a generation interface, not an image download URL. A
response is usable only after MIME/signature checks and image decoding; never
write returned HTML, JSON, an error page, or page source into
`assets/logo.png`. If an actual Logo task fails or its final image is invalid,
first check that task's status, then switch the generation UI's model selector
or the actual request's `model` parameter to another currently configured,
available image model that supports the same required settings. Merely naming
another model in the prompt does not switch it. Follow section 2.5: retain
high quality, one image, 1024x1024, and the final RGB PNG/no-Alpha requirement;
all model switches and other generation retries share at most three total
submissions and the original ten-minute deadline. Never resubmit a task with
unknown status, guess model IDs, or switch services. Record actual model IDs,
parameters, task IDs, reasons, and outcomes without credentials. Attempt a
supported alternative before falling back when one is available within budget;
do not ask the user to choose. A normal HTML response from the generation UI
alone is not a failed generation. If no supported alternative is available or
bounded attempts fail, record the official Logo/palette as `Blocked` and,
when available, use a valid existing AppIcon or explicitly
labelled `unverified` development brand only to keep local implementation and
listing generation moving. The fallback must remain clearly marked and must
not be reported as a successful Logo replacement. A blocked third-party photo
search is handled the same way: preserve the photo gap and provenance, then
continue local AppListing, About, `aduit/`, and Review Remarks work instead of
stopping the workflow.
4. After implementation and delivery quality review, read the complete synchronized remote AppListing checkout at `references/ios-app-listing/SKILL.md` and its required references, scripts, and assets. Generate the AppListing and corresponding About pages through that skill with `--no-deploy-about --no-sync-project-listing-urls`, verify the About palette against `assets/logo.png`, then rename/normalize the generated `AppListing/` directory to `aduit/` using the workflow whitelist. Preserve any existing `aduit/review/` directory recoverably while replacing older AppListing content. Do not ask for, look up, infer, or replace a domain; do not call a public deployment API, wait for DNS, probe public URLs, or claim that generated URLs are online. If the synchronized remote skill is unavailable or fails validation, mark this stage `Blocked` and do not generate an equivalent manual listing. Keep project operations pointed at `Target project root`.
5. Immediately after that rename, before URL-registry work or Review Remarks, completely replace `aduit/site/index.html` (the requested `aduit/index.html` refers to this existing whitelisted site file) with the current app's onboarding guide and load that same file as the actual Entry screen's bundled local WebView. Do not add a duplicate HTML file or change the site whitelist. Base 3–5 cards on verified project code/configuration and `aduit/intro.md`; use English for all visible copy and match the current App/Logo palette. Keep all HTML, CSS, and JavaScript inline in this single file, use system fonts, and load no external scripts, styles, fonts, images, or runtime resources. Make it responsive, as complete as possible within one screen, with no overlap or clipping; include `viewport-fit=cover`, `env(safe-area-inset-top)`, and `env(safe-area-inset-bottom)`. Show one card at a time, auto-rotate, and provide accessible clickable pagination dots. Honor `prefers-reduced-motion` by stopping automatic and nonessential movement while leaving dots usable. Retain the required two-line protocol footer with independently tappable Terms and Privacy text targets; keep it clear of the `Continue` button. Bind those targets to the final raw URLs in step 6, after the guide-specific acceptance is complete.

   The `Continue` button must call this exact page function; do not add alternate branches or change its behavior:

   ```javascript
   function continueToApp() {
     if (window.AppBridge && typeof window.AppBridge.postMessage === 'function') {
       window.AppBridge.postMessage('continue');
       return;
     }
     window.location.href = 'go://continue';
   }
   ```

   In the Entry WebView, expose only the minimal `AppBridge.postMessage` channel needed for `continue`, route that exact message through the existing Entry-to-main-app transition, and have the native navigation delegate intercept exact `go://continue` when the Bridge is absent. Both routes must converge on the same existing flow; neither may bypass initialization or permission behavior. Do not leave an old visible `Enter` CTA beside `Continue`.

   Before continuing, verify the actual packaged page is `< 262144` bytes, makes no external resource request, and has no overlapping, covered, or clipped content at `390×667`, `390×844`, `1024×768`, and `1440×900`. Exercise automatic rotation, every dot, reduced motion, Bridge-present single `continue` delivery with no fallback navigation, and Bridge-absent exact `go://continue` interception. Use no-network WebView/Bridge stubs for native routing and save screenshots/results in `.codex-work/`. If a required check is blocked, record it as `Blocked`/`Not verified`; do not silently skip it or begin Review Remarks before the guide is accepted.

6. After the guide is accepted, before writing Review Remarks, read `aduit/intro.md` and copy the four URLs under `All URL` exactly into the app's fixed URL registry as raw strings. Do not parse or validate them as a prerequisite to copying or storing; do not normalize, repair, omit, or replace a URL even if its syntax or destination appears invalid. At this same stage, confirm the actual welcome-page footer is exactly two lines, with an explicit line break after `our` and no final period:

   ```text
   By continuing, you agree to our
   Terms of Use and Privacy Policy
   ```

   Keep `Terms of Use` and `Privacy Policy` independently tappable on the second line, with `and` plain text, and bind each to its corresponding raw URL. Keep the footer centered inside the bottom safe area without clipping or obscuring `Continue`. Do not merely edit HTML, a string resource, or a plan: update and verify what the App actually renders. Settings must show exactly three WebView links: `Privacy Policy`, `Terms of Use`, and `Support`; never add the guide/Home link there. Keep the onboarding guide at `site/index.html` and retain the original About Home URL in the fixed registry without exposing it as a Settings entry. A user-initiated link opens through the existing WebView; a load failure must show a readable error with return/retry and must not fall back to the development-time local page or block `Continue`, Settings, Clear Data, or other app flows. Do not add a consent checkbox, extra confirmation, or personal acceptance record; this footer does not grant media permissions or ATT consent. For regression, use a WebView stub/fake that makes no network request to verify the exact footer copy and line break, safe-area layout, both link targets, all four registry values, exactly three Settings entries with no onboarding guide, error, and return behavior; do not visit or probe the real generated URLs. Then verify project source, configuration, and actual test records. Only after the guide and URL/footer stage is complete, create `aduit/review/remarks.md` in English, no more than 4,000 characters, with the seven required review sections in order. Use only confirmed facts; do not claim unsupported device tests, login or billing flows, services, regions, or features, and do not expose private package/module details. Then validate the final `aduit/` whitelist: `intro.md`, `site/` with the guide plus the other three HTML pages and `img/logo.png`, and `review/remarks.md` only. Follow sections 12.1-12.3 of the bundled workflow documents.

7. After every implementation, validation, AppListing/Review Remarks task, and delivery-directory check is complete, perform section 10.7 as the final workflow step before reporting. Recheck section 10.4's actual Logo replacements: the iPhone Home Screen icon, launch branding, Loading/Entry brand covers, and existing App/About brand placements must use the approved Logo or traceable derivatives. App runtime branding must reference `assets/logo.png`; saving the file, changing colors, or hot reloading alone is insufficient. Apply the references and iOS icon configuration, rebuild/install, and inspect the current icon and cold-launch screens. After AppListing normalization, copy that source to `aduit/site/img/logo.png`, compare hashes, and inspect local page rendering without adding cover files to the site whitelist. Record placement → file/derivation → actual reference → screenshot in `.codex-work/brand-assets.md`; repair old/default branding under section 10.4. Separately verify every content-image placement loads its correct theme-relevant image with no placeholders, broken images, generic empty thumbnails, or temporary art. For missing, incorrect, or unjustifiably duplicated content photographs, search and download licensed replacements from Pexels, Pixabay, Unsplash, or Wikimedia Commons, update assets/provenance and page references, rebuild, and recheck display and offline loading. Never replace content photographs with the Logo or AI-generated imagery. Scan the resolved local dependency/build trees, including local `path` packages, `.dart_tool/package_config.json` roots, `ios/.symlinks/plugins/`, `ios/Pods/`, `build/`, and the final App bundle; remove each exact nested `aduit` directory/link found there, then verify the dependency tree and bundle contain no `aduit` directory copy and rebuild as needed. Do not delete, move, or overwrite the target project's root `aduit/` deliverable. Entry/Settings protocol links must use the raw URLs from `aduit/intro.md` under `All URL`; verify the exact mapping with a no-network WebView stub. Do not visit or probe real URLs. Protocol HTML files remain listing deliverables and must not be copied into dependencies or the App bundle. Keep the Entry guide source at the single `aduit/site/index.html`; if the App needs a bundled copy, copy only that file, never the whole `aduit/` directory. Record dependency scan scope, each exact removed path, the preserved root directory, Logo and URL references, build/device, checked placements, sources/licenses, replacements, and final screenshots in `.codex-work/quality.md`. If no iPhone runtime is available, report the affected display checks as `Blocked`/`Not verified`; never claim they passed. Only after this check may the final report be delivered.

Do not join media checks, listing generation, normalization, and Remarks with
one shell `&&` chain. Inspect each result and preserve generated files on a
nonzero exit. The generator's `local_generation_complete` reports written
Intro/HTML output; `media_review_errors` and `failures` retain separate gaps.
If every image candidate is invalid, it still writes the four pages and
Intro, reports `required_logo_missing` and the failed contract, and leaves
`img/` empty. Continue normalization and factual Remarks without claiming the
Logo, whitelist, or publication checks passed; never fabricate an image.

On resumption, inspect the same task's actual input, approval, file, and process state. Preserve valid inputs and approvals without re-asking; never infer approval merely from a file's existence.

## Required real photographs, not illustration-only assets

Apply specification section 10.6 as a required media task: plan theme-specific photographic placements in the mind map, then, after approval and the Logo priority phase, actually search third-party sites, inspect source pages/images and licenses, download permitted real-world photographs into the target app's `assets/media/`, and bind them to the corresponding content pages. Stargate is Logo-only; never use its image-generation endpoint for content photographs, covers, backgrounds, video frames, or other local content images. Preserve source/query/license records and requirement → file → placement → current-build screenshot/offline-loading evidence in `.codex-work/`. Downloading a file without displaying it does not fulfill the task.

Missing Pexels/Pixabay keys or the optional resource-download skill does not cancel web discovery. Use available public-web search/browsing and allowed downloads; switch to another licensed source after a source fails. Before declaring photographs unavailable, actually attempt at least two independent suitable sources, following section 0.6's finite request/retry limits. If no network/browsing capability is available at all, record that evidence rather than inventing attempts. Do not bypass access restrictions, licensing, or fees, and do not ask for another asset-selection approval.

Emoji, gradients, vector art, illustrations, stock AI images, and synthetic photorealistic pictures do not count as real photographs. A fallback may keep independent development moving, but missing required photographs or unresolved license/display evidence leaves the corresponding media requirement `Blocked`/`Failed`/`Not verified`, not `Verified`; do not silently revise away the approved photographic placements. Content photographs belong in the app's media assets, not in the strictly whitelisted `aduit/site/img/`. This requirement does not change the Stargate-only Logo source or the user-supplied project name/output directory.

For visual quality, inspect the generated Logo for plausible subject structure, coherent materials and lighting, and obvious generation artifacts without sacrificing its vivid colors or gradients. Build varied content-list layouts from meaningful hierarchy rather than random card sizing: every primary list with multiple entries uses at least two clear size tiers; across the primary browse experience, use `featured`, `standard`, and `compact` where supported by content, without requiring all three on every page. Utility rows stay aligned and easy to scan. Verify image focus/cropping and VoiceOver/Dynamic Type order at each size on iPhone. Native icons, code-drawn vector symbols, decorative illustration, and gradients may be designed as UI assets; the third-party photo-source rule applies to real content photography and does not count these UI elements as photos. See sections 2.5, 4.2, 6.9, and 10.5 of the workflow collection.

## Branded Loading and native iOS launch screen

Keep the native cold-start screen and Flutter Loading as two distinct surfaces. The iOS `LaunchScreen.storyboard`/launch resources are static: show a visibly larger approved Logo, a separate `PRYRIN` wordmark, one truthful positioning line derived from the approved app idea, and a brand-colored decorative line. Use iPhone-safe layout constraints. `PRYRIN` does not replace the user's supplied project name, and neither it nor the positioning line is baked into the text-free Logo. The native screen has no animation, interaction, progress bar, percentage, or fake loading state; it hands off to Flutter Loading.

Flutter Loading uses a deep multi-stop gradient derived from the approved Logo palette, a soft glow behind the Logo, and a restrained breathing animation. Show the user's project name, the same positioning line, the current real startup step, a percentage, and a progress bar. Before startup, enumerate the required milestones; calculate percentage as completed required milestones divided by total required milestones (or from genuinely measurable completed/total work units). Keep independent work parallel, update only when real work completes, and never invent milestone weights or use a timer, animation, guessed duration, or minimum display delay to advance progress. Hold the last truthful percentage while a step is running, and show 100% only when every required startup milestone is ready. Deferred image decoding, video preloading, full media scans, and document-integrity scans are outside startup progress.

When core startup configuration fails, preserve both `Try again` and `Clear Data`. Retry the failed step (or restart from a consistent startup state) with a fresh operation identity so stale callbacks cannot overwrite the result. `Clear Data` must open the existing second-confirmation flow and reuse the full established clear/recovery behavior; cancellation changes nothing, and the app returns to Entry only after the confirmed clear actually succeeds. Honor the system Reduce Motion setting immediately, including changes while the app is open: stop breathing, glow pulsing, moving gradients, and animated progress transitions, while retaining the same static brand palette, actual step, percentage, and progress bar. Verify cold launch and Flutter Loading separately on iPhone, including normal/reduced motion, real progress updates, startup error, retry, and clear/cancel/confirm paths. Follow section 7.1 of the workflow collection.

## Minimum iOS deployment target

Set the minimum iOS deployment target to `15.6` by default in `platform :ios`, the app and UI-test targets, and every applicable build configuration. If Flutter, a plugin, CocoaPods, Xcode, or another actual dependency requires a higher value, retain the higher value consistently and record the evidence; never lower dependencies or fake settings/artifact metadata to force 15.6. Verify resolved build settings and, after a build/archive, the artifact's `MinimumOSVersion`.

## iPhone-only execution target

Create and configure only an iOS iPhone app. Set the application target's resolved `TARGETED_DEVICE_FAMILY = 1` and `SUPPORTED_PLATFORMS = iphoneos iphonesimulator`; do not add or build other platform targets. Select a specific iPhone model and UDID for every simulator run, screenshot, and UI check. Filter device listings before selection or presentation; never use an implicit/default destination or another device/platform as a fallback. Reuse at most one existing iPhone simulator, and start it only after Flutter project creation and a runnable page are ready. If no eligible iPhone is available, record that limit, continue independent static/iOS checks, and do not claim runtime verification.

## Best-effort Podfile permission macros

After resolving the actual permission plugin and version, inspect `ios/Podfile` and make an idempotent, minimal macro configuration before CocoaPods installation and iOS packaging. For `permission_handler_apple`, use only the macros required by the actual APIs (camera, PhotoKit library access, microphone); preserve an existing `post_install` hook and inherited settings. If writing, parsing, or validating the macro configuration fails, leave a syntactically valid Podfile, record the exact failure, and continue `pod install` and the iOS packaging/build attempt. Macro-configuration failure alone must never abort packaging. Report macro setup, Pods installation, build, and permission runtime verification as separate results; a missing macro or untested permission path is not `Verified`, and independent CocoaPods/build failures remain accurately reported.

## Final delivery whitelist

Enforce this exact structure in the app's output directory:

```text
aduit/
  intro.md
  site/
    index.html
    PrivacyPolicy.html
    Terms&Conditions.html
    Support.html
    img/
      logo.png
  review/
    remarks.md
```

Transfer only these files from `AppListing/`, renaming the actual generated `Intro.md` to `aduit/intro.md`. Keep Disclaimer and Content & Copyright Notice as sections in the permitted legal pages. Inline required CSS/JavaScript and use system fonts. Keep execution records, reports, screenshots, and recoverable extras/backups in the app's `.codex-work/`, outside `aduit/`.

Check exact entries including hidden items and symbolic links after generation and after transfer; validate required pages, image references, relative links, section anchors, and offline rendering. Validate `review/remarks.md` separately for English-only text, no more than 4,000 characters, all seven ordered sections, evidence-backed claims, and no `**` bold markers. Only then clean up the app's `AppListing/` and any old `aduit/html/`, preserving needed extras outside the delivery. Never claim the whitelist is satisfied while extras remain.

The shell launcher installs this skill and synchronizes the complete `ios-app-listing` checkout from the configured remote branch before preparing a prompt; it does not itself send a Codex message or build the app. File/folder mentions alone do not register a skill. Once installed and loaded, explicit invocation is `使用 $flutter-engine-runner，开始执行。` The source-bundle `ios-app-listing/` directory is not a runtime fallback and must not be used in place of the synchronized checkout.
