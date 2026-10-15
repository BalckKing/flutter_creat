"""Generate legal sections from normalized, evidenced project facts."""

from __future__ import annotations

from legal_facts import build_product_facts


def sentence_list(values: object) -> str:
    if isinstance(values, list):
        return ", ".join(str(value).strip() for value in values if str(value).strip())
    return str(values).strip() if values is not None else ""


def feature_labels(matrix: dict) -> list[str]:
    facts = matrix["facts"]
    labels = {
        "credential_auth": "credential-based sign-in",
        "local_session": "saved session preferences",
        "community_ugc": "community content",
        "messaging": "member messaging",
        "profile_view": "profiles",
        "photo_editing": "photo editing",
        "translation_text": "text translation",
        "translation_voice": "voice translation",
        "translation_image": "image translation",
        "ai_image_preview": "AI Preview",
        "location_features": "location features",
        "local_records": "saved records",
        "local_media": "imported media",
        "collections": "collections",
        "timeline_features": "timelines and history",
        "search_and_filters": "search and filters",
        "backup_export": "backup and export tools",
        "share_flow": "user-initiated sharing",
        "iap": "in-app purchases",
    }
    result = [label for name, label in labels.items() if facts.get(name) is True]
    if facts.get("ai") is True and not facts.get("ai_image_preview") and not facts.get("translation_image"):
        result.append("AI-assisted features")
    return result


