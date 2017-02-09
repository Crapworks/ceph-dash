#!/usr/bin/env sh

CEPHCONFIG="/etc/ceph/ceph.conf"
CEPHKEYRING="/etc/ceph/keyring"

echo "# REQUIRED ENVIRONMENT VARIABLES"
echo "* CEPHMONS (comma separated list of ceph monitor ip addresses)"
echo "* KEYRING (full keyring to deploy in docker container)"
echo ""
echo "# OPTIONAL ENVIRONMENT VARIABLES"
echo "* NAME (keyring name to use)"
echo "* ID (keyting id to use)"
echo ""

echo -e "${KEYRING}" > ${CEPHKEYRING}
echo -e "[global]\nmon host = ${CEPHMONS}" > ${CEPHCONFIG}

echo "# CEPH STATUS"
ceph -s

export CEPHDASH_CEPHCONFIG="${CEPHCONFIG}"
export CEPHDASH_KEYRING="${CEPHKEYRING}"

if [ -n "${NAME}" ]; then
    export CEPHDASH_NAME="${NAME}"
fi

if [ -n "${ID}" ]; then
    export CEPHDASH_ID="${ID}"
fi

python $*
