#!/bin/bash
# Generate self-signed SSL certificates for development

# Create self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /home/mike/mvidarr/docker/nginx/ssl/key.pem \
    -out /home/mike/mvidarr/docker/nginx/ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

echo "Self-signed SSL certificates generated successfully!"
echo "Certificate: /home/mike/mvidarr/docker/nginx/ssl/cert.pem"
echo "Private key: /home/mike/mvidarr/docker/nginx/ssl/key.pem"
echo ""
echo "Note: These are self-signed certificates for development only."
echo "For production, use proper SSL certificates from a trusted CA."