def build_privacy(app_name: str, payload: dict, active: set[str]) -> list[dict]:
    matrix = build_product_facts(payload, active)
    facts = matrix["facts"]
    legal = payload.get("legal", {}) if payload.get("legal", {}).get("confirmed") is True else {}
    contact = str(payload.get("support_email") or "").strip()
    sections: list[dict] = []

    def add(title: str, body: str, bullets: list | None = None) -> None:
        if body:
            section = {"title": title, "body": body}
            if bullets:
                section["bullets"] = bullets
            sections.append(section)

    overview = f"This Privacy Policy explains how {app_name} handles information in its available features."
    if contact:
        overview += " It also explains how to contact the operator about privacy."
    add("Overview", overview)
    categories = []
    if facts["credential_auth"] is True:
        categories.append("Sign-in details and authentication records used for credential-based access.")
    if facts["profile_view"] is True:
        categories.append("Profile information that you choose to provide.")
    if facts["community_ugc"] is True:
        categories.append("User content submitted to community features.")
    if facts["messaging"] is True:
        categories.append("Messages that you choose to send through the app.")
    if facts["saved_notes"] is True:
        categories.append("Notes that you choose to save.")
    if facts["saved_work"] is True:
        categories.append("Work that you choose to save.")
    if facts.get("local_records") is True:
        categories.append("Records and content that you create or save in the app.")
    if facts.get("local_media") is True:
        categories.append("Photos or other media that you choose to import into the app.")
    if facts.get("collections") is True:
        categories.append("Collection details used to organize the content you choose to keep.")
    if facts["iap"] is True:
        categories.append("Transaction records used to provide in-app purchases.")
    if facts["local_session"] is True:
        categories.append("Saved session settings stored for repeat access on your device.")
    if contact:
        categories.append("Information in support messages that you choose to send by email.")
    add("Information We Collect", "The following information is processed when you use the corresponding available feature. A permission declaration alone does not mean information is uploaded.", categories)
    purposes = feature_labels(matrix)
    use_copy = f"We use relevant information to provide {sentence_list(purposes) if purposes else 'the functions you request in the app'}."
    if contact:
        use_copy += " We also use information you send when responding to support requests."
    add("How We Use Information", use_copy)
    if facts.get("backup_export") is True:
        add("User-Initiated Backup and Export", "You choose when to use the available backup or data export tools. Copies contain the content selected through that flow; protect any copies you keep or send to another destination.")
    if facts.get("share_flow") is True:
        add("User-Initiated Sharing", "You choose when to share content. The app passes the selected content to the system destination or share service you choose, which handles it under its own privacy practices.")
    if facts["credential_auth"] is True:
        auth_copy = "Sign-in details are processed to verify credential-based access."
        if contact:
            auth_copy += " Contact support for questions about authentication data."
        add("Sign-In and Credential Information", auth_copy)
    permissions = payload.get("permissions", {})
    media = []
    for name, label, signal in (("camera", "camera access", "camera"), ("photo_library", "photo-library access", "photo_library"), ("photo_library_add", "add-to-library access", "photo_library_add")):
        reason = permissions.get(name)
        if reason:
            media.append(f"The app declares {label} for this purpose: {reason}")
        elif payload.get("privacy_signals", {}).get(signal):
            media.append(f"The app declares {label}. You can manage this permission through device settings.")
    if media:
        add("Image and Media Access", " ".join(media))
    if facts["audio_recording"] is True or permissions.get("microphone"):
        add("Audio Processing", f"The app processes microphone input for its audio feature. {permissions.get('microphone', '')} You can manage microphone permission through device settings.")
    if facts["speech_recognition"] is True or permissions.get("speech_recognition"):
        add("Speech Recognition", f"The app uses speech recognition for spoken input. {permissions.get('speech_recognition', '')} Processing and retention follow the confirmed data-handling details for this feature.")
    location_reasons = [permissions[key] for key in ("location_when_in_use", "location_always") if permissions.get(key)]
    if facts["location_features"] is True or location_reasons or payload.get("privacy_signals", {}).get("location"):
        add("Location Features", "The app requests location access for the purpose stated in its system permission prompt. " + " ".join(location_reasons) + " You can change location permission through device settings.")
    if facts["iap"] is True:
        add("Purchases and Billing", "When you make an in-app purchase through Apple, the app processes relevant transaction records to provide the purchased item or access. Payment processing is handled through the App Store.")
    if facts["ai"] is True or facts["face_data"] is True:
        config = legal.get("ai", {})
        profile = payload.get("ai_signals", {}).get("review_profile", {})
        recipients = config.get("providers") or payload.get("ai_signals", {}).get("providers") or payload.get("ai_signals", {}).get("network_hosts", [])
        workflow = "AI Preview" if facts["ai_image_preview"] is True else "AI Translation" if facts["translation_image"] is True else "AI and Assisted Processing"
        body = f"{app_name} processes {sentence_list(config.get('inputs', [])) or 'the input submitted to the feature'} to provide the requested result."
        if facts["face_data"] is True:
            body += " A selected user photo or selected image may include visible facial features and other visual characteristics present in the image."
            body += " The app processes the generated preview result to generate the requested preview and present the result." if facts["ai_image_preview"] is True else " The app processes the translated result to extract readable text, generate the requested translation, and present the result."
            if profile.get("reference_image"):
                body += " The requested flow also uses a selected reference image."
        if config.get("send_condition"):
            body += " " + str(config["send_condition"])
        if facts["photo_export"] is True and facts["ai_image_preview"] is True:
            body += " You can choose to save the result to Photos."
        add(workflow + (" and Selected Photos" if facts["face_data"] else ""), body)
        processing = str(config.get("processing", ""))
        if recipients:
            processing = f"Submitted input is sent to {sentence_list(recipients)} for the requested AI processing. " + processing
        if config.get("equivalent_protection_confirmed") is True:
            processing += " These third-party recipients are confirmed by the operator to provide equivalent protection."
        if config.get("identity_processing") is False and facts["face_data"] is True:
            processing += " This data is not used for identity verification, face recognition, or biometric profiling."
        add("AI Processing and Storage", processing)
        add(workflow + " Retention and Deletion", " ".join(str(config.get(key, "")) for key in ("retention", "deletion")).strip())
    if facts["community_ugc"] is True:
        body = "We process user content and messages only in the corresponding available community or messaging features."
        if facts["moderation"] is True:
            body += " We review reports and moderate content under the service rules."
            if legal.get("review_time"):
                body += " " + str(legal["review_time"])
        add("Community, Safety, and User Content", body)
        if facts["terms_acceptance"] is True:
            add("Community Access and Terms Acceptance", "Before using the community features, you must review and accept the app's EULA or Terms & Conditions.")
    elif facts["messaging"] is True:
        add("Message Handling", "We process messages that you choose to send through the available messaging feature to deliver the conversation and respond to support or safety requests.")
    for name, title in (("tracking", "App Tracking Transparency"), ("analytics", "Analytics"), ("advertising", "Advertising")):
        if facts[name] is True:
            config = legal.get(name, {})
            body = f"We process {sentence_list(config.get('data_types', []))} for {sentence_list(config.get('purposes', []))}. Recipients are {sentence_list(config.get('providers', []))}."
            if name == "tracking" and config.get("authorization_gated") is True:
                body += " Tracking starts only after you grant permission through Apple's App Tracking Transparency system prompt. If you deny or revoke permission, tracking is not enabled. You can manage tracking permission in Settings."
            add(title, body)
    providers = legal.get("service_providers", [])
    network_services = legal.get("network_services", [])
    if providers or network_services:
        recipient_lines = [
            f"{service.get('host')}: {service.get('recipient_type').replace('_', ' ')}; data: {sentence_list(service.get('data_types'))}; purposes: {sentence_list(service.get('purposes'))}."
            for service in network_services if isinstance(service, dict)
        ]
        recipient_lines.extend(
            f"{provider.get('name', '')}: {sentence_list(provider.get('data_types', []))}; {provider.get('purpose', '')}."
            for provider in providers if isinstance(provider, dict)
        )
        add("Sharing and Service Providers", "Information is shared with the following confirmed recipients for the stated purposes.", recipient_lines)
    retention = facts["data_retention"]
    if retention != "unknown":
        add("Data Retention", sentence_list(retention))
    rights = f"Contact {contact} with access, deletion, or other privacy requests." if contact else "You can manage requested permissions through your operating system settings."
    if facts["profile_edit"] is True:
        rights += " You can update profile information in the app."
    if permissions:
        rights += " You can manage requested permissions through device settings."
    add("Your Rights and Choices", rights)
    audience = facts["children_targeted"]
    if audience is False:
        body = f"{app_name} is not directed to children."
        if contact:
            body += f" Contact {contact} if you believe a child has provided personal information requiring review."
        add("Children's Privacy", body)
    elif audience is True:
        add("Children's Privacy", str(legal.get("children_policy", "")))
    add("Changes to This Policy", "Changes will be published on this page with an updated policy date.")
    if contact:
        add("Contact", f"For privacy questions or requests, contact {contact}.")
    return sections


