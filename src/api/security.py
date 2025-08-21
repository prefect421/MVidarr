"""
Security API endpoints for certificate management
"""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

from src.middleware.simple_auth_middleware import auth_required
from src.utils.logger import get_logger

security_bp = Blueprint("security", __name__, url_prefix="/security")
logger = get_logger("mvidarr.api.security")

# Certificate storage paths
CERT_DIR = Path("data/certificates")
CERT_DIR.mkdir(parents=True, exist_ok=True)

CERT_FILE = CERT_DIR / "certificate.crt"
KEY_FILE = CERT_DIR / "private.key"
CHAIN_FILE = CERT_DIR / "chain.crt"


def validate_certificate_file(file_content: bytes) -> tuple[bool, str, dict]:
    """
    Validate a certificate file and extract information

    Returns:
        tuple: (is_valid, error_message, cert_info)
    """
    try:
        cert = x509.load_pem_x509_certificate(file_content)

        # Extract certificate information
        cert_info = {
            "subject": cert.subject.rfc4514_string(),
            "issuer": cert.issuer.rfc4514_string(),
            "not_before": cert.not_valid_before.isoformat(),
            "not_after": cert.not_valid_after.isoformat(),
            "serial_number": str(cert.serial_number),
            "version": cert.version.name,
            "signature_algorithm": cert.signature_algorithm_oid._name,
        }

        # Check for Subject Alternative Names
        try:
            san_ext = cert.extensions.get_extension_for_oid(
                x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
            )
            alt_names = [name.value for name in san_ext.value]
            cert_info["alt_names"] = alt_names
        except x509.ExtensionNotFound:
            cert_info["alt_names"] = []

        # Calculate days until expiry
        now = datetime.utcnow()
        days_until_expiry = (cert.not_valid_after - now).days
        cert_info["days_until_expiry"] = days_until_expiry

        # Check if certificate is currently valid
        is_valid = cert.not_valid_before <= now <= cert.not_valid_after
        cert_info["is_currently_valid"] = is_valid

        return True, "", cert_info

    except Exception as e:
        return False, f"Invalid certificate format: {str(e)}", {}


