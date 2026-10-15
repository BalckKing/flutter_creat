"""Evidence normalization for conditional listing and legal copy."""

from __future__ import annotations

import json
import os
import plistlib
import re
from pathlib import Path


SOURCE_PATTERNS = {
    "photo_capture": r"ImageSource\.camera|AVCaptureSession\s*\(|availableCameras\s*\(",
    "photo_import": r"ImageSource\.gallery|PHPickerViewController\s*\(|PhotosPicker\s*\(|pickMultiImage\s*\(|pickImage\s*\(",
    "photo_export": r"UIImageWriteToSavedPhotosAlbum\s*\(|PHAssetChangeRequest\.creationRequestForAsset|ImageGallerySaver\.(?:saveImage|saveFile)\s*\(|(?:saveImageToGallery|saveImageToPhotos)\s*\(",
    "audio_recording": r"AVAudioRecorder\s*\(|(?:startRecording|recordAudio)\s*\(",
    "speech_recognition": r"SFSpeechRecognizer\s*\(|SpeechToText\s*\(|speechToText\.listen\s*\(",
    "profile_edit": r"(?:editProfile|updateProfile|saveProfile)\s*\(",
    "reporting": r"(?:reportContent|reportPost|reportUser|submitReport)\s*\(",
    "blocking": r"(?:blockUser|blockMember|blockProfile)\s*\(",
    "restore_purchases": r"(?:restorePurchases|restoreCompletedTransactions|AppStore\.sync)\s*\(",
    "subscription": r"\.autoRenewable\b|\.nonRenewable\b|ProductType\.(?:autoRenewable|nonRenewableSubscription)\b",
    "consumable_iap": r"\.consumable\b|buyConsumable\s*\(",
    "non_consumable_iap": r"\.nonConsumable\b|buyNonConsumable\s*\(",
    "att_request_detected": r"(?:requestTrackingAuthorization|requestTrackingPermission)\s*\(",
    "att_authorization_gate_detected": r"trackingAuthorizationStatus|TrackingStatus\.authorized|ATTrackingManager\.AuthorizationStatus",
    "idfa_access_detected": r"\.advertisingIdentifier\b|(?:getAdvertisingIdentifier|advertisingIdentifier)\s*\(",
    "analytics_active": r"(?:Analytics|FirebaseAnalytics|Amplitude|Mixpanel)\.(?:logEvent|track|trackEvent)\s*\(|(?:analytics|mixpanel|amplitude)\.(?:logEvent|track|trackEvent)\s*\(",
    "advertising_active": r"(?:GADBannerView|GADInterstitialAd|BannerAd|InterstitialAd|RewardedAd)\s*(?:\(|\.load\s*\()",
}
ANALYTICS_SDKS = ("firebase_analytics", "firebaseanalytics", "amplitude", "mixpanel", "appsflyer", "adjust")
TRACKING_SDKS = ("appsflyer", "adjust", "facebook", "fbsdk", "google_mobile_ads", "googlemobileads")
PRODUCT_TYPES = {
    "Consumable": "consumable_iap",
    "NonConsumable": "non_consumable_iap",
    "AutoRenewableSubscription": "subscription",
    "NonRenewingSubscription": "subscription",
}