def build_terms(app_name: str, payload: dict, active: set[str]) -> list[dict]:
    matrix = build_product_facts(payload, active)
    facts = matrix["facts"]
    legal = payload.get("legal", {}) if payload.get("legal", {}).get("confirmed") is True else {}
    sections = []

    def add(title: str, body: str) -> None:
        if body:
            sections.append({"title": title, "body": body})

    labels = feature_labels(matrix)
    add("Definitions", f"The Service means {app_name} and its available functions" + (f", including {sentence_list(labels)}." if labels else "."))
    add("Acceptance of Terms", f"By using {app_name}, you accept these Terms & Conditions.")
    usage = "Use the Service lawfully. Do not interfere with its operation or submit unlawful, infringing, deceptive, or harmful material."
    minimum_age = facts["minimum_age"]
    if isinstance(minimum_age, int) and not isinstance(minimum_age, bool):
        usage += f" You must be {minimum_age} or older to use the features covered by this age policy."
    add("Use of the Service", usage)
    if facts["credential_auth"] is True:
        add("User Accounts", "You are responsible for your sign-in details and activity through your credential-based access. Keep those access details secure.")
    elif facts["local_session"] is True:
        add("Saved Access", "Saved session settings are maintained on your device. Protect your device and do not misuse the Service.")
    owner = facts["operator_name"]
    property_body = f"The Service's original software, branding and design belong to {owner} or its licensors." if owner != "unknown" else "Rights in the Service's original software, branding and design are reserved by their respective rights holders."
    if facts["community_ugc"] is True:
        property_body += " You retain rights in content you submit and grant the permissions needed to display and process it within the available community features."
    elif facts["photo_editing"] is True or facts["saved_work"] is True:
        property_body += " You retain rights in materials you import and authorize processing only to provide the functions you request."
    add("Intellectual Property", property_body)
    if facts["community_ugc"] is True:
        body = "You are responsible for user content or messages you submit. Harassment, abusive behavior, illegal content and infringement are prohibited."
        if facts["reporting"] is True:
            body += " Use the reporting controls to report content or members."
        if facts["blocking"] is True:
            body += " You can block other members through the app's blocking controls."
        if facts["moderation"] is True:
            body += " We review reports and may remove content, restrict access, or block abusive users under the service rules."
        if legal.get("review_time"):
            body += " " + str(legal["review_time"])
        if contact:
            body += " Contact support if you need help."
        add("User Content and Community Rules", body)
    elif facts["messaging"] is True:
        message_copy = "Use messaging lawfully and do not send unlawful, abusive, deceptive, or harmful material."
        if contact:
            message_copy += " Contact support if you need help with a message or conversation."
        add("Message Use", message_copy)
    if facts["iap"] is True:
        body = "In-app purchases are processed through Apple and the App Store. Review the product details and price before confirming a purchase. Refund requests are handled under the App Store's applicable policies and your statutory rights."
        if facts["subscription"] is True:
            body += " For subscriptions, review the renewal terms shown before purchase and manage renewal or cancellation in your App Store subscription settings."
        if facts["consumable_iap"] is True:
            body += " Consumable items are used up through the corresponding feature."
        if facts["non_consumable_iap"] is True:
            body += " Non-consumable purchases unlock the item or feature identified in the product details."
        if facts["virtual_goods"] is True:
            body += " Virtual goods have no cash value and are not redeemable for cash."
        if facts["restore_purchases"] is True:
            body += " Use the app's restore purchases flow for eligible transactions."
        add("Purchases", body)
    if facts["ai"] is True:
        recipients = legal.get("ai", {}).get("providers", [])
        if recipients:
            provider_clause = f"AI-assisted features may send submitted material to {sentence_list(recipients)} for processing as described in the Privacy Policy."
        else:
            provider_clause = "AI-assisted features use the processing services identified in the Privacy Policy."
        body = f"{provider_clause} Output may vary and is not guaranteed accurate. You are responsible for submitted material and must review results before relying on them."
        if facts["ai_image_preview"] is True:
            body += " AI Preview is intended for visual styling preview and consumer entertainment."
        elif facts["translation_image"] is True:
            body += " AI-assisted translation is intended for consumer translation and informational content."
        if facts["face_data"] is True:
            body += " Do not use this visual workflow for identity verification, face recognition, biometric profiling, legal advice, medical decisions, or safety-critical purposes."
        add("AI-Assisted Features and Output Limitations", body)
    if any(facts[name] is True for name in ("translation_text", "translation_image", "translation_voice")):
        add("Translation Accuracy", "Translation results may vary with input quality, language and context. Review important information before relying on a result.")
    add("Disclaimers and Limitation of Liability", "The Service is provided on an as-available basis. To the extent permitted by applicable law, warranties and liability for indirect or consequential damages are limited. Nothing in these Terms excludes rights that cannot lawfully be excluded.")
    availability = "Available features may change or become unavailable. These Terms do not remove applicable statutory rights."
    if facts["iap"] is True:
        availability += " Applicable purchase rights are also preserved."
    add("Service Availability", availability)
    add("Amendments", "Updated Terms will be published on this page with an updated date. Review material changes before continuing to use the Service.")
    if facts["operator_jurisdiction"] != "unknown":
        add("Governing Law", f"These Terms are governed by {facts['operator_jurisdiction']}, subject to applicable mandatory consumer protections.")
    contact = str(payload.get("support_email") or "").strip()
    if contact:
        add("Contact", f"For questions about these Terms, contact {contact}.")
    return sections


