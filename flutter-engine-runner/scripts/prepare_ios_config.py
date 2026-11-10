#!/usr/bin/env python3
"""Prepare Flutter iOS source configuration; never claim a build was verified."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import tempfile


FRAMEWORK = "ios/Flutter/AppFrameworkInfo.plist"
PODFILE = "ios/Podfile"
BEGIN = "# BEGIN CODEX IOS PERMISSIONS"
END = "# END CODEX IOS PERMISSIONS"

# Parse only: evaluating a Podfile could run arbitrary project setup during a check.
RUBY_HOOKS = r"""require 'json'
begin
  root = RubyVM::AbstractSyntaxTree.parse(STDIN.read)
  hooks = []
  walk = lambda do |node|
    return unless node.is_a?(RubyVM::AbstractSyntaxTree::Node)
    if node.type == :ITER
      call = node.children[0]
      if call.type == :FCALL && call.children[0] == :post_install
        hooks << [node.first_lineno, node.last_lineno]
      end
    end
    node.children.each { |child| walk.call(child) }
  end
  walk.call(root)
  puts JSON.generate(hooks)
rescue SyntaxError => error
  warn error.message
  exit 1
end
"""


class ConfigError(Exception):
    pass


def project_path(root, relative, *, must_exist=True):
    """Reject symlink components, including backup directories."""
    path = root
    for component in Path(relative).parts:
        path = path / component
        if path.is_symlink():
            raise ConfigError(f"Refusing symlink: {path}")
    if must_exist and not path.is_file():
        raise ConfigError(f"Missing required file: {relative}; restore it from the current "
                          "Flutter SDK template while preserving native customization.")
    return path


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d+(?:\.\d+){0,2}", value):
        raise ConfigError(f"Invalid MinimumOSVersion/iOS version: {value!r}")
    parts = tuple(int(part) for part in value.split("."))
    if parts[0] < 1:
        raise ConfigError(f"Invalid iOS version: {value!r}")
    return parts + (0,) * (3 - len(parts))


def framework_content(original, minimum):
    try:
        data = plistlib.loads(original)
    except Exception as error:
        raise ConfigError(f"Invalid {FRAMEWORK}: {error}") from error
    if not isinstance(data, dict):
        raise ConfigError(f"{FRAMEWORK} must contain a dictionary")
    # Preserve a higher existing value, including a user's incorrectly cased key.
    keys = [key for key in data if key.lower() == "minimumosversion"]
    candidates = [minimum] + [data[key] for key in keys]
    selected = max(candidates, key=version)
    if keys == ["MinimumOSVersion"] and data["MinimumOSVersion"] == selected:
        return original
    for key in keys:
        del data[key]
    data["MinimumOSVersion"] = selected
    format_kind = plistlib.FMT_BINARY if original.startswith(b"bplist00") else plistlib.FMT_XML
    return plistlib.dumps(data, fmt=format_kind, sort_keys=False)


def ruby_run(arguments, text):
    ruby = shutil.which("ruby")
    if not ruby:
        raise ConfigError("Ruby is required to parse the CocoaPods Podfile")
    try:
        result = subprocess.run([ruby, *arguments], input=text, text=True,
                                capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ConfigError(f"Cannot validate Podfile: {error}") from error
    if result.returncode:
        raise ConfigError(f"Podfile Ruby validation failed: {result.stderr.strip()}")
    return result.stdout


def permission_block(installer, access, indent):
    photos = 1 if access == "read-write" else 0
    add_only = 1 if access == "add-only" else 0
    block = r"""# BEGIN CODEX IOS PERMISSIONS
INSTALLER.pods_project.targets.each do |ios_permission_target|
  next unless ios_permission_target.name == 'permission_handler_apple'
  ios_permission_target.build_configurations.each do |ios_permission_config|
    ios_permission_flags = ios_permission_config.build_settings['GCC_PREPROCESSOR_DEFINITIONS']
    case ios_permission_flags
    when nil
      ios_permission_flags = []
    when String
      ios_permission_flags = [ios_permission_flags]
    when Array
      ios_permission_flags = ios_permission_flags.dup
    else
      raise 'Unsupported permission_handler_apple GCC_PREPROCESSOR_DEFINITIONS'
    end
    ios_permission_flags = ios_permission_flags.map do |ios_permission_flag|
      ios_permission_flag.to_s.gsub(/(?:\A|\s)(?:PERMISSION_PHOTOS|PERMISSION_PHOTOS_ADD_ONLY|PERMISSION_APP_TRACKING_TRANSPARENCY)(?:\s*=\s*[^\s]+)?(?=\s|\z)/, ' ').strip
    end.reject(&:empty?)
    unless ios_permission_flags.any? { |ios_permission_flag| ios_permission_flag.include?('$(inherited)') }
      ios_permission_flags.unshift('$(inherited)')
    end
    ios_permission_flags += [
      'PERMISSION_PHOTOS=PHOTOS_VALUE',
      'PERMISSION_PHOTOS_ADD_ONLY=ADD_ONLY_VALUE',
      'PERMISSION_APP_TRACKING_TRANSPARENCY=0',
    ]
    ios_permission_config.build_settings['GCC_PREPROCESSOR_DEFINITIONS'] = ios_permission_flags
  end