def inspect_legal_signals(app_root: Path, ignored: set[str]) -> dict:
    matches: dict[str, list[dict]] = {name: [] for name in SOURCE_PATTERNS}
    manifests: list[dict] = []
    conflicts: list[str] = []
    for directory, directories, filenames in os.walk(app_root, followlinks=False):
        directories[:] = sorted(name for name in directories if name.lower() not in ignored and not name.startswith(".") and not Path(directory, name).is_symlink())
        for filename in sorted(filenames):
            path = Path(directory, filename)
            if path.is_symlink():
                continue
            relative_path = str(path.relative_to(app_root))
            if path.suffix in {".dart", ".swift", ".m", ".mm"}:
                text = path.read_text(encoding="utf-8", errors="ignore")
                text = re.sub(r"/\*.*?\*/", lambda match: "\n" * match.group(0).count("\n"), text, flags=re.DOTALL)
                text = re.sub(r"(?m)^\s*//[^\n]*", "", text)
                for name, pattern in SOURCE_PATTERNS.items():
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        matches[name].append({"file": relative_path, "line": text.count("\n", 0, match.start()) + 1, "match": match.group(0), "kind": "code"})
            elif filename == "PrivacyInfo.xcprivacy":
                try:
                    with path.open("rb") as handle:
                        manifest = plistlib.load(handle)
                    manifests.append({"file": relative_path, "tracking": manifest.get("NSPrivacyTracking"), "tracking_domains": manifest.get("NSPrivacyTrackingDomains", [])})
                except (OSError, ValueError, plistlib.InvalidFileException) as error:
                    conflicts.append(f"{relative_path}: invalid privacy manifest ({error})")
            elif path.suffix == ".storekit":
                try:
                    catalog = json.loads(path.read_text(encoding="utf-8"))
                    for product in catalog.get("products", []):
                        fact = PRODUCT_TYPES.get(product.get("type"))
                        if fact:
                            matches[fact].append({"file": relative_path, "kind": "storekit", "product_id": product.get("productID", "")})
                    if any(group.get("subscriptions") for group in catalog.get("subscriptionGroups", [])):
                        matches["subscription"].append({"file": relative_path, "kind": "storekit"})
                except (OSError, ValueError, AttributeError) as error:
                    conflicts.append(f"{relative_path}: invalid StoreKit catalog ({error})")
    return {"matches": matches, "privacy_manifests": manifests, "conflicts": conflicts, "inspection_complete": True}


def disclosure_required(payload: dict, key: str) -> bool:
    signals = payload.get(key, {})
    if not isinstance(signals, dict):
        return False
    if "disclosure_required" in signals:
        return signals["disclosure_required"] is True
    if "claimable" in signals:
        return signals["claimable"] is True
    return bool(signals.get("active") and signals.get("user_reachable", True))


def active_features(payload: dict) -> set[str]:
    result = set()
    for name, candidate in payload.get("capability_candidates", {}).items():
        if not isinstance(candidate, dict):
            continue
        try:
            supported = float(candidate.get("score", 0)) >= 1
        except (ValueError, TypeError):
            supported = False
        if supported and candidate.get("user_reachable", True):
            result.add(name)
    if not disclosure_required(payload, "ai_signals"):
        result -= {"ai_chat", "ai_image_generation"}
    if payload.get("translation_signals") and not disclosure_required(payload, "translation_signals"):
        result -= {"translate_text", "translate_voice"}
    if payload.get("messaging_signals", {}).get("real_user_chat") is False:
        result.discard("messaging")
    if payload.get("beauty_editing_signals", {}).get("disclosure_required") is False:
        result.discard("beauty_editing")
    return result


