#!/usr/bin/env bash
set -e

MEMBER="$1"

case "$MEMBER" in
  amrith|AMRITH|AMRITH03)
    NAME="AMRITH03"
    EMAIL="amrith2503@gmail.com"
    KEY="$HOME/.ssh/id_ed25519_amrith"
    HANDLE="AMRITH03"
    ;;
  adithya|adi|Achilles80)
    NAME="Achilles80"
    EMAIL="adithyaajay2005@gmail.com"
    KEY="$HOME/.ssh/id_ed25519_adithya"
    HANDLE="Achilles80"
    ;;
  gowreesh|gow|Gowreesh1905)
    NAME="Gowreesh1905"
    EMAIL="gowreeshoff@gmail.com"
    KEY="$HOME/.ssh/id_ed25519_gowreesh"
    HANDLE="Gowreesh1905"
    ;;
  rishi|rishiikesh|Rishiikesh-20)
    NAME="Rishiikesh-20"
    EMAIL="rishiikeshsk@gmail.com"
    KEY="$HOME/.ssh/id_ed25519_rishi"
    HANDLE="Rishiikesh-20"
    ;;
  adhi|adhikkesh|Adhikkesh)
    NAME="Adhikkesh"
    EMAIL="adhikkesh@gmail.com"
    KEY="$HOME/.ssh/id_ed25519"
    HANDLE="Adhikkesh"
    ;;
  *)
    echo "Usage: $0 [amrith|adithya|gowreesh|rishi|adhi]"
    exit 1
    ;;
esac

echo "==> Switching active Git identity to: $NAME <$EMAIL>"
git config user.name "$NAME"
git config user.email "$EMAIL"

if [ -f "$KEY" ]; then
  echo "==> Updating active SSH key symlink: ~/.ssh/github_active -> $KEY"
  ln -sf "$KEY" "$HOME/.ssh/github_active"
else
  echo "Warning: SSH key $KEY not found"
fi

echo "==> Testing GitHub SSH connection..."
ssh -o StrictHostKeyChecking=accept-new -o BatchMode=yes -T git@github.com 2>&1 || true

echo "==> Active Git config in repo:"
echo "    user.name:  $(git config user.name)"
echo "    user.email: $(git config user.email)"