end
# END CODEX IOS PERMISSIONS
"""
    block = block.replace("INSTALLER", installer).replace("PHOTOS_VALUE", str(photos))
    block = block.replace("ADD_ONLY_VALUE", str(add_only))
    return "".join(indent + line + "\n" for line in block.splitlines())


def podfile_content(original, access):
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ConfigError("Podfile is not UTF-8") from error
    newline = "\r\n" if "\r\n" in text else "\n"
    text = text.replace("\r\n", "\n")
    if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
        raise ConfigError("Podfile has malformed or multiple managed permission blocks")
    if BEGIN in text:
        pattern = rf"^[ \t]*{re.escape(BEGIN)}\n.*?^[ \t]*{re.escape(END)}\n"
        text, count = re.subn(pattern, "", text, flags=re.M | re.S)
        if count != 1:
            raise ConfigError("Cannot safely replace managed Podfile permission block")
    hooks = json.loads(ruby_run(["-e", RUBY_HOOKS], text))
    if len(hooks) != 1:
        raise ConfigError("Podfile needs exactly one post_install hook; restore/merge the "
                          "actual Flutter CocoaPods hook before preparing permissions")
    start, end = hooks[0]
    lines = text.splitlines(keepends=True)
    header = re.fullmatch(r"([ \t]*)post_install\s+do\s*\|([a-z_][a-zA-Z0-9_]*)\|\s*(?:#.*)?\n?",
                          lines[start - 1])
    if not header or not re.fullmatch(r"[ \t]*end[ \t]*(?:#.*)?\n?", lines[end - 1]):
        raise ConfigError("Unsupported post_install syntax; preserve it and configure macros manually")
    lines.insert(end - 1, permission_block(header[2], access, header[1] + "  "))
    updated = "".join(lines)
    ruby_run(["-c"], updated)
    return updated.replace("\n", newline).encode("utf-8")


def atomic_write(path, content, mode):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".ios-config-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def apply_changes(root, changes):
    backup_dir = project_path(root, ".work/ios-config-backup", must_exist=False)
    if backup_dir.exists() and not backup_dir.is_dir():
        raise ConfigError("iOS configuration backup path must be a directory")
    backup_dir.mkdir(parents=True, exist_ok=True)
    # Back up every planned input before replacing any source file.
    for relative, path, before, after in changes:
        name = relative.replace("/", "--") + "." + hashlib.sha256(before).hexdigest() + ".bak"
        backup = project_path(root, str(backup_dir.relative_to(root) / name), must_exist=False)
        if backup.exists():
            if backup.read_bytes() != before:
                raise ConfigError(f"Backup content mismatch: {backup}")
        else:
            with backup.open("xb") as stream:
                stream.write(before)
    modes = {relative: path.stat().st_mode & 0o777 for relative, path, _, _ in changes}
    written = []
    try:
        for relative, path, before, after in changes:
            if path.read_bytes() != before:
                raise ConfigError(f"File changed during preparation: {relative}")
            atomic_write(path, after, modes[relative])
            written.append((relative, path, before))
    except Exception:
        for relative, path, before in reversed(written):
            atomic_write(path, before, modes[relative])
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--photo-access", choices=("none", "picker", "read-write", "add-only"), required=True,
                        help="Choose from the actual API; a system picker does not require library access")
    parser.add_argument("--permission-handler", action="store_true",
                        help="Only for permission_handler_apple integrated through CocoaPods")
    parser.add_argument("--minimum-ios", default="15.6", help="Never lowers an existing higher source value")
    parser.add_argument("--apply", action="store_true", help="Back up and apply; default only checks")
    args = parser.parse_args()
    result = {"scope": "source-preparation", "build_verified": False, "changed": [],
              "required_changes": [], "errors": []}
    try:
        root = args.project_root.resolve(strict=True)
        project_path(root, "pubspec.yaml")
        if version(args.minimum_ios) < version("15.6"):
            raise ConfigError("--minimum-ios must be at least 15.6 under this workflow")
        changes = []
        path = project_path(root, FRAMEWORK)
        original = path.read_bytes()
        updated = framework_content(original, args.minimum_ios)
        if updated != original:
            changes.append((FRAMEWORK, path, original, updated))
            result["required_changes"].append({"file": FRAMEWORK, "reason": "Set correctly cased MinimumOSVersion"})
        if args.permission_handler:
            path = project_path(root, PODFILE)
            original = path.read_bytes()
            updated = podfile_content(original, args.photo_access)
            if updated != original:
                changes.append((PODFILE, path, original, updated))
                result["required_changes"].append({"file": PODFILE, "reason": "Configure effective photo macros at end of post_install"})
        if args.apply and changes:
            apply_changes(root, changes)
            result["changed"] = [change[0] for change in changes]
        result["source_ready"] = not changes or args.apply
        result["next_steps"] = ["Verify deployment targets and API-specific usage descriptions",
                                "For CocoaPods run pod install and inspect permission plugin target build settings",
                                "Build iOS, recheck source preflight, and inspect actual App.framework and app plists",
                                "Verify actual authorization paths and removal of ATT dependencies, requests and links"]
        status = 0 if result["source_ready"] else 1
    except (ConfigError, OSError, ValueError) as error:
        result["source_ready"] = False
        result["errors"].append(str(error))
        status = 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