def build_product_facts(payload: dict, active: set[str] | None = None) -> dict:
    active = active_features(payload) if active is None else active
    privacy = payload.get("privacy_signals", {})
    permissions = payload.get("permissions", {})
    signals = payload.get("legal_signals", {})
    legal = payload.get("legal", {})
    if not isinstance(legal, dict):
        legal = {}
    legal_signals = payload.get("legal_signals", {})
    matches = legal_signals.get("matches", {}) if isinstance(legal_signals, dict) else {}
    if not isinstance(matches, dict):
        matches = {}
    confirmed = legal.get("confirmed") is True
    declared = legal.get("features", {}) if confirmed else {}
    facts: dict[str, object] = {}
    evidence: dict[str, list] = {}
    conflicts = list(signals.get("conflicts", []))
    unknowns: list[dict] = []

    def record(name: str, value: object, sources: list) -> None:
        facts[name] = value
        evidence[name] = sources
        if value == "unknown":
            unknowns.append({"field": name, "reason": "Evidence does not establish actual runtime behavior.", "evidence": sources})

    for name in SOURCE_PATTERNS:
        sources = list(matches.get(name, []))
        record(name, bool(sources), sources)
    capability_flags = {
        "credential_auth": payload.get("access_signals", {}).get("mode") == "credential_account",
        "local_session": payload.get("access_signals", {}).get("mode") == "local_session",
        "community_ugc": (
            bool({"feed", "post_creation"} & active)
            or (
                payload.get("privacy_signals", {}).get("user_content") is True
                and not isinstance(payload.get("capability_candidates"), dict)
            )
        ),
        "messaging": "messaging" in active or payload.get("messaging_signals", {}).get("real_user_chat") is True,
        "profile_view": "profile" in active,
        "photo_editing": "beauty_editing" in active,
        "translation_text": "translate_text" in active or disclosure_required(payload, "translation_signals"),
        "translation_voice": "translate_voice" in active,
        "ai": disclosure_required(payload, "ai_signals"),
        "iap": bool(payload.get("iap_codes")) or privacy.get("payments") is True or "recharge" in active,
        "location_features": "location" in active,
    }
    for name, value in capability_flags.items():
        record(name, value, [{"kind": "capability", "source": "inspect", "features": sorted(active)}])
    project_profile = payload.get("project_profile", {})
    profile_features = project_profile.get("features", []) if isinstance(project_profile, dict) else []
    profile_ids = {
        str(feature.get("id"))
        for feature in profile_features
        if isinstance(feature, dict) and feature.get("status") == "confirmed"
    }
    profile_fact_map = {
        "local_records": "journal_or_notes" in profile_ids,
        "local_media": "photo_media" in profile_ids,
        "collections": "collections" in profile_ids,
        "timeline_features": "timeline_history" in profile_ids,
        "search_and_filters": "search_and_filters" in profile_ids,
        "backup_export": "backup_and_export" in profile_ids,
        "share_flow": "sharing" in profile_ids,
    }
    for name, value in profile_fact_map.items():
        record(name, value, [{"kind": "project_profile", "source": "confirmed product surface"}] if value else [])
    destinations = payload.get("network_destinations", [])
    record("network_destinations", list(destinations) if isinstance(destinations, list) else [], [{"kind": "network_destination", "host": host} for host in destinations] if isinstance(destinations, list) else [])
    profile = payload.get("ai_signals", {}).get("review_profile", {})
    face_active = profile.get("needs_face_data_clauses") is True and (facts["ai"] is True or disclosure_required(payload, "translation_signals"))
    record("face_data", face_active, [{"kind": "inspect", "source": "ai_signals.review_profile"}] if face_active else [])
    record("ai_image_preview", face_active and profile.get("workflow_kind", "preview") != "translation_face_visibility", evidence["face_data"])
    record("translation_image", face_active and profile.get("workflow_kind") == "translation_face_visibility", evidence["face_data"])
    record("anonymous_use", not facts["credential_auth"] and not facts["local_session"], evidence["credential_auth"])
    for name in ("photo_upload", "remote_audio_processing", "moderation", "terms_acceptance", "saved_notes", "saved_work", "virtual_goods"):
        permission_evidence = privacy.get("photo_library") is True and facts["community_ugc"] is True
        uncertain = (name == "photo_upload" and permission_evidence) or (name == "remote_audio_processing" and bool(matches.get("audio_recording")))
        record(name, "unknown" if uncertain else False, [{"kind": "permission", "source": "possible feature usage"}] if uncertain else [])
    for name, value in matches.items():
        if name in facts and value:
            record(name, True, list(value))
    for name, value in declared.items():
        if name not in facts or not isinstance(value, bool):
            conflicts.append(f"legal.features.{name}: unrecognized feature or non-boolean value")
            continue
        if value is False and facts.get(name) is True:
            conflicts.append(f"legal.features.{name}: contradicts code or capability evidence {evidence[name]}")
            continue
        record(name, value, evidence.get(name, []) + [{"kind": "confirmed", "source": f"legal.features.{name}"}])
    for field, permission in (("photo_capture", "camera"), ("photo_import", "photo_library"), ("audio_recording", "microphone"), ("location_features", "location")):
        if declared.get(field) is False and privacy.get(permission) is True:
            conflicts.append(f"legal.features.{field}: contradicts the {permission} permission declaration")

    tracking = legal.get("tracking", {}) if confirmed else {}
    manifests = signals.get("privacy_manifests", [])
    tracking_sources = [item for item in manifests if item.get("tracking") is True or item.get("tracking_domains")]
    dep_blob = " ".join(payload.get("dependencies", [])).lower()
    sdk_candidates = [name for name in TRACKING_SDKS if name in dep_blob]
    att_declared = "tracking" in permissions or privacy.get("tracking") is True
    tracking_candidate = att_declared or bool(tracking_sources or sdk_candidates or matches.get("idfa_access_detected"))
    tracking_state = tracking.get("enabled", "unknown" if tracking_candidate else False)
    if not isinstance(tracking_state, bool) and tracking_state != "unknown":
        conflicts.append("legal.tracking.enabled: expected true or false")
        tracking_state = "unknown"
    if tracking_state is False and (tracking_sources or matches.get("idfa_access_detected")):
        conflicts.append("legal.tracking.enabled: contradicts privacy manifest or IDFA evidence")
    record("tracking", tracking_state, tracking_sources + list(matches.get("idfa_access_detected", [])) + ([{"kind": "permission", "source": "NSUserTrackingUsageDescription"}] if att_declared else []) + ([{"kind": "sdk_candidate", "names": sdk_candidates}] if sdk_candidates else []) + ([{"kind": "confirmed", "source": "legal.tracking.enabled"}] if "enabled" in tracking else []))
    analytics = legal.get("analytics", {}) if confirmed else {}
    analytics_candidate = bool(matches.get("analytics_active")) or any(name in dep_blob for name in ANALYTICS_SDKS)
    record("analytics", analytics.get("enabled", "unknown" if analytics_candidate else False), list(matches.get("analytics_active", [])))
    advertising = legal.get("advertising", {}) if confirmed else {}
    record("advertising", advertising.get("enabled", "unknown" if matches.get("advertising_active") else False), list(matches.get("advertising_active", [])))
    iap_types = legal.get("iap_types", []) if confirmed else []
    for name in ("subscription", "consumable_iap", "non_consumable_iap"):
        if name in iap_types:
            record(name, True, [{"kind": "confirmed", "source": "legal.iap_types"}])
    if any(facts[name] is True for name in ("subscription", "consumable_iap", "non_consumable_iap")):
        record("iap", True, evidence["iap"] + [{"kind": "product_type", "source": "code or StoreKit catalog or confirmed legal.iap_types"}])
    record("iap_type", "known" if any(facts[name] is True for name in ("subscription", "consumable_iap", "non_consumable_iap")) else "unknown" if facts["iap"] else "none", evidence["iap"])
    for name in ("children_targeted", "minimum_age", "data_retention", "operator_name", "operator_jurisdiction"):
        key = name
        value = legal.get("operator_jurisdiction", legal.get("jurisdiction", "unknown")) if confirmed and name == "operator_jurisdiction" else legal.get(key, "unknown") if confirmed else "unknown"
        if name == "children_targeted" and not isinstance(value, bool):
            value = "unknown"
        record(name, value, [{"kind": "confirmed", "source": f"legal.{key}"}] if value != "unknown" else [])
    if "unknown" in facts.values():
        unknowns = [item for item in unknowns if facts[item["field"]] == "unknown"]
    return {"facts": facts, "evidence": evidence, "unknowns": unknowns, "conflicts": conflicts}