def build_faq(payload: dict, active: set[str]) -> list[dict]:
    facts = build_product_facts(payload, active)["facts"]
    contact = str(payload.get("support_email") or "").strip()
    result = []
    if contact:
        result.append({"title": "How can I get help?", "body": f"Email {contact} and describe your question."})
    if facts["credential_auth"] is True and contact:
        result.append({"title": "How can I get sign-in help?", "body": "Contact support with the sign-in issue. Do not send your password."})
    if facts["iap"] is True:
        body = "Review your App Store transaction details and contact support if purchased access is not available." if contact else "Review your App Store transaction details and the purchase details shown in the app."
        if facts["restore_purchases"] is True:
            body += " Use the restore purchases flow for eligible transactions."
        result.append({"title": "Where can I get purchase help?", "body": body})
    if facts["ai_image_preview"] is True:
        body = "Choose the input for AI Preview, request the feature, and review the generated preview result."
        if facts["photo_export"] is True:
            body += " You can choose to save the result to Photos."
        result.append({"title": "How does AI Preview work?", "body": body})
    if facts["translation_image"] is True:
        result.append({"title": "How does image translation work?", "body": "Choose an image containing readable text, request image translation, and review the translated result."})
    permissions = payload.get("permissions", {})
    labels = {"camera": "camera", "photo_library": "photo-library", "photo_library_add": "add-to-library", "microphone": "microphone", "speech_recognition": "speech recognition", "location_when_in_use": "location"}
    for key, label in labels.items():
        if key in permissions:
            result.append({"title": f"Why does the app request {label} access?", "body": f"The app declares this permission for the purpose stated in the system prompt: {permissions[key]} You can manage the permission through device settings."})
    if facts["reporting"] is True:
        report_body = "Use the app's report controls."
        if contact:
            report_body += " You can also email support with the relevant content details."
        result.append({"title": "How can I report a concern?", "body": report_body})
    if facts["blocking"] is True:
        result.append({"title": "How can I block a member?", "body": "Use the app's block controls to limit interaction with that member."})
    return result