def validate_private_key_file(file_content: bytes) -> tuple[bool, str]:
    """
    Validate a private key file

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Try to load as PEM format
        try:
            serialization.load_pem_private_key(file_content, password=None)
            return True, ""
        except TypeError:
            # Might be password protected
            return False, "Private key appears to be password protected (not supported)"
        except ValueError:
            # Try different formats or provide error
            return False, "Invalid private key format or unsupported key type"

    except Exception as e:
        return False, f"Error validating private key: {str(e)}"


@security_bp.route("/certificates/status", methods=["GET"])
@auth_required
def get_certificate_status():
    """Get current certificate status"""
    try:
        status = {
            "certificate_exists": CERT_FILE.exists(),
            "private_key_exists": KEY_FILE.exists(),
            "certificate_chain_exists": CHAIN_FILE.exists(),
            "expiry_date": None,
            "days_until_expiry": None,
            "is_valid": False,
        }

        # If certificate exists, get additional info
        if status["certificate_exists"]:
            try:
                with open(CERT_FILE, "rb") as f:
                    cert_content = f.read()

                is_valid, error, cert_info = validate_certificate_file(cert_content)
                if is_valid:
                    status["expiry_date"] = cert_info["not_after"]
                    status["days_until_expiry"] = cert_info["days_until_expiry"]
                    status["is_valid"] = cert_info["is_currently_valid"]
                    status["subject"] = cert_info["subject"]
                    status["issuer"] = cert_info["issuer"]

            except Exception as e:
                logger.warning(f"Error reading certificate file: {e}")

        return jsonify({"success": True, "status": status})

    except Exception as e:
        logger.error(f"Error getting certificate status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@security_bp.route("/certificates/upload", methods=["POST"])
@auth_required
def upload_certificates():
    """Upload new SSL certificates"""
    try:
        if "certificate" not in request.files or "private_key" not in request.files:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Both certificate and private key files are required",
                    }
                ),
                400,
            )

        cert_file = request.files["certificate"]
        key_file = request.files["private_key"]
        chain_file = request.files.get("certificate_chain")

        if cert_file.filename == "" or key_file.filename == "":
            return jsonify({"success": False, "error": "No files selected"}), 400

        # Read and validate certificate
        cert_content = cert_file.read()
        is_valid, error, cert_info = validate_certificate_file(cert_content)
        if not is_valid:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Certificate validation failed: {error}",
                    }
                ),
                400,
            )

        # Read and validate private key
        key_content = key_file.read()
        is_valid, error = validate_private_key_file(key_content)
        if not is_valid:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Private key validation failed: {error}",
                    }
                ),
                400,
            )

        # Backup existing files if they exist
        backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        if CERT_FILE.exists():
            shutil.copy2(
                CERT_FILE, CERT_DIR / f"certificate_backup_{backup_suffix}.crt"
            )
        if KEY_FILE.exists():
            shutil.copy2(KEY_FILE, CERT_DIR / f"private_backup_{backup_suffix}.key")

        # Save new certificate and key
        with open(CERT_FILE, "wb") as f:
            f.write(cert_content)
        with open(KEY_FILE, "wb") as f:
            f.write(key_content)

        # Set secure permissions
        os.chmod(CERT_FILE, 0o644)
        os.chmod(KEY_FILE, 0o600)  # Private key should be more restricted

        # Handle optional certificate chain
        if chain_file and chain_file.filename != "":
            chain_content = chain_file.read()
            with open(CHAIN_FILE, "wb") as f:
                f.write(chain_content)
            os.chmod(CHAIN_FILE, 0o644)

        logger.info(
            f"SSL certificates uploaded successfully - expires: {cert_info['not_after']}"
        )

        return jsonify(
            {
                "success": True,
                "message": "Certificates uploaded successfully",
                "certificate_info": {
                    "subject": cert_info["subject"],
                    "expiry_date": cert_info["not_after"],
                    "days_until_expiry": cert_info["days_until_expiry"],
                },
            }
        )

    except Exception as e:
        logger.error(f"Error uploading certificates: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@security_bp.route("/certificates/validate", methods=["POST"])
@auth_required
def validate_certificate():
    """Validate the current certificate"""
    try:
        if not CERT_FILE.exists():
            return (
                jsonify({"success": False, "error": "No certificate file found"}),
                404,
            )

        # Read and validate certificate
        with open(CERT_FILE, "rb") as f:
            cert_content = f.read()

        is_valid, error, cert_info = validate_certificate_file(cert_content)

        validation_result = {
            "valid": is_valid,
            "errors": [error] if error else [],
            **cert_info,
        }

        # Additional validation checks
        if is_valid:
            # Check if certificate is expiring soon (within 30 days)
            if cert_info["days_until_expiry"] < 30:
                validation_result["warnings"] = [
                    f"Certificate expires in {cert_info['days_until_expiry']} days"
                ]

            # Check if private key exists and matches
            if KEY_FILE.exists():
                try:
                    with open(KEY_FILE, "rb") as f:
                        key_content = f.read()
                    key_valid, key_error = validate_private_key_file(key_content)
                    if not key_valid:
                        validation_result["errors"].append(
                            f"Private key issue: {key_error}"
                        )
                        validation_result["valid"] = False
                except Exception as e:
                    validation_result["errors"].append(
                        f"Error reading private key: {str(e)}"
                    )
                    validation_result["valid"] = False
            else:
                validation_result["errors"].append("Private key file not found")
                validation_result["valid"] = False

        return jsonify({"success": True, "validation": validation_result})

    except Exception as e:
        logger.error(f"Error validating certificate: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@security_bp.route("/certificates/download", methods=["GET"])
@auth_required
def download_certificate():
    """Download the current certificate file"""
    try:
        if not CERT_FILE.exists():
            return (
                jsonify({"success": False, "error": "No certificate file found"}),
                404,
            )

        return send_file(
            CERT_FILE,
            as_attachment=True,
            download_name="mvidarr-certificate.crt",
            mimetype="application/x-x509-ca-cert",
        )

    except Exception as e:
        logger.error(f"Error downloading certificate: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@security_bp.route("/certificates/remove", methods=["DELETE"])
@auth_required
def remove_certificates():
    """Remove SSL certificates"""
    try:
        removed_files = []

        # Backup files before removal
        backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

        if CERT_FILE.exists():
            backup_path = CERT_DIR / f"certificate_removed_{backup_suffix}.crt"
            shutil.move(str(CERT_FILE), str(backup_path))
            removed_files.append("certificate")

        if KEY_FILE.exists():
            backup_path = CERT_DIR / f"private_removed_{backup_suffix}.key"
            shutil.move(str(KEY_FILE), str(backup_path))
            removed_files.append("private_key")

        if CHAIN_FILE.exists():
            backup_path = CERT_DIR / f"chain_removed_{backup_suffix}.crt"
            shutil.move(str(CHAIN_FILE), str(backup_path))
            removed_files.append("certificate_chain")

        if not removed_files:
            return (
                jsonify(
                    {"success": False, "error": "No certificate files found to remove"}
                ),
                404,
            )

        logger.info(f"SSL certificates removed: {', '.join(removed_files)}")

        return jsonify(
            {
                "success": True,
                "message": f"Removed {', '.join(removed_files)} (backed up with timestamp)",
                "removed_files": removed_files,
            }
        )

    except Exception as e:
        logger.error(f"Error removing certificates: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