def legal_fact_errors(payload: dict) -> list[str]:
    matrix = build_product_facts(payload)
    facts = matrix["facts"]
    errors = list(matrix["conflicts"])
    signals = payload.get("legal_signals", {})
    matches = signals.get("matches", {}) if isinstance(signals, dict) else {}
    if not isinstance(matches, dict):
        matches = {}
    legal = payload.get("legal", {})
    if not isinstance(legal, dict):
        return errors + ["legal: expected a confirmed legal configuration object"]
    for product_type in legal.get("iap_types", []):
        if product_type not in {"subscription", "consumable_iap", "non_consumable_iap"}:
            errors.append(f"legal.iap_types: unsupported type {product_type}")
    if facts["community_ugc"] is True:
        if not isinstance(facts["minimum_age"], int) or isinstance(facts["minimum_age"], bool) or not 1 <= facts["minimum_age"] <= 120:
            errors.append("legal.minimum_age: confirm the actual community age policy")
        for field in ("reporting", "blocking", "moderation", "terms_acceptance"):
            if facts[field] is not True:
                errors.append(f"legal.features.{field}: community safety capability is not established")
    if facts["iap"] is True and facts["iap_type"] == "unknown":
        errors.append("legal.iap_types: purchase identifiers do not establish the product type")
    for area in ("tracking", "analytics", "advertising"):
        if facts[area] == "unknown":
            errors.append(f"legal.{area}.enabled: verify SDK runtime data use before publication")
        elif facts[area] is True:
            config = legal.get(area, {})
            for field in ("data_types", "purposes", "providers"):
                if not config.get(field):
                    errors.append(f"legal.{area}.{field}: required for actual data processing")
            if area == "tracking" and config.get("authorization_gated") is not True:
                errors.append("legal.tracking.authorization_gated: ATT authorization must be verified, not inferred from an API name")
            if area == "tracking" and not matches.get("att_request_detected") and not config.get("authorization_evidence"):
                errors.append("legal.tracking.authorization_evidence: provide detectable ATT request evidence or a confirmed native/plugin integration reference")
    if facts["ai"] is True or facts["face_data"] is True:
        config = legal.get("ai", {})
        for field in ("inputs", "processing", "retention", "deletion", "send_condition"):
            if not config.get(field):
                errors.append(f"legal.ai.{field}: confirm the actual AI data flow")
        if config.get("equivalent_protection_confirmed") is not True:
            errors.append("legal.ai.equivalent_protection_confirmed: verify recipient protection instead of asserting a contract")
        providers = payload.get("ai_signals", {}).get("providers", []) + payload.get("ai_signals", {}).get("network_hosts", [])
        if not providers and not config.get("providers"):
            errors.append("legal.ai.providers: confirm the actual AI recipient")
        if facts["face_data"] is True and config.get("identity_processing") is not False:
            errors.append("legal.ai.identity_processing: verify whether face recognition or biometric processing occurs")
    return errors


