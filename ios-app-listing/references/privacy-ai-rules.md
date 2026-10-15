# AI Privacy Rules

Apply these rules only when `ai_signals.disclosure_required = true` in the inspect output.

Interpretation notes:
- `ai_signals.active` means AI code evidence exists
- `ai_signals.claimable` / `disclosure_required` means the AI flow is treated as product-facing for listing and legal output
- under the current relaxed rule, any structural AI entry such as route registration, route jump, visible entry surface, or tab-mounted AI page can make AI disclosure required
- `auth_gated` and `paywall_gated` do not cancel disclosure by themselves
- `residual_code = true` means AI code was found without a structural entry and should not trigger these rules on its own

The privacy policy must clearly cover all of the following:

1. What data is sent
- Identify the user data that may be transmitted to an AI or inference service.
- Typical examples: prompts, chat messages, uploaded images, generated image inputs, voice audio, copied text, optional profile context.

2. Who the data is sent to
- State whether the data is sent to:
  - an external AI model provider
  - a third-party inference service
  - a contracted AI service provider category
- If the project evidence exposes a concrete provider or host, prefer naming that provider or host instead of using only generic language.

3. Permission before sending data
- State that the app only sends user content after a clear user action or consent step.
- If relevant permissions exist, describe them separately from inference permission:
  - camera
  - microphone
  - photo library

4. Collection, method, and use
- Identify:
  - what data the app collects
  - how that data is collected
  - why it is used
- This must cover both app-owned collection and AI-processing use.

5. Third-party protection
- Confirm that third parties receiving the data provide the same or an equivalent level of protection.
- Acceptable formulations include:
  - contractually required to provide equivalent protection
  - required to protect the data to the same or a materially equivalent standard

## Required Privacy Policy Coverage

When AI rules are active, `PrivacyPolicy.html` must include a dedicated AI section or equivalent grouped coverage that contains:
- transmitted data categories
- recipients or recipient categories
- user permission or user-initiated send condition
- collection and use explanation
- third-party protection statement

## Minimum Terms Coverage

When AI rules are active, `TermsConditions.html` should also include an AI-related limitation section that states:
- outputs may vary
- outputs are not guaranteed accurate
- users remain responsible for what they submit and how they use generated or assisted output

## AI Preview / Face-Data Review Profile

When `ai_signals.review_profile.needs_face_data_clauses = true`, generic AI wording is not enough. The generated output must be review-ready for Apple follow-up questions about face data and image preview flows.

### Privacy Policy must include quoteable section headings for:
- AI Preview and selected photos or equivalent
- third-party AI processing and storage or equivalent
- retention and deletion for AI Preview or equivalent

### Privacy Policy must clearly state:
1. What is collected
- selected user photo
- visible facial features or equivalent visual characteristics in the image
- generated preview result
- reference image when the evidence supports a multi-image preview flow

2. What it is used for
- generate the requested preview
- show the preview result in the app
- optionally let the user save the result to Photos

3. Who receives it
- name the concrete provider or host when inspect evidence exposes one

4. Where it is processed or stored
- provider cloud systems or equivalent
- temporary in-app cache on device when relevant
- saved copy in the user photo library when the user chooses to save

5. How long it is retained
- include a concrete duration or active-request retention statement
- prefer a precise window such as `up to 24 hours` when evidence or prior approved wording supports it

6. How it is deleted
- deleted when leaving the preview screen unless saved
- saved copy remains in Photos until the user deletes it
- support contact for deletion requests

7. Prohibited use statement
- explicitly state the data is not used for identity verification, face recognition, or biometric profiling

### Related page requirements
- `Intro.md`: first 255 characters must summarize the selected photo -> preview -> review -> optional save flow
- `index.html`: include a dedicated AI Preview module
- `Support.html`: include FAQ entries for AI Preview behavior and camera / photo-library / add-to-library permission reasons
- `Terms&Conditions.html`: restrict the feature to visual styling preview or similar consumer use and prohibit identity-verification, legal, medical, and safety-critical uses