def legal_fact_review_items(payload: dict) -> list[str]:
    """Return facts needing operator review without blocking local generation or About deployment."""
    matrix = build_product_facts(payload)
    facts = matrix["facts"]
    legal = payload.get("legal", {})
    if not isinstance(legal, dict):
        return ["legal: operator review is needed for the legal configuration object"]

    items: list[str] = []
    for field in ("operator_name", "operator_jurisdiction", "children_targeted", "data_retention"):
        if facts[field] == "unknown" or facts[field] == "":
            items.append(f"legal.{field}: confirm before final legal publication")
    if facts["children_targeted"] is True and not legal.get("children_policy"):
        items.append("legal.children_policy: confirm the child-data policy before final legal publication")
    if facts["community_ugc"] is True:
        if not isinstance(facts["minimum_age"], int) or isinstance(facts["minimum_age"], bool) or not 1 <= facts["minimum_age"] <= 120:
            items.append("legal.minimum_age: confirm the actual community age policy")

    for provider in legal.get("service_providers", []):
        if not isinstance(provider, dict) or not all(provider.get(key) for key in ("name", "data_types", "purpose")):
            items.append("legal.service_providers: complete recipient name, data types, and purpose before final legal publication")
    destinations = payload.get("network_destinations", [])
    network_services = legal.get("network_services", [])
    service_hosts = {str(item.get("host", "")).lower() for item in network_services if isinstance(item, dict)}
    missing_hosts = [host for host in destinations if str(host).lower() not in service_hosts]
    if missing_hosts:
        items.append("legal.network_services: review recipient type, data types, and purpose for: " + ", ".join(map(str, missing_hosts)))
    for service in network_services:
        if not isinstance(service, dict) or not service.get("host") or service.get("recipient_type") not in {"first_party", "third_party"} or not service.get("data_types") or not service.get("purposes"):
            items.append("legal.network_services: complete host, recipient type, data types, and purposes before final legal publication")
    return list(dict.fromkeys(items))
